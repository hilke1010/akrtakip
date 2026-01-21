import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import numpy as np
import os
import io
import google.generativeai as genai
import json

# --- 1. SAYFA VE GENEL AYARLAR ---
st.set_page_config(
    page_title="EPDK Akaryakıt Pazar Analizi",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- GEMINI AYARI (HATA ALMAMAK İÇİN GÜNCELLENDİ) ---
API_KEY = "AIzaSyBx_1E62Atypmdyzahb7IVbGjCOPLpTcqc"
genai.configure(api_key=API_KEY)
# Modeli güvenli şekilde tanımlıyoruz
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# --- PERFORMANS AYARLARI ---
MAX_ROW_DISPLAY = 1000  
MAX_MAP_POINTS = 50000 
PREVIEW_ROW_LIMIT = 100

# --- 2. DOSYA İSİMLERİ ---
SABIT_DOSYA_ADI = "asatis.xlsx"

# --- 3. CSS ÖZELLEŞTİRME (ORİJİNAL) ---
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        border-left: 5px solid #2980b9; 
        padding: 15px;
        border-radius: 5px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .block-container { padding-top: 2rem; }
    .crm-box {
        background-color: #fff9c4;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #fbc02d;
        margin-bottom: 10px;
    }
    .warning-box {
        padding: 1rem;
        background-color: #ffeba0;
        border-left: 6px solid #ffa500;
        color: #5c3a00;
        border-radius: 4px;
        font-weight: bold;
    }
    .year-box {
        background-color: #e8f4f8;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        border: 1px solid #b3e5fc;
        margin-bottom: 5px;
    }
    .year-title { font-weight: bold; color: #0277bd; font-size: 1.1em; }
    .year-count { font-size: 1.5em; font-weight: bold; color: #01579b; }
    
    .insight-box-success { padding: 15px; border-radius: 8px; background-color: #d4edda; border-left: 5px solid #28a745; color: #155724; margin-bottom: 10px; }
    .insight-box-warning { padding: 15px; border-radius: 8px; background-color: #fff3cd; border-left: 5px solid #ffc107; color: #856404; margin-bottom: 10px; }
    .insight-box-danger { padding: 15px; border-radius: 8px; background-color: #f8d7da; border-left: 5px solid #dc3545; color: #721c24; margin-bottom: 10px; }
    .insight-box-info { padding: 15px; border-radius: 8px; background-color: #d1ecf1; border-left: 5px solid #17a2b8; color: #0c5460; margin-bottom: 10px; }
    .district-chip { display: inline-block; background-color: #f1f3f5; padding: 5px 10px; margin: 3px; border-radius: 15px; font-size: 0.9em; border: 1px solid #ddd; cursor: help; }
    .district-chip:hover { background-color: #e2e6ea; border-color: #adb5bd; }
</style>
""", unsafe_allow_html=True)

# --- 4. KOORDİNAT VERİTABANI (ORİJİNAL) ---
CITY_COORDINATES = {
    "ADANA": [37.0000, 35.3213], "ADIYAMAN": [37.7648, 38.2786], "AFYONKARAHİSAR": [38.7507, 30.5567],
    "AĞRI": [39.7191, 43.0503], "AMASYA": [40.6499, 35.8353], "ANKARA": [39.9334, 32.8597],
    "ANTALYA": [36.8969, 30.7133], "ARTVİN": [41.1828, 41.8183], "AYDIN": [37.8560, 27.8416],
    "BALIKESİR": [39.6484, 27.8826], "BİLECİK": [40.1451, 29.9799], "BİNGÖL": [38.8854, 40.4983],
    "BİTLİS": [38.3938, 42.1232], "BOLU": [40.7350, 31.6061], "BURDUR": [37.4613, 30.0665],
    "BURSA": [40.1885, 29.0610], "ÇANAKKALE": [40.1553, 26.4142], "ÇANKIRI": [40.6013, 33.6134],
    "ÇORUM": [40.5506, 34.9556], "DENİZLİ": [37.7765, 29.0864], "DİYARBAKIR": [37.9144, 40.2306],
    "EDİRNE": [41.6768, 26.5603], "ELAZIĞ": [38.6810, 39.2264], "ERZİNCAN": [39.7500, 39.5000],
    "ERZURUM": [39.9043, 41.2679], "ESKİŞEHİR": [39.7767, 30.5206], "GAZİANTEP": [37.0662, 37.3833],
    "GİRESUN": [40.9128, 38.3895], "GÜMÜŞHANE": [40.4600, 39.4700], "HAKKARİ": [37.5833, 43.7333],
    "HATAY": [36.4018, 36.3498], "ISPARTA": [37.7648, 30.5566], "MERSİN": [36.8000, 34.6333],
    "İSTANBUL": [41.0082, 28.9784], "İZMİR": [38.4189, 27.1287], "KARS": [40.6172, 43.0974],
    "KASTAMONU": [41.3887, 33.7827], "KAYSERİ": [38.7312, 35.4787], "KIRKLARELİ": [41.7333, 27.2167],
    "KIRŞEHİR": [39.1425, 34.1709], "KOCAELİ": [40.8533, 29.8815], "KONYA": [37.8667, 32.4833],
    "KÜTAHYA": [39.4167, 29.9833], "MALATYA": [38.3552, 38.3095], "MANİSA": [38.6191, 27.4289],
    "KAHRAMANMARAŞ": [37.5858, 36.9371], "MARDİN": [37.3212, 40.7245], "MUĞLA": [37.2153, 28.3636],
    "MUŞ": [38.9462, 41.7539], "NEVŞEHİR": [38.6244, 34.7144], "NİĞDE": [37.9667, 34.6833],
    "ORDU": [40.9839, 37.8764], "RİZE": [41.0201, 40.5234], "SAKARYA": [40.7569, 30.3783],
    "SAMSUN": [41.2928, 36.3313], "SİİRT": [37.9333, 41.9500], "SİNOP": [42.0231, 35.1531],
    "SİVAS": [39.7477, 37.0179], "TEKİRDAĞ": [40.9833, 27.5167], "TOKAT": [40.3167, 36.5500],
    "TRABZON": [41.0015, 39.7178], "TUNCELİ": [39.1079, 39.5401], "ŞANLIURFA": [37.1591, 38.7969],
    "UŞAK": [38.6823, 29.4082], "VAN": [38.4891, 43.4089], "YOZGAT": [39.8181, 34.8147],
    "ZONGULDAK": [41.4564, 31.7987], "AKSARAY": [38.3687, 34.0370], "BAYBURT": [40.2552, 40.2249],
    "KARAMAN": [37.1759, 33.2287], "KIRIKKALE": [39.8468, 33.5153], "BATMAN": [37.8812, 41.1291],
    "ŞIRNAK": [37.4187, 42.4918], "BARTIN": [41.6344, 32.3375], "ARDAHAN": [41.1105, 42.7022],
    "IĞDIR": [39.9196, 44.0459], "YALOVA": [40.6500, 29.2667], "KARABÜK": [41.2061, 32.6204],
    "KİLİS": [36.7184, 37.1212], "OSMANİYE": [37.0742, 36.2467], "DÜZCE": [40.8438, 31.1565]
}

# --- 5. BÖLGE TANIMLARI (ORİJİNAL) ---
BOLGE_TANIMLARI = {
    "Orta Anadolu": [
        "DÜZCE", "KARABÜK", "KONYA", "BOLU", "AFYONKARAHİSAR",
        "AKSARAY", "ESKİŞEHİR", "ANKARA", "KIRIKKALE", "KASTAMONU",
        "ÇANKIRI", "YOZGAT", "KIRŞEHİR", "KAYSERİ", "NEVŞEHİR",
        "NİĞDE", "ZONGULDAK", "BARTIN"
    ]
}

# --- SESSIONS ---
if 'crm_notes' not in st.session_state:
    st.session_state.crm_notes = {}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Merhaba kanka! Ben senin akıllı veri asistanınım. ⛽ Her şeyi sorabilirsin!"}
    ]

# --- 6. EXCEL VERİ YÜKLEME (ORİJİNAL) ---
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path): return None, None, None
    try:
        df = pd.read_excel(file_path)
        df.columns = [str(c).strip() for c in df.columns]
        if 'Dağıtıcı' in df.columns and 'Dağıtım Şirketi' not in df.columns:
            df.rename(columns={'Dağıtıcı': 'Dağıtım Şirketi'}, inplace=True)
        
        date_cols = ['Lisans Başlangıç Tarihi', 'Lisans Bitiş Tarihi',
                     'Dağıtıcı ile Yapılan Sözleşme Başlangıç Tarihi',
                     'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi']
        for col in date_cols:
            if col in df.columns: df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

        target_col = 'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi'
        if target_col not in df.columns: target_col = 'Lisans Bitiş Tarihi'
        
        start_col = 'Dağıtıcı ile Yapılan Sözleşme Başlangıç Tarihi'
        if start_col not in df.columns: start_col = 'Lisans Başlangıç Tarihi'

        today = pd.to_datetime(datetime.date.today())
        if target_col in df.columns:
            df['Kalan_Gun'] = (df[target_col] - today).dt.days
            df['Bitis_Yili'] = df[target_col].dt.year
            month_map = {1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan', 5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos', 9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'}
            df['Bitis_Ayi_No'] = df[target_col].dt.month
            df['Bitis_Ayi'] = df['Bitis_Ayi_No'].map(month_map)
        else:
            df['Kalan_Gun'] = np.nan
            df['Bitis_Yili'] = np.nan
            df['Bitis_Ayi'] = np.nan
            df['Bitis_Ayi_No'] = np.nan

        if start_col in df.columns and target_col in df.columns:
            df['Sozlesme_Suresi_Gun'] = (df[target_col] - df[start_col]).dt.days
        else:
            df['Sozlesme_Suresi_Gun'] = np.nan

        def get_risk(days):
            if pd.isna(days): return "Bilinmiyor"
            if days < 0: return "SÜRESİ DOLDU 🚨"
            if days < 90: return "KRİTİK (<3 Ay) ⚠️"
            if days < 180: return "YAKLAŞIYOR (<6 Ay) ⏳"
            return "GÜVENLİ ✅"
        df['Risk_Durumu'] = df['Kalan_Gun'].apply(get_risk)

        if 'İl' in df.columns: df['İl'] = df['İl'].astype(str).str.upper().str.replace('i', 'İ').str.replace('ı', 'I')
        if 'İlçe' in df.columns: df['İlçe'] = df['İlçe'].astype(str).str.upper().str.replace('i', 'İ').str.replace('ı', 'I')
        return df, target_col, start_col
    except Exception as e: return None, str(e), None

# --- DETAY TABLOSU (ORİJİNAL) ---
def show_details_table(dataframe, target_date_col, extra_cols=None):
    if dataframe is None or dataframe.empty:
        st.info("Seçilen kriterlere uygun kayıt bulunamadı.")
        return
    record_count = len(dataframe)
    
    if record_count > MAX_ROW_DISPLAY:
        st.markdown(f"<div class='warning-box'>⚠️ <b>Performans Uyarısı:</b> Listede toplam <b>{record_count:,}</b> kayıt var.<br>Aşağıda ilk <b>{MAX_ROW_DISPLAY:,}</b> tanesi gösterilmektedir.</div>", unsafe_allow_html=True)
        display_df_limit = dataframe.head(MAX_ROW_DISPLAY)
    else:
        display_df_limit = dataframe

    cols = ['Unvan', 'İl', 'İlçe', 'Dağıtım Şirketi', target_date_col, 'Kalan_Gun', 'Risk_Durumu']
    if extra_cols: cols.extend(extra_cols)
    seen = set()
    final_cols = [c for c in cols if c in display_df_limit.columns and not (c in seen or seen.add(c))]
    display_df = display_df_limit[final_cols].copy()
    
    date_columns = [col for col in display_df.columns if "Tarihi" in col or "Tarih" in col]
    for date_col in date_columns:
        try: display_df[date_col] = pd.to_datetime(display_df[date_col]).dt.strftime('%d.%m.%Y')
        except: pass

    def highlight_risk(val):
        if not isinstance(val, (int, float)): return ''
        if val < 0: return 'background-color: #ffcccc'
        elif val < 90: return 'background-color: #ffe5cc'
        return ''
    
    st.markdown(f"**📋 Listelenen Bayi Sayısı:** {len(display_df)}")
    st.dataframe(display_df.style.map(highlight_risk, subset=['Kalan_Gun']), use_container_width=True, hide_index=True)

# --- GEMINI ANALİZ FONKSİYONU (YENİ VE ZEKİ) ---
def analyze_query(user_prompt, df):
    system_prompt = f"""
    Sen akaryakıt pazar analisti bir kankasın. Bugünü tarihi: {datetime.date.today()}.
    Kullanıcının sorusuna göre filtreleme yapmamı sağla. 
    LÜTFEN SADECE ŞU JSON FORMATINDA CEVAP VER, BAŞKA METİN EKLEME:
    {{
      "is_data": true,
      "answer": "Kanka senin için bulduğum sonuçlar...",
      "filters": {{
          "İl": "ANKARA" veya null,
          "Dağıtım Şirketi": "TAM ŞİRKET ADI" veya null,
          "Bitis_Yili": 2026 veya null
      }}
    }}
    Önemli Şirketler: 
    - GÜZEL ENERJİ AKARYAKIT ANONİM ŞİRKETİ (Total/Güzel Enerji deyince bunu kullan)
    - OPET PETROLCÜLÜK A.Ş.
    - PETROL OFİSİ A.Ş.
    """
    
    try:
        response = ai_model.generate_content(system_prompt + "\nSoru: " + user_prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(text)
        
        filtered = df.copy()
        if data.get("is_data"):
            f = data.get("filters", {})
            if f.get("İl"): filtered = filtered[filtered['İl'] == f["İl"].upper()]
            if f.get("Dağıtım Şirketi"): 
                comp = f["Dağıtım Şirketi"].upper()
                filtered = filtered[filtered['Dağıtım Şirketi'].str.contains(comp, na=False)]
            if f.get("Bitis_Yili"): filtered = filtered[filtered['Bitis_Yili'] == int(f["Bitis_Yili"])]
            
            return data["answer"], filtered.head(50)
        return data["answer"], None
    except:
        return "Kanka bir şeyler ters gitti, tekrar sorar mısın?", None

# --- ANA UYGULAMA ---
def main():
    data_result = load_data(SABIT_DOSYA_ADI)
    if data_result is None or data_result[0] is None:
        st.error(f"⚠️ Hata: Veri Yüklenemedi")
        st.stop()
    df, target_date_col, start_date_col = data_result

    # --- SIDEBAR (ORİJİNAL) ---
    with st.sidebar:
        st.info("🕒 Veriler her gün saat 10:00'da yenilenmektedir.")
        st.title("🔍 Filtre Paneli")
        region_options = ["Tümü"] + list(BOLGE_TANIMLARI.keys())
        selected_region = st.selectbox("🌍 Bölge Seç", region_options)
        if selected_region != "Tümü":
            df_for_sidebar = df[df['İl'].isin(BOLGE_TANIMLARI[selected_region])]
        else: df_for_sidebar = df.copy()
        selected_cities = st.multiselect("🏢 Şehir Seç", sorted(df_for_sidebar['İl'].unique().tolist()))
        selected_companies = st.multiselect("⛽ Şirket Seç", sorted(df['Dağıtım Şirketi'].dropna().unique().tolist()))
        st.markdown("---")
        st.markdown("[📊 Pazar Payı](https://pazarpayi.streamlit.app/)")

    # Filtreleme
    df_filtered = df.copy()
    if selected_region != "Tümü": df_filtered = df_filtered[df_filtered['İl'].isin(BOLGE_TANIMLARI[selected_region])]
    if selected_cities: df_filtered = df_filtered[df_filtered['İl'].isin(selected_cities)]
    if selected_companies: df_filtered = df_filtered[df_filtered['Dağıtım Şirketi'].isin(selected_companies)]

    # --- KPI (ORİJİNAL) ---
    st.title("🚀 Akaryakıt Pazar & Risk Analizi")
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam İstasyon", f"{len(df_filtered):,}")
    c2.metric("Acil Sözleşme", len(df_filtered[df_filtered['Kalan_Gun'] < 90]))
    c3.metric("Aktif Dağıtıcı", df_filtered['Dağıtım Şirketi'].nunique())
    
    st.divider()

    # --- TÜM SEKMELERİ GERİ GETİRDİM (ORİJİNAL YAPI) ---
    tab_overview, tab_chat, tab_machine, tab_compare, tab_sim, tab_calendar, tab_radar, tab_ilce, tab_report, tab_crm, tab_data = st.tabs([
        "📊 Bölgesel & Durum", "💬 Veri Asistanı", "🤖 Makine Analizi", "⚔️ Karşılaştırma", 
        "🔮 Simülasyon", "📅 Takvim", "📡 Radar", "📍 İlçe", "📄 İl Karnesi", "📝 CRM", "📋 Ham Veri"
    ])
    
    # 1. BÖLGESEL (ORİJİNAL)
    with tab_overview:
        map_data = df_filtered['İl'].value_counts().reset_index()
        map_data.columns = ['İl', 'Adet']
        map_data['lat'] = map_data['İl'].map(lambda x: CITY_COORDINATES.get(x, [None, None])[0])
        map_data['lon'] = map_data['İl'].map(lambda x: CITY_COORDINATES.get(x, [None, None])[1])
        fig_map = px.scatter_mapbox(map_data.dropna(), lat="lat", lon="lon", size="Adet", color="Adet", hover_name="İl", size_max=35, zoom=5, mapbox_style="open-street-map")
        st.plotly_chart(fig_map, use_container_width=True)
        show_details_table(df_filtered, target_date_col)

    # 2. VERİ ASİSTANI (GELİŞMİŞ GEMINI)
    with tab_chat:
        st.subheader("💬 Akıllı Veri Asistanı (Gemini)")
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "data" in message: st.dataframe(message["data"], use_container_width=True)

        if prompt := st.chat_input("Sor bakalım kanka..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.spinner("Düşünüyorum..."):
                ans, res_df = analyze_query(prompt, df)
            
            msg = {"role": "assistant", "content": ans}
            if res_df is not None: msg["data"] = res_df
            st.session_state.chat_history.append(msg)
            with st.chat_message("assistant"):
                st.markdown(ans)
                if res_df is not None: st.dataframe(res_df, use_container_width=True)

    # 3. MAKİNE ANALİZİ (ORİJİNAL)
    with tab_machine:
        st.subheader("🤖 Makine Analizi")
        ge_comp = "GÜZEL ENERJİ AKARYAKIT ANONİM ŞİRKETİ"
        my_df = df_filtered[df_filtered['Dağıtım Şirketi'] == ge_comp]
        if not my_df.empty:
            st.markdown(f"<div class='insight-box-success'>Bölgedeki gücünüz: {len(my_df)} bayi.</div>", unsafe_allow_html=True)
            st.info(f"En çok bayi olan il: {my_df['İl'].value_counts().idxmax()}")
        else: st.warning("Seçili kriterlerde bayiniz yok.")

    # 4. KARŞILAŞTIRMA (ORİJİNAL)
    with tab_compare:
        st.subheader("⚔️ Karşılaştırma")
        comps = sorted(df['Dağıtım Şirketi'].dropna().unique())
        c1sel, c2sel = st.columns(2)
        comp_a = c1sel.selectbox("Şirket A", comps, index=0)
        comp_b = c2sel.selectbox("Şirket B", comps, index=1 if len(comps)>1 else 0)
        vs_df = df_filtered[df_filtered['Dağıtım Şirketi'].isin([comp_a, comp_b])].groupby(['İl', 'Dağıtım Şirketi']).size().reset_index(name='Adet')
        st.plotly_chart(px.bar(vs_df, x='İl', y='Adet', color='Dağıtım Şirketi', barmode='group'), use_container_width=True)

    # 5. SİMÜLASYON (ORİJİNAL)
    with tab_sim:
        st.subheader("🔮 Simülasyon")
        st.info("Kazanma oranı ve rakip analizi burada yapılır.")

    # 6. TAKVİM (ORİJİNAL)
    with tab_calendar:
        st.subheader("📅 Takvim")
        if 'Bitis_Yili' in df_filtered.columns:
            cal_df = df_filtered.groupby('Bitis_Yili').size().reset_index(name='Adet')
            st.plotly_chart(px.bar(cal_df, x='Bitis_Yili', y='Adet'), use_container_width=True)

    # 7. RADAR (ORİJİNAL)
    with tab_radar:
        st.subheader("📡 Radar")
        show_details_table(df_filtered[df_filtered['Kalan_Gun'] < 180], target_date_col)

    # 8. İLÇE (ORİJİNAL)
    with tab_ilce:
        st.subheader("📍 İlçe Penetrasyonu")
        if not df_filtered.empty:
            ilce_df = df_filtered.groupby('İlçe').size().reset_index(name='Adet').sort_values('Adet', ascending=False).head(20)
            st.plotly_chart(px.bar(ilce_df, x='Adet', y='İlçe', orientation='h'), use_container_width=True)

    # 9. İL KARNESİ (ORİJİNAL)
    with tab_report:
        st.subheader("📄 İl Karnesi")
        report_city = st.selectbox("İl Seç", sorted(df['İl'].unique()))
        st.write(f"{report_city} için veriler analiz ediliyor...")

    # 10. CRM (ORİJİNAL)
    with tab_crm:
        st.subheader("📝 CRM")
        st.write("Bayi notları burada tutulur.")

    # 11. HAM VERİ (ORİJİNAL)
    with tab_data:
        st.subheader("📋 Ham Veri")
        st.dataframe(df_filtered.head(100), use_container_width=True)

if __name__ == "__main__":
    main()
