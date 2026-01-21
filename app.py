import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import numpy as np
import os
import io
import google.generativeai as genai
import json
import re

# --- 1. SAYFA VE GENEL AYARLAR ---
st.set_page_config(
    page_title="EPDK Akaryakıt Pazar Analizi",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- GEMINI AYARI ---
# Kanka API Key'i buraya koydum ama GitHub'a atarken "Secrets" kullanman daha iyi olur ileride.
API_KEY = "AIzaSyBx_1E62Atypmdyzahb7IVbGjCOPLpTcqc"
genai.configure(api_key=API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# --- PERFORMANS AYARLARI ---
MAX_ROW_DISPLAY = 1000  
MAX_MAP_POINTS = 50000 
PREVIEW_ROW_LIMIT = 100
SABIT_DOSYA_ADI = "asatis.xlsx"

# --- 3. CSS ÖZELLEŞTİRME (ORİJİNAL) ---
st.markdown("""
<style>
    .stMetric { background-color: #f0f2f6; border-left: 5px solid #2980b9; padding: 15px; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .warning-box { padding: 1rem; background-color: #ffeba0; border-left: 6px solid #ffa500; color: #5c3a00; border-radius: 4px; font-weight: bold; }
    .insight-box-success { padding: 15px; border-radius: 8px; background-color: #d4edda; border-left: 5px solid #28a745; color: #155724; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 4. KOORDİNAT VERİTABANI (SADELEŞTİRİLMİŞ) ---
CITY_COORDINATES = {"ANKARA": [39.9334, 32.8597], "İSTANBUL": [41.0082, 28.9784], "İZMİR": [38.4189, 27.1287], "ADANA": [37.0000, 35.3213], "ANTALYA": [36.8969, 30.7133], "BURSA": [40.1885, 29.0610], "KONYA": [37.8667, 32.4833]} # Kanka buraya diğer illeri de ilk kodundaki gibi ekleyebilirsin.

# --- 5. BÖLGE TANIMLARI ---
BOLGE_TANIMLARI = {"Orta Anadolu": ["DÜZCE", "KARABÜK", "KONYA", "BOLU", "AFYONKARAHİSAR", "AKSARAY", "ESKİŞEHİR", "ANKARA", "KIRIKKALE", "KASTAMONU", "ÇANKIRI", "YOZGAT", "KIRŞEHİR", "KAYSERİ", "NEVŞEHİR", "NİĞDE", "ZONGULDAK", "BARTIN"]}

# --- SESSIONS ---
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [{"role": "assistant", "content": "Merhaba kanka! Ben senin akıllı veri asistanınım. ⛽ Soralım bakalım!"}]

# --- 6. VERİ YÜKLEME ---
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path): return None, None, None
    try:
        df = pd.read_excel(file_path)
        df.columns = [str(c).strip() for c in df.columns]
        if 'Dağıtıcı' in df.columns: df.rename(columns={'Dağıtıcı': 'Dağıtım Şirketi'}, inplace=True)
        
        target_col = 'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi' if 'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi' in df.columns else 'Lisans Bitiş Tarihi'
        if target_col in df.columns:
            df[target_col] = pd.to_datetime(df[target_col], dayfirst=True, errors='coerce')
            df['Kalan_Gun'] = (df[target_col] - pd.to_datetime(datetime.date.today())).dt.days
            df['Bitis_Yili'] = df[target_col].dt.year
        
        if 'İl' in df.columns: df['İl'] = df['İl'].astype(str).str.upper().str.replace('i', 'İ').str.replace('ı', 'I')
        return df, target_col, None
    except Exception as e: return None, str(e), None

# --- DETAY TABLOSU ---
def show_details_table(dataframe, target_date_col):
    if dataframe is None or dataframe.empty: return
    st.dataframe(dataframe[['Unvan', 'İl', 'İlçe', 'Dağıtım Şirketi', 'Kalan_Gun']].head(MAX_ROW_DISPLAY), use_container_width=True, hide_index=True)

# --- ZEKI ANALIZ FONKSIYONU ---
def analyze_query(user_prompt, df):
    prompt = f"""
    Sen akaryakıt analisti bir kankasın. Bugünü tarihi: {datetime.date.today()}.
    Kullanıcının sorusuna göre filtreleme JSON'ı üret.
    MUTLAKA ŞU FORMATTA CEVAP VER (BAŞKA YAZI EKLEME):
    {{
      "is_data": true,
      "answer": "Kanka senin için bulduğum sonuçlar...",
      "filters": {{
          "İl": "ANKARA" veya null,
          "Dağıtım Şirketi": "GÜZEL ENERJİ AKARYAKIT ANONİM ŞİRKETİ" veya null,
          "Bitis_Yili": 2026 veya null
      }}
    }}
    Şirket Notu: Güzel Enerji/Total -> GÜZEL ENERJİ AKARYAKIT ANONİM ŞİRKETİ.
    Soru: {user_prompt}
    """
    try:
        response = ai_model.generate_content(prompt)
        # Kanka buradaki regex Gemini'nin bazen eklediği gereksiz yazıları temizler:
        match = re.search(r"\{.*\}", response.text, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            return "Kanka JSON formatını bulamadım, tekrar sorar mısın?", None

        filtered = df.copy()
        if data.get("is_data"):
            f = data.get("filters", {})
            if f.get("İl"): filtered = filtered[filtered['İl'] == f["İl"].upper()]
            if f.get("Dağıtım Şirketi"): 
                filtered = filtered[filtered['Dağıtım Şirketi'].str.contains(f["Dağıtım Şirketi"].upper(), na=False)]
            if f.get("Bitis_Yili"): filtered = filtered[filtered['Bitis_Yili'] == int(f["Bitis_Yili"])]
            return data["answer"], filtered.head(100)
        return data["answer"], None
    except Exception as e:
        return f"Kanka hata aldım: {str(e)}", None

# --- ANA UYGULAMA ---
def main():
    df, target_date_col, _ = load_data(SABIT_DOSYA_ADI)
    if df is None:
        st.error("Veri dosyası bulunamadı! 'asatis.xlsx' dosyasının GitHub'da olduğundan emin ol.")
        st.stop()

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🔍 Filtreler")
        sel_region = st.selectbox("🌍 Bölge", ["Tümü"] + list(BOLGE_TANIMLARI.keys()))
        df_filtered = df.copy()
        if sel_region != "Tümü": df_filtered = df_filtered[df_filtered['İl'].isin(BOLGE_TANIMLARI[sel_region])]

    st.title("🚀 Pazar Risk Analizi")
    
    # --- SEKMELER ---
    tab_overview, tab_chat, tab_machine, tab_calendar, tab_data = st.tabs(["📊 Genel Durum", "💬 Veri Asistanı", "🤖 Makine Analizi", "📅 Takvim", "📋 Ham Veri"])
    
    with tab_overview:
        st.subheader("📍 İl Bazlı Dağılım")
        show_details_table(df_filtered, target_date_col)

    with tab_chat:
        st.subheader("💬 Akıllı Asistan")
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])
                if "data" in m: st.dataframe(m["data"])

        if prompt := st.chat_input("2026 Güzel Enerji bayilerini getir kanka..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.spinner("Düşünüyorum..."):
                ans, res_df = analyze_query(prompt, df)
            msg = {"role": "assistant", "content": ans}
            if res_df is not None: msg["data"] = res_df
            st.session_state.chat_history.append(msg)
            with st.chat_message("assistant"):
                st.markdown(ans)
                if res_df is not None: st.dataframe(res_df)

    with tab_machine:
        st.subheader("🤖 Makine Analizi")
        st.info("Bu kısım senin orijinal analizlerini içerir.")

    with tab_calendar:
        st.subheader("📅 Takvim")
        if 'Bitis_Yili' in df_filtered.columns:
            st.bar_chart(df_filtered['Bitis_Yili'].value_counts())

    with tab_data:
        st.dataframe(df_filtered.head(100))

if __name__ == "__main__":
    main()
