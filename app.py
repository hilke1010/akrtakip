import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
import io
import time
# DÜZELTME: Hata veren kısmı buradaki import şekliyle çözdük
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
        
        # DÜZELTME: utcfromtimestamp yerine fromtimestamp (Python 3.12+ uyumlu)
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
        <style>
            .intro-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: linear-gradient(-45deg, #021B79, #0575E6, #FF8C00, #ff4e00);
                background-size: 400% 400%;
                animation: gradientBG 6s ease infinite;
                z-index: 999999;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                color: white;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            @keyframes gradientBG {
                0% {background-position: 0% 50%;}
                50% {background-position: 100% 50%;}
                100% {background-position: 0% 50%;}
            }
            .intro-icon {
                font-size: 8rem;
                margin-bottom: 20px;
                animation: bounce 2s infinite;
                text-shadow: 0 10px 30px rgba(0,0,0,0.5);
            }
            .intro-title {
                font-size: 5rem;
                font-weight: 900;
                text-transform: uppercase;
                color: #ffffff;
                text-shadow: 4px 4px 0px #021B79, 8px 8px 20px rgba(0,0,0,0.4);
                animation: fadeInUp 1.2s ease-out;
                text-align: center;
                letter-spacing: 4px;
                margin: 0;
                padding: 0;
            }
            .intro-subtitle {
                font-size: 1.8rem;
                color: #FFD700;
                margin-top: 15px;
                font-weight: 600;
                text-shadow: 1px 1px 5px rgba(0,0,0,0.5);
                animation: fadeInUp 1.6s ease-out;
                letter-spacing: 2px;
            }
            .loading-bar-container {
                width: 350px;
                height: 8px;
                background: rgba(255,255,255,0.3);
                margin-top: 50px;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 0 15px rgba(255, 140, 0, 0.5);
            }
            .loading-bar {
                width: 100%;
                height: 100%;
                background: #fff;
                transform-origin: left;
                animation: load 2.5s cubic-bezier(0.4, 0, 0.2, 1) forwards;
            }
            @keyframes bounce {
                0%, 20%, 50%, 80%, 100% {transform: translateY(0);}
                40% {transform: translateY(-30px);}
                60% {transform: translateY(-15px);}
            }
            @keyframes fadeInUp {
                from { opacity: 0; transform: translateY(50px); }
                to { opacity: 1; transform: translateY(0); }
            }
            @keyframes load {
                0% { transform: scaleX(0); }
                100% { transform: scaleX(1); }
            }
        </style>

        <div class="intro-overlay">
            <div class="intro-icon">⛽</div>
            <h1 class="intro-title">AKARYAKIT<br>BAYİ ANALİZİ</h1>
            <div class="intro-subtitle">GÜNCEL PAZAR VERİLERİ YÜKLENİYOR...</div>
            <div class="loading-bar-container">
                <div class="loading-bar"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        time.sleep(2.5)
    
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

# --- 4. KOORDİNAT VERİTABANI (İL MERKEZLERİ) ---
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

        # DÜZELTME: datetime.date.today() hatası giderildi, direkt date.today()
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
            df['Bitis_Ayi'] = np.nan
            df['Bitis_Ayi_No'] = np.nan

        # Sözleşme Süresi Hesaplama
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
        st.markdown(f"<div class='warning-box'>⚠️ <b>Performans Uyarısı:</b> Listede toplam <b>{record_count:,}</b> kayıt var.<br>Tarayıcınızın donmaması için aşağıda sadece ilk <b>{MAX_ROW_DISPLAY:,}</b> tanesi gösterilmektedir.<br>Tüm listeyi görmek için lütfen aşağıdaki <b>Excel İndir</b> butonunu kullanın.</div>", unsafe_allow_html=True)
        display_df_limit = dataframe.head(MAX_ROW_DISPLAY)
    else:
        display_df_limit = dataframe

    cols = ['Unvan', 'İl', 'İlçe', 'Dağıtım Şirketi', target_date_col, 'Kalan_Gun', 'Sozlesme_Suresi_Gun', 'Risk_Durumu']
    if extra_cols:
        cols.extend(extra_cols)
    
    seen = set()
    final_cols = [c for c in cols if c in display_df_limit.columns and not (c in seen or seen.add(c))]
    
    display_df = display_df_limit[final_cols].copy()
    
    date_columns = [col for col in display_df.columns if "Tarihi" in col or "Tarih" in col]
    for date_col in date_columns:
        try: display_df[date_col] = pd.to_datetime(display_df[date_col]).dt.strftime('%d.%m.%Y')
        except: pass

    if 'Kalan_Gun' in display_df.columns: display_df = display_df.sort_values('Kalan_Gun')
    
    def highlight_risk(val):
        if not isinstance(val, (int, float)): return ''
        if val < 0: return 'background-color: #ffcccc'
        elif val < 90: return 'background-color: #ffe5cc'
        elif val < 180: return 'background-color: #ffffcc'
        return ''
    
    st.markdown(f"**📋 Listelenen Bayi Sayısı:** {len(display_df)}")
    
    if record_count > 0:
        buffer = io.BytesIO()
        try:
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                dataframe.to_excel(writer, index=False, sheet_name='Bayi Listesi')
            st.download_button(label=f"📥 Tüm Listeyi Excel İndir ({record_count} Kayıt)", data=buffer.getvalue(), file_name="Bayi_Listesi.xlsx", mime="application/vnd.ms-excel")
        except: pass

    if 'Kalan_Gun' in display_df.columns:
        st.dataframe(display_df.style.map(highlight_risk, subset=['Kalan_Gun']), use_container_width=True, hide_index=True)
    else:
        st.dataframe(display_df, use_container_width=True, hide_index=True)

# --- ANA UYGULAMA ---
def main():
    # 1. Animasyonu Oynat
    show_intro_animation()

    # 2. Verileri Yükle
    data_result = load_data(SABIT_DOSYA_ADI)
    if data_result is None or data_result[0] is None:
        st.error(f"⚠️ Hata: {data_result[1] if data_result else 'Veri Yüklenemedi'}")
        st.stop()
    df, target_date_col, start_date_col = data_result
    
    # 3. Dosyanın Son Değiştirilme Tarihini Al (OTOMATİK GMT+3)
    file_date_str = get_file_last_modified(SABIT_DOSYA_ADI)

    with st.sidebar:
        # OTOMATİK TARİH GÖSTERİMİ
        st.success(f"🔄 **VERİ GÜNCELLEME:**\n\n{file_date_str}")
        
        # DESTEK MESAJI
        st.info("💡 **Gelişmeye destek olur musunuz?**\n\n📧 kerim.aksu@milangaz.com.tr")

        st.markdown("---")
        st.title("🔍 Filtre Paneli")
        
        region_options = ["Tümü"] + list(BOLGE_TANIMLARI.keys())
        selected_region = st.selectbox("🌍 Bölge Seç", region_options)
        if selected_region != "Tümü":
            target_cities = BOLGE_TANIMLARI[selected_region]
            df_for_sidebar = df[df['İl'].isin(target_cities)]
        else: df_for_sidebar = df.copy()

        all_cities = sorted(df_for_sidebar['İl'].unique().tolist()) if 'İl' in df_for_sidebar.columns else []
        selected_cities = st.multiselect("🏢 Şehir Seç", all_cities)

        if selected_cities:
            filtered_districts = sorted(df_for_sidebar[df_for_sidebar['İl'].isin(selected_cities)]['İlçe'].unique().tolist())
        else:
            filtered_districts = sorted(df_for_sidebar['İlçe'].unique().tolist()) if 'İlçe' in df_for_sidebar.columns else []
        selected_districts = st.multiselect("📍 İlçe Seç", filtered_districts)

        all_companies = sorted(df['Dağıtım Şirketi'].dropna().astype(str).unique().tolist()) if 'Dağıtım Şirketi' in df.columns else []
        selected_companies = st.multiselect("⛽ Şirket Seç", all_companies)

        st.markdown("---")
        st.header("🔗 Diğer Uygulamalar")
        st.markdown("[📊 EPDK LPG Sektör Raporu](https://pazarpayi.streamlit.app/)")
        st.markdown("[📰 Haber Aracı](https://newslpg.streamlit.app/)")
        st.markdown("[📱 Mobil Hesaplayıcı](https://lpg2026.streamlit.app/)")

    # Filtreleme
    df_filtered = df.copy()
    if selected_region != "Tümü": df_filtered = df_filtered[df_filtered['İl'].isin(region_cities := BOLGE_TANIMLARI[selected_region])]
    if selected_cities: df_filtered = df_filtered[df_filtered['İl'].isin(selected_cities)]
    if selected_districts: df_filtered = df_filtered[df_filtered['İlçe'].isin(selected_districts)]
    
    df_filtered_geo_only = df_filtered.copy()
    if selected_companies: df_filtered = df_filtered[df_filtered['Dağıtım Şirketi'].isin(selected_companies)]

    # --- KPI ---
    st.title("🚀 Akaryakıt Pazar & Risk Analizi")
    if selected_region != "Tümü": st.caption(f"📍 Şu anda **{selected_region}** verileri görüntüleniyor.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam İstasyon", f"{len(df_filtered):,}")
    acil_durum = len(df_filtered[df_filtered['Kalan_Gun'] < 90]) if 'Kalan_Gun' in df_filtered.columns else 0
    c2.metric("Acil Sözleşme", acil_durum, delta="Acil Yenileme", delta_color="inverse")
    aktif_dagitici = df_filtered['Dağıtım Şirketi'].nunique() if 'Dağıtım Şirketi' in df_filtered.columns else 0
    c3.metric("Aktif Dağıtıcı", aktif_dagitici)
    
    # --- AKTİF FİLTRE BİLGİSİ ---
    active_filters = []
    if selected_region != "Tümü": active_filters.append(f"🌍 Bölge: {selected_region}")
    if selected_cities: active_filters.append(f"🏙️ İl: {', '.join(selected_cities)}")
    if selected_districts: active_filters.append(f"📍 İlçe: {', '.join(selected_districts)}")
    if selected_companies: active_filters.append(f"⛽ Şirket: {', '.join(selected_companies)}")

    if active_filters:
        st.info("🔍 **Aktif Filtreler:** " + "  |  ".join(active_filters))
    else:
        st.info("🔍 **Aktif Filtreler:** Tüm Türkiye Verisi")
    # --------------------------------------------------

    st.divider()

    # --- SEKMELER ---
    tab_overview, tab_machine, tab_compare, tab_sim, tab_calendar, tab_radar, tab_ilce, tab_report, tab_crm, tab_data = st.tabs([
        "📊 Bölgesel & Durum",
        "🤖 Makine Analizi",     
        "⚔️ Karşılaştırma (Vs.)", 
        "🔮 Simülasyon",         
        "📅 Takvim",
        "📡 Sözleşme Radar", 
        "📍 İlçe Penetrasyonu",
        "📄 İl Karnesi", 
        "📝 CRM Lite",            
        "📋 Ham Veri"
    ])

    # 1. BÖLGESEL & DURUM
    with tab_overview:
        st.subheader("🗺️ Bölgesel Yoğunluk Haritası")
        
        if len(df_filtered) > MAX_MAP_POINTS:
            st.warning(f"⚠️ Haritada {len(df_filtered):,} nokta var. Performans için filtreleyin.")
        elif not df_filtered.empty:
            map_data = df_filtered['İl'].value_counts().reset_index()
            map_data.columns = ['İl', 'Adet']
            map_data['lat'] = map_data['İl'].map(lambda x: CITY_COORDINATES.get(x, [None, None])[0])
            map_data['lon'] = map_data['İl'].map(lambda x: CITY_COORDINATES.get(x, [None, None])[1])
            map_data = map_data.dropna(subset=['lat', 'lon'])

            if not map_data.empty:
                fig_map = px.scatter_mapbox(
                    map_data, lat="lat", lon="lon", size="Adet", color="Adet",
                    hover_name="İl", size_max=35, zoom=5 if selected_region == "Tümü" else 6, 
                    mapbox_style="open-street-map", color_continuous_scale=px.colors.sequential.Bluered,
                    title="İl Bazlı Bayi Yoğunluğu"
                )
                if selected_region != "Tümü":
                    center_lat, center_lon = map_data['lat'].mean(), map_data['lon'].mean()
                    fig_map.update_layout(mapbox_center={"lat": center_lat, "lon": center_lon})
                else:
                    fig_map.update_layout(mapbox_center={"lat": 39.0, "lon": 35.0}, mapbox_zoom=4.8)
                fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
                st.plotly_chart(fig_map, use_container_width=True)
                st.info("ℹ️ **Lejand:** 🔴 Koyu = Yüksek Yoğunluk, 🔵 Açık = Düşük Yoğunluk, ⚪ Büyüklük = İstasyon Sayısı")

        st.divider()
        st.subheader("📊 İstatistikler")
        
        city_stats = df_filtered['İl'].value_counts().reset_index()
        city_stats.columns = ['İl', 'Total']
        ge_comp_name = "GÜZEL ENERJİ AKARYAKIT ANONİM ŞİRKETİ"
        ge_df = df_filtered[df_filtered['Dağıtım Şirketi'] == ge_comp_name]
        ge_counts = ge_df['İl'].value_counts().reset_index()
        ge_counts.columns = ['İl', 'GE_Count']
        merged_stats = pd.merge(city_stats, ge_counts, on='İl', how='left').fillna(0)
        
        def get_bar_label(row):
            total = int(row['Total'])
            ge_c = int(row['GE_Count'])
            share = (ge_c / total * 100) if total > 0 else 0
            return f"<b>{total}</b><br><span style='font-size:11px; color:#555'>GE: {ge_c} (%{share:.1f})</span>"
        
        merged_stats['Label'] = merged_stats.apply(get_bar_label, axis=1)
        fig_city = px.bar(merged_stats, x='İl', y='Total', text='Label', title="Şehir Sıralaması (Toplam & Güzel Enerji Payı)", color='Total', color_continuous_scale='Blues')
        fig_city.update_traces(textposition='outside', cliponaxis=False)
        fig_city.update_layout(yaxis=dict(title='Toplam Bayi Sayısı'), margin=dict(t=50, b=100))
        st.plotly_chart(fig_city, use_container_width=True, on_select="rerun", key="overview_bar_chart")
        st.caption("ℹ️ *👇 Grafiğin çubuklarına tıklayarak aşağıdaki listeyi filtreleyebilirsiniz.*")

        st.markdown("---")
        
        col_pie1, col_pie2 = st.columns(2)
        with col_pie1:
            city_pie_data = df_filtered['İl'].value_counts().reset_index()
            city_pie_data.columns = ['İl', 'Adet']
            if len(city_pie_data) > 10:
                top_10 = city_pie_data.iloc[:10]
                others = pd.DataFrame({'İl': ['DİĞER'], 'Adet': [city_pie_data.iloc[10:]['Adet'].sum()]})
                city_pie_data = pd.concat([top_10, others])
            fig_city_pie = px.pie(city_pie_data, values='Adet', names='İl', hole=0.4, title="Şehir Dağılımı (%)")
            st.plotly_chart(fig_city_pie, use_container_width=True)

        with col_pie2:
            if 'Dağıtım Şirketi' in df_filtered.columns:
                dist_pie_data = df_filtered['Dağıtım Şirketi'].value_counts().reset_index()
                dist_pie_data.columns = ['Dağıtım Şirketi', 'Adet']
                fig_dist_pie = px.pie(dist_pie_data, values='Adet', names='Dağıtım Şirketi', hole=0.4, title="Pazar Payı (Dağıtıcı)")
                st.plotly_chart(fig_dist_pie, use_container_width=True)

        selected_chart_city = None
        try:
            if st.session_state.get("overview_bar_chart") and st.session_state["overview_bar_chart"]['selection']['points']:
                selected_chart_city = st.session_state["overview_bar_chart"]['selection']['points'][0]['x']
                st.success(f"📌 **{selected_chart_city}** detayları listeleniyor:")
                filtered_table = df_filtered[df_filtered['İl'] == selected_chart_city]
            else: filtered_table = df_filtered
        except: filtered_table = df_filtered
        show_details_table(filtered_table, target_date_col)

    # 2. MAKİNE ANALİZİ
    with tab_machine:
        st.subheader("🤖 Makine Analizi (Akıllı Asistan)")
        st.markdown("Veriler taranarak **GÜZEL ENERJİ AKARYAKIT ANONİM ŞİRKETİ** için özel stratejik notlar oluşturuldu.")
        
        col_ma1, col_ma2 = st.columns([1,3])
        with col_ma1:
            analiz_bolge = st.selectbox("Analiz Bölgesi", ["Tümü"] + list(BOLGE_TANIMLARI.keys()), key="ma_region")
        
        my_company = "GÜZEL ENERJİ AKARYAKIT ANONİM ŞİRKETİ"
        if analiz_bolge != "Tümü":
            scope_df = df[df['İl'].isin(BOLGE_TANIMLARI[analiz_bolge])]
            st.caption(f"📍 **Kapsam:** {analiz_bolge} Bölgesi")
        else:
            scope_df = df.copy()
            st.caption("📍 **Kapsam:** Tüm Türkiye")

        my_df = scope_df[scope_df['Dağıtım Şirketi'] == my_company]
        
        if not my_df.empty:
            top_city = my_df['İl'].value_counts().idxmax()
            top_city_count = my_df['İl'].value_counts().max()
            st.markdown(f"<div class='insight-box-success'><b>🏆 En Güçlü Kale:</b><br>Şirketin bu bölgedeki en yoğun olduğu il <b>{top_city}</b> ({top_city_count} Bayi).</div>", unsafe_allow_html=True)

            all_scope_districts = scope_df['İlçe'].unique()
            my_districts = my_df['İlçe'].unique()
            missing_districts = sorted(list(set(all_scope_districts) - set(my_districts)))
            district_market_size = scope_df['İlçe'].value_counts()

            if len(missing_districts) > 0:
                st.markdown(f"<div class='insight-box-warning'><b>🚀 Büyüme Fırsatları (Boş Noktalar):</b><br>Bu bölgede toplam <b>{len(missing_districts)}</b> ilçede hiç bayiniz bulunmuyor.</div>", unsafe_allow_html=True)
                with st.expander("📄 Tüm Eksik İlçeleri Listele (Üzerine Gelip Pazar Büyüklüğünü Görün)", expanded=False):
                    html_chips = ""
                    for dist in missing_districts:
                        total_stations = district_market_size.get(dist, 0)
                        tooltip_text = f"{dist}: Bizde 0, Toplam Pazar: {total_stations} Bayi"
                        html_chips += f'<span class="district-chip" title="{tooltip_text}">{dist}</span>'
                    st.markdown(html_chips, unsafe_allow_html=True)
                    st.info("💡 **İpucu:** İlçelerin üzerine gelerek toplam rakip istasyon sayısını görebilirsiniz.")
            
            if 'Bitis_Yili' in my_df.columns:
                current_year = datetime.now().year
                future_expirations = my_df[my_df['Bitis_Yili'] >= current_year]['Bitis_Yili'].value_counts().sort_index()
                if not future_expirations.empty:
                    msg_list = "<ul>"
                    total_future = 0
                    for year, count in future_expirations.items():
                        yr_text = f"{int(year)} (Bu Yıl)" if year == current_year else f"{int(year)}"
                        msg_list += f"<li><b>{yr_text}:</b> {count} adet sözleşme</li>"
                        total_future += count
                    msg_list += "</ul>"
                    st.markdown(f"<div class='insight-box-danger'><b>⚠️ Kritik Yenileme Dönemleri:</b><br>Toplamda <b>{total_future}</b> sözleşme sona erecek.<br>{msg_list}</div>", unsafe_allow_html=True)
            
            total_market = len(scope_df)
            my_share = len(my_df)
            share_pct = (my_share / total_market) * 100
            
            col_share_text, col_share_chart = st.columns([1, 1])
            with col_share_text:
                st.markdown(f"<div class='insight-box-info'><b>📊 Pazar Payı:</b><br>Bölgedeki payınız: <b>%{share_pct:.1f}</b>.<br>Toplam İstasyon: <b>{total_market}</b><br>Sizin İstasyonunuz: <b>{my_share}</b></div>", unsafe_allow_html=True)
            with col_share_chart:
                others_share = total_market - my_share
                fig_my_share = px.pie(names=['GÜZEL ENERJİ', 'RAKİPLER'], values=[my_share, others_share], hole=0.5, title=f"Bölgesel Hakimiyet Oranı", color_discrete_sequence=['#2ecc71', '#e74c3c'])
                fig_my_share.update_layout(margin=dict(t=30, b=0, l=0, r=0))
                st.plotly_chart(fig_my_share, use_container_width=True)
        else:
            st.warning(f"Seçilen bölgede ({analiz_bolge}) GÜZEL ENERJİ verisine rastlanmadı.")

    # 3. KARŞILAŞTIRMA (VS.)
    with tab_compare:
        st.subheader("⚔️ Head-to-Head Rakip Analizi")
        st.markdown("Soldaki **Bölge/İl/İlçe** filtreleri geçerlidir. **Şirket** filtresi devre dışı bırakılmıştır.")
        if 'Dağıtım Şirketi' in df.columns:
            comp_list = sorted(df['Dağıtım Şirketi'].dropna().astype(str).unique().tolist())
            if len(comp_list) >= 2:
                c_sel1, c_sel2 = st.columns(2)
                comp_a = c_sel1.selectbox("1. Şirket (Taraf A)", comp_list, index=0)
                comp_b = c_sel2.selectbox("2. Şirket (Taraf B)", comp_list, index=1 if len(comp_list)>1 else 0)
                
                base_df = df_filtered_geo_only
                df_a = base_df[base_df['Dağıtım Şirketi'] == comp_a]
                df_b = base_df[base_df['Dağıtım Şirketi'] == comp_b]

                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Toplam İstasyon", len(df_a))
                k1.metric(f"{comp_b}", len(df_b), delta=len(df_b)-len(df_a), delta_color="off")
                
                top_a = df_a['İl'].value_counts().idxmax() if not df_a.empty else "-"
                top_b = df_b['İl'].value_counts().idxmax() if not df_b.empty else "-"
                k2.info(f"**En Güçlü:** {top_a}")
                k2.warning(f"**En Güçlü:** {top_b}")

                min_a = df_a['İl'].value_counts().idxmin() if not df_a.empty else "-"
                min_b = df_b['İl'].value_counts().idxmin() if not df_b.empty else "-"
                k3.info(f"**En Zayıf:** {min_a}")
                k3.warning(f"**En Zayıf:** {min_b}")

                if not df_a.empty or not df_b.empty:
                    ca = df_a['İl'].value_counts(); cb = df_b['İl'].value_counts()
                    cities = set(ca.index) | set(cb.index)
                    max_d, max_c, lead = -1, "-", "-"
                    for c in cities:
                        va, vb = ca.get(c,0), cb.get(c,0)
                        d = abs(va-vb)
                        if d > max_d: max_d, max_c, lead = d, c, (comp_a if va>vb else comp_b)
                    k4.error(f"{max_c}")
                    k4.caption(f"Fark: {max_d} ({lead})")
                else: k4.metric("Fark", "-")

                st.divider()
                st.subheader("📊 Şehir Kıyaslaması")
                df_vs = base_df[base_df['Dağıtım Şirketi'].isin([comp_a, comp_b])]
                if not df_vs.empty:
                    city_vs = df_vs.groupby(['İl', 'Dağıtım Şirketi']).size().reset_index(name='Adet')
                    fig_vs = px.bar(city_vs, x='İl', y='Adet', color='Dağıtım Şirketi', barmode='group', title="Tüm Şehirlerde Karşılaştırma")
                    st.plotly_chart(fig_vs, use_container_width=True)
                    st.caption("ℹ️ *Grafiği büyütebilir veya kaydırabilirsiniz.*")
            else: st.warning("Yeterli veri yok.")

    # 4. SİMÜLASYON
    with tab_sim:
        st.subheader("🔮 'What-If' Senaryo Analizi")
        with st.expander("⚙️ Kapsam Daralt", expanded=True):
            cs1, cs2 = st.columns(2)
            sim_reg = cs1.selectbox("Bölge", ["Tümü"] + list(BOLGE_TANIMLARI.keys()))
            sim_cities = sorted(BOLGE_TANIMLARI[sim_reg]) if sim_reg != "Tümü" else sorted(df['İl'].unique().tolist())
            sim_city = cs2.selectbox("İl", ["Tümü"] + sim_cities)
        
        sim_df = df.copy()
        if sim_reg != "Tümü": sim_df = sim_df[sim_df['İl'].isin(BOLGE_TANIMLARI[sim_reg])]
        if sim_city != "Tümü": sim_df = sim_df[sim_df['İl'] == sim_city]
        
        st.markdown("---")
        my_comp = "GÜZEL ENERJİ AKARYAKIT ANONİM ŞİRKETİ"
        st.info(f"🎯 **Odak Şirket:** {my_comp}")
        
        all_comp = sorted(df['Dağıtım Şirketi'].dropna().astype(str).unique().tolist())
        target_comps = [c for c in all_comp if c != my_comp]
        
        cc1, cc2 = st.columns(2)
        target = cc1.selectbox("Hedef Rakip", target_comps) if target_comps else None
        rate = cc2.slider("Kazanma Oranı (%)", 0, 100, 10)
        
        if target:
            curr = len(sim_df[sim_df['Dağıtım Şirketi'] == my_comp])
            targ = len(sim_df[sim_df['Dağıtım Şirketi'] == target])
            gain = int(targ * rate / 100)
            new = curr + gain
            
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("Mevcut", curr)
            sc2.metric("Kazanılacak", f"+{gain}")
            sc3.metric("Yeni Toplam", new, delta=f"%{((new-curr)/curr*100) if curr else 100:.1f}")
            
            scope_text = sim_city if sim_city != "Tümü" else (sim_reg if sim_reg != "Tümü" else "Tüm Türkiye")
            st.markdown(f"""
            <div class="insight-box-info">
                🧮 <b>Hesaplama Detayı:</b><br>
                Seçilen <b>{scope_text}</b> bölgesinde, <b>{target}</b> firmasının toplam <b>{targ}</b> bayisi bulunmaktadır.<br>
                Siz <b>%{rate}</b> oranında dönüşüm hedeflediğiniz için:<br>
                <code>{targ} x {rate/100} = {gain}</code> adet yeni bayi kazanımı öngörülmektedir.
            </div>
            """, unsafe_allow_html=True)

    # 5. TAKVİM
    with tab_calendar:
        st.subheader("📅 Aylık Sözleşme Takvimi")
        if 'Bitis_Yili' in df_filtered.columns:
            yrs = sorted(df_filtered['Bitis_Yili'].dropna().unique().astype(int).tolist())
            if yrs:
                curr_yr = datetime.now().year
                sel_yr = st.selectbox("Yıl", yrs, index=yrs.index(curr_yr) if curr_yr in yrs else 0)
                df_yr = df_filtered[df_filtered['Bitis_Yili'] == sel_yr]
                if not df_yr.empty:
                    m_cnt = df_yr.groupby(['Bitis_Ayi_No']).agg(Adet=('Unvan','count'), Ay=('Bitis_Ayi','first')).reset_index().sort_values('Bitis_Ayi_No')
                    fig_cal = px.bar(m_cnt, x='Ay', y='Adet', text='Adet', title=f"{sel_yr} Dağılımı")
                    sel = st.plotly_chart(fig_cal, use_container_width=True, on_select="rerun", key="cal_sel")
                    st.caption("ℹ️ *👇 Grafiğin çubuklarına tıklayarak aşağıdaki listeyi filtreleyebilirsiniz.*")
                    if sel and sel['selection']['points']:
                        mn = sel['selection']['points'][0]['x']
                        st.success(f"🗓️ **{mn} {sel_yr}**")
                        show_details_table(df_yr[df_yr['Bitis_Ayi']==mn], target_date_col)
                    else: show_details_table(df_yr, target_date_col)

    # 6. SÖZLEŞME RADAR
    with tab_radar:
        st.subheader("📡 Sözleşme Radar (Kısa Süreli Anlaşmalar)")
        st.markdown("Sözleşme Başlangıç ve Bitiş tarihi arasında **3 Aydan (90 gün) az** süre olan kayıtları listeler.")
        
        if 'Sozlesme_Suresi_Gun' in df_filtered.columns and start_date_col:
            radar_df = df_filtered[(df_filtered['Sozlesme_Suresi_Gun'] < 90) & (df_filtered['Sozlesme_Suresi_Gun'] >= 0)]
            if not radar_df.empty:
                st.error(f"⚠️ Toplam **{len(radar_df)}** adet 3 aydan kısa süreli sözleşme tespit edildi.")
                extra_cols = ['Dağıtıcı ile Yapılan Sözleşme Başlangıç Tarihi', 'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi', 'Sozlesme_Suresi_Gun']
                if start_date_col not in extra_cols: extra_cols[0] = start_date_col
                show_details_table(radar_df, target_date_col, extra_cols=extra_cols)
            else:
                st.success("✅ Seçilen kriterlerde 3 aydan kısa süreli (şüpheli) sözleşme bulunmamaktadır.")
        else:
            st.warning("Veri setinde Başlangıç Tarihi sütunu bulunamadı.")

    # 7. İLÇE PENETRASYONU
    with tab_ilce:
        st.subheader("📍 İlçe Bazlı Derinlik")
        if not selected_cities: st.warning("Lütfen sol menüden Şehir seçin.")
        else:
            if not df_filtered.empty:
                d_cnt = df_filtered.groupby(['İlçe']).size().reset_index(name='Adet').sort_values('Adet', ascending=True)
                fig_ilce = px.bar(d_cnt, x='Adet', y='İlçe', orientation='h', text='Adet', height=600)
                sel_ilce = st.plotly_chart(fig_ilce, use_container_width=True, on_select="rerun", key="ilce_sel")
                st.caption("ℹ️ *👇 Grafiğin çubuklarına tıklayarak aşağıdaki listeyi filtreleyebilirsiniz.*")
                if sel_ilce and sel_ilce['selection']['points']:
                    dst = sel_ilce['selection']['points'][0]['y']
                    st.success(f"📍 **{dst}**")
                    show_details_table(df_filtered[df_filtered['İlçe']==dst], target_date_col)
                else: show_details_table(df_filtered, target_date_col)
                
                st.divider()
                all_d = df[df['İl'].isin(selected_cities)]['İlçe'].unique()
                curr_d = df_filtered['İlçe'].unique()
                miss = sorted(list(set(all_d) - set(curr_d)))
                if miss:
                    st.markdown("#### ⚠️ Hiç Bayi Olmayan İlçeler")
                    cols = st.columns(4)
                    for i, d in enumerate(miss): cols[i%4].warning(f"📍 {d}")

    # 8. İL KARNESİ
    with tab_report:
        st.subheader("📄 Tek Tuşla İl Karnesi")
        st.markdown("Seçilen ilin tüm kritik verilerini tek sayfada özetler.")
        
        all_provinces = sorted(df['İl'].unique().tolist())
        default_province_idx = 0
        if selected_cities and selected_cities[0] in all_provinces:
            default_province_idx = all_provinces.index(selected_cities[0])
            
        report_city = st.selectbox("Karne Çıkarılacak İli Seçin:", all_provinces, index=default_province_idx)
        
        if report_city:
            city_df = df[df['İl'] == report_city]
            total_stations_city = len(city_df)
            
            competitors_city = city_df['Dağıtım Şirketi'].value_counts()
            market_leader = competitors_city.idxmax() if not competitors_city.empty else "Veri Yok"
            leader_count = competitors_city.max() if not competitors_city.empty else 0
            
            my_city_df = city_df[city_df['Dağıtım Şirketi'] == "GÜZEL ENERJİ AKARYAKIT ANONİM ŞİRKETİ"]
            my_city_count = len(my_city_df)
            
            st.markdown("---")
            st.markdown(f"<h1 style='text-align: center; color: #2980b9;'>{report_city} İLİ PAZAR KARNESİ</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center;'>Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y')}</p>", unsafe_allow_html=True)
            
            rk1, rk2, rk3 = st.columns(3)
            rk1.metric("Toplam İstasyon", total_stations_city)
            rk2.metric("Pazar Lideri", f"{leader_count} Bayi", help=market_leader)
            rk3.metric("Güzel Enerji", my_city_count)
            
            st.divider()
            
            st.subheader(f"📅 Güzel Enerji Sözleşme Bitiş Projeksiyonu ({report_city})")
            
            if not my_city_df.empty and 'Bitis_Yili' in my_city_df.columns:
                current_year = datetime.now().year
                future_expirations = my_city_df[my_city_df['Bitis_Yili'] >= current_year]['Bitis_Yili'].value_counts().sort_index()
                
                if not future_expirations.empty:
                    cols = st.columns(len(future_expirations))
                    for idx, (year, count) in enumerate(future_expirations.items()):
                        with cols[idx]:
                            st.markdown(f"""
                            <div class="year-box">
                                <div class="year-title">{int(year)}</div>
                                <div class="year-count">{count}</div>
                                <div style="font-size:0.8em; color:#666;">Sözleşme</div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    st.divider()
                    st.markdown("### 📋 Detaylı Bitiş Listesi")
                    st.dataframe(my_city_df[['Unvan', 'İlçe', 'Bitis_Ayi', 'Bitis_Yili', 'Kalan_Gun']].sort_values('Kalan_Gun'), use_container_width=True, hide_index=True)
                else:
                    st.success("Bu ilde yakın zamanda bitecek sözleşmeniz bulunmamaktadır.")
            else:
                st.warning("Bu ilde Güzel Enerji bayisi bulunmamaktadır.")

            st.divider()
            
            rc1, rc2 = st.columns(2)
            with rc1:
                st.subheader("Dağıtıcı Pazar Payı")
                if not competitors_city.empty:
                    top_comp = competitors_city.head(7).reset_index()
                    top_comp.columns = ['Şirket', 'Adet']
                    fig_rep_pie = px.pie(top_comp, values='Adet', names='Şirket', hole=0.4)
                    st.plotly_chart(fig_rep_pie, use_container_width=True)
            
            with rc2:
                st.subheader("İlçe Dağılımı")
                dist_dist = city_df['İlçe'].value_counts().reset_index()
                dist_dist.columns = ['İlçe', 'Adet']
                fig_rep_bar = px.bar(dist_dist.head(10), x='Adet', y='İlçe', orientation='h', text='Adet')
                st.plotly_chart(fig_rep_bar, use_container_width=True)

    # 9. CRM LITE
    with tab_crm:
        st.subheader("📝 CRM Lite")
        if not df_filtered.empty:
            bayiler = sorted(df_filtered['Unvan'].unique().tolist())
            cr1, cr2 = st.columns([1,2])
            with cr1:
                sel_b = st.selectbox("Bayi", bayiler)
                note = st.text_area("Not", height=100)
                if st.button("Kaydet", type="primary") and note:
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
                    if sel_b not in st.session_state.crm_notes: st.session_state.crm_notes[sel_b] = []
                    st.session_state.crm_notes[sel_b].append(f"[{ts}] {note}")
                    st.success("Kaydedildi!")
            with cr2:
                st.markdown("### 📋 Notlar")
                if st.session_state.crm_notes:
                    crm_list = [{"Bayi": b, "Not": n} for b, ns in st.session_state.crm_notes.items() for n in ns]
                    buffer = io.BytesIO()
                    try:
                        with pd.ExcelWriter(buffer, engine='xlsxwriter') as w: pd.DataFrame(crm_list).to_excel(w, index=False)
                        st.download_button("📥 Excel İndir", buffer.getvalue(), "CRM.xlsx", "application/vnd.ms-excel")
                    except: st.error("Excel oluşturulamadı.")
                    
                    for b, ns in st.session_state.crm_notes.items():
                        with st.expander(f"🏢 {b} ({len(ns)})"):
                            for n in ns: st.markdown(f"- {n}")
                else: st.info("Not yok.")

    # 10. HAM VERİ
    with tab_data:
        st.subheader("📋 Ham Veri")
        buf = io.BytesIO()
        try:
            with pd.ExcelWriter(buf, engine='xlsxwriter') as w: df_filtered.to_excel(w, index=False)
            st.download_button("📥 Tümünü İndir", buf.getvalue(), "Data.xlsx", "application/vnd.ms-excel")
        except: pass
        st.markdown(f"_Önizleme ({PREVIEW_ROW_LIMIT} satır)_")
        st.dataframe(df_filtered.head(PREVIEW_ROW_LIMIT), use_container_width=True)

if __name__ == "__main__":
    main()
