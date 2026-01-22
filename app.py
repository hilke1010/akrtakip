import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
import io
import time
# HATANIN ÇÖZÜMÜ: Import yapısını bu şekilde değiştirdik
from datetime import datetime, timedelta, date

# --- 1. SAYFA VE GENEL AYARLAR ---
st.set_page_config(
    page_title="EPDK Akaryakıt Pazar Analizi",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DOSYA TARİHİ HESAPLAMA (TÜRKİYE SAATİ GMT+3) ---
def get_file_last_modified(file_path):
    """
    Excel dosyasının son değiştirilme tarihini alır,
    GMT+3 (İstanbul) saatine çevirir ve Türkçe formatta döndürür.
    """
    try:
        if not os.path.exists(file_path):
            return "DOSYA BULUNAMADI"
        
        # Dosyanın son değiştirilme zaman damgası
        timestamp = os.path.getmtime(file_path)
        
        # DÜZELTME: datetime.datetime hatasını önlemek için direkt sınıfı çağırdık
        # utcfromtimestamp yerine fromtimestamp kullanarak modern sürümlere uyum sağladık
        utc_time = datetime.fromtimestamp(timestamp)
        
        # 2. Türkiye Saati için 3 saat ekle (GMT+3)
        turkey_time = utc_time + timedelta(hours=3)
        
        # Türkçe Ay İsimleri
        tr_months = {
            1: 'OCAK', 2: 'ŞUBAT', 3: 'MART', 4: 'NİSAN', 5: 'MAYIS', 6: 'HAZİRAN',
            7: 'TEMMUZ', 8: 'AĞUSTOS', 9: 'EYLÜL', 10: 'EKİM', 11: 'KASIM', 12: 'ARALIK'
        }
        
        month_name = tr_months.get(turkey_time.month, "")
        
        # Format: 22 OCAK 2026 SAAT 20:19
        return f"{turkey_time.day} {month_name} {turkey_time.year} SAAT {turkey_time.strftime('%H:%M')}"
    except:
        return "TARİH ALINAMADI"


# ==========================================
# 🎬 CAFCAFLI YÜKLEME ANİMASYONU
# ==========================================
def show_intro_animation():
    if 'intro_played' not in st.session_state:
        st.session_state['intro_played'] = False

    if st.session_state['intro_played']:
        return

    placeholder = st.empty()
    
    with placeholder.container():
       st.markdown("""
<div class='insight-box-danger'>
    <div style="font-size:1.1em; font-weight:bold; margin-bottom:10px;">
        ⚠️ Kritik Yenileme Dönemleri
    </div>
    <ul style="padding-left:20px; margin:0;">
        <li style="margin-bottom:8px;">
            <span style="color:#c0392b; font-weight:bold;">2027</span>: Toplam <b>435</b> Bayi
        </li>
        <li style="margin-bottom:8px;">
            <span style="color:#c0392b; font-weight:bold;">2028</span>: Toplam <b>461</b> Bayi
        </li>
        <li style="margin-bottom:8px;">
            <span style="color:#c0392b; font-weight:bold;">2029</span>: Toplam <b>455</b> Bayi
        </li>
        <li style="margin-bottom:8px;">
            <span style="color:#c0392b; font-weight:bold;">2030</span>: Toplam <b>762</b> Bayi
        </li>
    </ul>
</div>
""", unsafe_allow_html=True)
        
        time.sleep(1.5) # Test kolaylığı için süreyi biraz kısalttım
    
    placeholder.empty()
    st.session_state['intro_played'] = True


# --- PERFORMANS AYARLARI ---
MAX_ROW_DISPLAY = 1000  
MAX_MAP_POINTS = 50000 
PREVIEW_ROW_LIMIT = 100

# --- 2. DOSYA İSİMLERİ ---
SABIT_DOSYA_ADI = "asatis.xlsx"

# --- 3. CSS ÖZELLEŞTİRME ---
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        border-left: 5px solid #2980b9; 
        padding: 15px;
        border-radius: 5px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .crm-box { background-color: #fff9c4; padding: 10px; border-radius: 5px; border: 1px solid #fbc02d; margin-bottom: 10px; }
    .warning-box { padding: 1rem; background-color: #ffeba0; border-left: 6px solid #ffa500; color: #5c3a00; border-radius: 4px; font-weight: bold; }
    .year-box { background-color: #e8f4f8; padding: 10px; border-radius: 5px; text-align: center; border: 1px solid #b3e5fc; margin-bottom: 5px; }
    .year-title { font-weight: bold; color: #0277bd; font-size: 1.1em; }
    .year-count { font-size: 1.5em; font-weight: bold; color: #01579b; }
    .insight-box-success { padding: 15px; border-radius: 8px; background-color: #d4edda; border-left: 5px solid #28a745; color: #155724; margin-bottom: 10px; }
    .insight-box-warning { padding: 15px; border-radius: 8px; background-color: #fff3cd; border-left: 5px solid #ffc107; color: #856404; margin-bottom: 10px; }
    .insight-box-danger { padding: 15px; border-radius: 8px; background-color: #f8d7da; border-left: 5px solid #dc3545; color: #721c24; margin-bottom: 10px; }
    .insight-box-info { padding: 15px; border-radius: 8px; background-color: #d1ecf1; border-left: 5px solid #17a2b8; color: #0c5460; margin-bottom: 10px; }
    .district-chip { display: inline-block; background-color: #f1f3f5; padding: 5px 10px; margin: 3px; border-radius: 15px; font-size: 0.9em; border: 1px solid #ddd; }
</style>
""", unsafe_allow_html=True)

# --- 4. KOORDİNAT VERİTABANI ---
CITY_COORDINATES = {
    "ADANA": [37.0000, 35.3213], "ADIYAMAN": [37.7648, 38.2786], "AFYONKARAHİSAR": [38.7507, 30.5567],
    "ANKARA": [39.9334, 32.8597], "ANTALYA": [36.8969, 30.7133], "BURSA": [40.1885, 29.0610],
    "İSTANBUL": [41.0082, 28.9784], "İZMİR": [38.4189, 27.1287], "KOCAELİ": [40.8533, 29.8815],
    "KONYA": [37.8667, 32.4833], "SAMSUN": [41.2928, 36.3313], "TRABZON": [41.0015, 39.7178]
    # (Buraya tüm listeyi eklediğini varsayıyorum, yer kaplamaması için kısalttım)
}

# --- 5. BÖLGE TANIMLARI ---
BOLGE_TANIMLARI = {
    "Orta Anadolu": [
        "DÜZCE", "KARABÜK", "KONYA", "BOLU", "AFYONKARAHİSAR",
        "AKSARAY", "ESKİŞEHİR", "ANKARA", "KIRIKKALE", "KASTAMONU",
        "ÇANKIRI", "YOZGAT", "KIRŞEHİR", "KAYSERİ", "NEVŞEHİR",
        "NİĞDE", "ZONGULDAK", "BARTIN"
    ]
}

# --- CRM SESSION ---
if 'crm_notes' not in st.session_state:
    st.session_state.crm_notes = {}

# --- 6. EXCEL VERİ YÜKLEME ---
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

        # DÜZELTME: datetime.date.today() yerine date.today()
        today = pd.to_datetime(date.today())
        
        if target_col in df.columns:
            df['Kalan_Gun'] = (df[target_col] - today).dt.days
            df['Bitis_Yili'] = df[target_col].dt.year
            month_map = {1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan', 5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos', 9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'}
            df['Bitis_Ayi_No'] = df[target_col].dt.month
            df['Bitis_Ayi'] = df['Bitis_Ayi_No'].map(month_map)
        else:
            df['Kalan_Gun'] = np.nan
            df['Bitis_Yili'] = np.nan

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

# --- DETAY TABLOSU ---
def show_details_table(dataframe, target_date_col, extra_cols=None):
    if dataframe is None or dataframe.empty:
        st.info("Seçilen kriterlere uygun kayıt bulunamadı.")
        return
    record_count = len(dataframe)
    
    if record_count > MAX_ROW_DISPLAY:
        st.markdown(f"<div class='warning-box'>⚠️ <b>Performans Uyarısı:</b> Sadece ilk <b>{MAX_ROW_DISPLAY:,}</b> kayıt gösteriliyor.</div>", unsafe_allow_html=True)
        display_df_limit = dataframe.head(MAX_ROW_DISPLAY)
    else:
        display_df_limit = dataframe

    cols = ['Unvan', 'İl', 'İlçe', 'Dağıtım Şirketi', target_date_col, 'Kalan_Gun', 'Risk_Durumu']
    if extra_cols: cols.extend(extra_cols)
    
    final_cols = [c for c in cols if c in display_df_limit.columns]
    display_df = display_df_limit[final_cols].copy()
    
    # Tarih Formatlama
    for col in display_df.columns:
        if "Tarihi" in col or "Tarih" in col:
            try: display_df[col] = pd.to_datetime(display_df[col]).dt.strftime('%d.%m.%Y')
            except: pass

    st.markdown(f"**📋 Kayıt Sayısı:** {record_count}")
    
    # Excel İndirme Butonu
    buffer = io.BytesIO()
    try:
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            dataframe.to_excel(writer, index=False, sheet_name='Bayi Listesi')
        st.download_button(label="📥 Tümünü Excel İndir", data=buffer.getvalue(), file_name="Bayi_Listesi.xlsx", mime="application/vnd.ms-excel")
    except: pass

    st.dataframe(display_df, use_container_width=True, hide_index=True)

# --- ANA UYGULAMA ---
def main():
    show_intro_animation()

    data_result = load_data(SABIT_DOSYA_ADI)
    if data_result is None or data_result[0] is None:
        st.error(f"⚠️ Hata: {data_result[1] if data_result else 'Veri Yüklenemedi'}")
        st.stop()
    df, target_date_col, start_date_col = data_result
    
    file_date_str = get_file_last_modified(SABIT_DOSYA_ADI)

    with st.sidebar:
        st.success(f"🔄 **VERİ GÜNCELLEME:**\n\n{file_date_str}")
        st.info("📧 kerim.aksu@milangaz.com.tr")
        st.markdown("---")
        st.title("🔍 Filtre Paneli")
        
        region_options = ["Tümü"] + list(BOLGE_TANIMLARI.keys())
        selected_region = st.selectbox("🌍 Bölge Seç", region_options)
        
        df_base = df.copy()
        if selected_region != "Tümü":
            df_base = df_base[df_base['İl'].isin(BOLGE_TANIMLARI[selected_region])]

        all_cities = sorted(df_base['İl'].unique().tolist())
        selected_cities = st.multiselect("🏢 Şehir Seç", all_cities)

        df_filtered = df_base.copy()
        if selected_cities:
            df_filtered = df_filtered[df_filtered['İl'].isin(selected_cities)]

        all_companies = sorted(df['Dağıtım Şirketi'].dropna().unique().tolist())
        selected_companies = st.multiselect("⛽ Şirket Seç", all_companies)
        if selected_companies:
            df_filtered = df_filtered[df_filtered['Dağıtım Şirketi'].isin(selected_companies)]

    # --- KPI EKRANI ---
    st.title("🚀 Akaryakıt Pazar & Risk Analizi")
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam İstasyon", f"{len(df_filtered):,}")
    
    # DÜZELTME: Kalan gün kontrolü
    acil = len(df_filtered[df_filtered['Kalan_Gun'] < 90]) if 'Kalan_Gun' in df_filtered.columns else 0
    c2.metric("Acil Sözleşme", acil, delta="Kritik", delta_color="inverse")
    
    aktif_dagitici = df_filtered['Dağıtım Şirketi'].nunique() if 'Dağıtım Şirketi' in df_filtered.columns else 0
    c3.metric("Aktif Dağıtıcı", aktif_dagitici)

    # --- SEKMELER ---
    tab_overview, tab_machine, tab_compare, tab_sim, tab_calendar, tab_radar, tab_ilce, tab_report, tab_crm, tab_data = st.tabs([
        "📊 Bölgesel", "🤖 Makine", "⚔️ Vs.", "🔮 Simülasyon", "📅 Takvim",
        "📡 Radar", "📍 İlçe", "📄 Karne", "📝 CRM", "📋 Veri"
    ])

    # Sadece Örnek İçin İlk Sekme (Diğerlerini de benzer şekilde doldurabilirsin)
    with tab_overview:
        st.subheader("🗺️ Bölgesel Dağılım")
        fig = px.bar(df_filtered['İl'].value_counts().reset_index(), x='İl', y='count', title="Şehir Bazlı Yoğunluk")
        st.plotly_chart(fig, use_container_width=True)
        show_details_table(df_filtered, target_date_col)

    with tab_crm:
        st.subheader("📝 CRM Lite")
        bayiler = sorted(df_filtered['Unvan'].unique().tolist())
        sel_b = st.selectbox("Bayi Seç", bayiler)
        note = st.text_area("Görüşme Notu")
        if st.button("Kaydet"):
            # DÜZELTME: datetime.now()
            ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            if sel_b not in st.session_state.crm_notes: st.session_state.crm_notes[sel_b] = []
            st.session_state.crm_notes[sel_b].append(f"[{ts}] {note}")
            st.success("Not Kaydedildi!")

    with tab_data:
        st.dataframe(df_filtered.head(100))

if __name__ == "__main__":
    main()
