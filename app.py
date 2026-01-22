import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import numpy as np
import os
import io
import time

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
        
        # 1. Önce UTC (Evrensel) zamanı al
        utc_time = datetime.datetime.utcfromtimestamp(timestamp)
        
        # 2. Türkiye Saati için 3 saat ekle (GMT+3)
        turkey_time = utc_time + datetime.timedelta(hours=3)
        
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
    
    # 3. Dosyanın Son Değiştirilme Tarihini Al
    file_date_str = get_file_last_modified(SABIT_DOSYA_ADI)

    with st.sidebar:
        st.success(f"🔄 **VERİ GÜNCELLEME:**\n\n{file_date_str}")
        st.info("💡 **Öneri İçin..**\n\n📧 kerim.aksu@milangaz.com.tr")
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
