import pydeck as pdk
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import io
import time
import math
import networkx as nx
from datetime import datetime, timedelta, date

# --- 1. SAYFA VE GENEL AYARLAR ---
st.set_page_config(
    page_title="EPDK Akaryakıt Pazar Analizi",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- HAVERSINE (MESAFE HESAPLAMA) FONKSİYONU ---
def haversine(lat1, lon1, lat2, lon2):
    if any(x is None for x in [lat1, lon1, lat2, lon2]): return 99999
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# --- DOSYA TARİHİ HESAPLAMA ---
def get_file_last_modified(file_path):
    try:
        if not os.path.exists(file_path): return "DOSYA BULUNAMADI"
        timestamp = os.path.getmtime(file_path)
        utc_time = datetime.fromtimestamp(timestamp)
        turkey_time = utc_time + timedelta(hours=3)
        tr_months = {1: 'OCAK', 2: 'ŞUBAT', 3: 'MART', 4: 'NİSAN', 5: 'MAYIS', 6: 'HAZİRAN',
                     7: 'TEMMUZ', 8: 'AĞUSTOS', 9: 'EYLÜL', 10: 'EKİM', 11: 'KASIM', 12: 'ARALIK'}
        month_name = tr_months.get(turkey_time.month, "")
        return f"{turkey_time.day} {month_name} {turkey_time.year} SAAT {turkey_time.strftime('%H:%M')}"
    except: return "TARİH ALINAMADI"

# --- GİRİŞ ANİMASYONU ---
def show_intro_animation():
    if 'intro_played' not in st.session_state: st.session_state['intro_played'] = False
    if st.session_state['intro_played']: return
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("""
<div class='insight-box-danger'>
    <div style="font-size:1.1em; font-weight:bold; margin-bottom:10px;">
        ⚠️ Kritik Yenileme Dönemleri
    </div>
    <ul style="padding-left:20px; margin:0;">
        <li style="margin-bottom:8px;"><span style="color:#c0392b; font-weight:bold;">2027</span>: Toplam <b>435</b> Bayi</li>
        <li style="margin-bottom:8px;"><span style="color:#c0392b; font-weight:bold;">2028</span>: Toplam <b>461</b> Bayi</li>
        <li style="margin-bottom:8px;"><span style="color:#c0392b; font-weight:bold;">2029</span>: Toplam <b>455</b> Bayi</li>
        <li style="margin-bottom:8px;"><span style="color:#c0392b; font-weight:bold;">2030</span>: Toplam <b>762</b> Bayi</li>
    </ul>
</div>
""", unsafe_allow_html=True)
        time.sleep(1.5)
    placeholder.empty()
    st.session_state['intro_played'] = True

# --- AYARLAR VE CSS ---
MAX_ROW_DISPLAY = 1000
MAX_MAP_POINTS = 50000
PREVIEW_ROW_LIMIT = 100
SABIT_DOSYA_ADI = "asatis.xlsx"

st.markdown("""
<style>
    .stMetric { background-color: #f0f2f6; border-left: 5px solid #2980b9; padding: 15px; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .crm-box { background-color: #fff9c4; padding: 10px; border-radius: 5px; border: 1px solid #fbc02d; margin-bottom: 10px; }
    .warning-box { padding: 1rem; background-color: #ffeba0; border-left: 6px solid #ffa500; color: #5c3a00; border-radius: 4px; font-weight: bold; }
    .year-box { background-color: #e8f4f8; padding: 10px; border-radius: 5px; text-align: center; border: 1px solid #b3e5fc; margin-bottom: 5px; }
    .year-title { font-weight: bold; color: #0277bd; font-size: 1.1em; }
    .year-count { font-size: 1.5em; font-weight: bold; color: #01579b; }
    .insight-box-success { padding: 15px; border-radius: 8px; background-color: #d4edda; border-left: 5px solid #28a745; color: #155724; margin-bottom: 10px; }
    .insight-box-warning { padding: 15px; border-radius: 8px; background-color: #fff3cd; border-left: 5px solid #ffc107; color: #856404; margin-bottom: 10px; }
    .insight-box-danger { padding: 15px; border-radius: 8px; background-color: #f8d7da; border-left: 5px solid #dc3545; color: #721c24; margin-bottom: 10px; }
    .insight-box-info { padding: 15px; border-radius: 8px; background-color: #d1ecf1; border-left: 5px solid #17a2b8; color: #0c5460; margin-bottom: 10px; }
    .district-chip { display: inline-block; background-color: #f1f3f5; padding: 5px 10px; margin: 3px; border-radius: 15px; font-size: 0.9em; border: 1px solid #ddd; cursor: help; }
    .filter-container { background-color: #e3f2fd; padding: 15px; border-radius: 10px; border: 1px solid #bbdefb; margin-bottom: 15px; }
    
    /* --- SADE KIRMIZI YANIP SÖNME EFEKTİ --- */
    @keyframes blinker-red {
        50% { opacity: 0.5; color: #ff2b2b; }
    }
    
    /* YENİ SIRALAMAYA GÖRE KIRMIZI YANIP SÖNECEK SEKMELER [NEW Olanlar] */
    /* 1 tabanlı indeksleme: 7, 8, 9, 10, 11. sekmeler */
    
    button[data-testid="stTab"]:nth-child(7) p, /* Yarıçap */
    button[data-testid="stTab"]:nth-child(8) p, /* Rota */
    button[data-testid="stTab"]:nth-child(9) p, /* Robo */
    button[data-testid="stTab"]:nth-child(10) p, /* Vergi */
    button[data-testid="stTab"]:nth-child(11) p { /* Detaylı Arama */
        color: #ff2b2b !important;
        font-weight: 800 !important;
        animation: blinker-red 1.5s linear infinite;
    }

    /* Robo Kartları (Sade Tasarım) */
    .dealer-card, .robo-card {
        background: white;
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        font-family: sans-serif;
    }
    .dealer-header {
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
        margin-bottom: 15px;
    }
    .dealer-title { font-size: 1.5em; font-weight: bold; color: #2c3e50; }
    .dealer-badge { 
        background-color: #3498db; color: white; padding: 4px 8px; 
        border-radius: 4px; font-size: 0.8em; font-weight: bold; vertical-align: middle;
    }
    .dealer-row { display: flex; justify-content: space-between; margin-bottom: 8px; border-bottom: 1px dotted #eee; padding-bottom: 5px; }
    .dealer-label { font-weight: bold; color: #7f8c8d; min-width: 150px; }
    .dealer-value { color: #2c3e50; font-weight: 500; text-align: right; width: 100%; word-break: break-word; }
    
    .robo-header {
        font-size: 1.2em; font-weight: bold; margin-bottom: 10px; color: #2c3e50;
        border-bottom: 1px solid #eee; padding-bottom: 5px;
    }
    .robo-list { list-style-type: none; padding: 0; margin: 0; }
    .robo-list li { margin-bottom: 8px; font-size: 1em; padding-left: 10px; border-left: 3px solid #eee; }
    .robo-highlight { font-weight: bold; color: #d35400; }
</style>
""", unsafe_allow_html=True)

# --- KOORDİNAT VERİTABANI ---
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

# --- BÖLGE TANIMLARI ---
BOLGE_TANIMLARI = {
    "Orta Anadolu": [
        "DÜZCE", "KARABÜK", "KONYA", "BOLU", "AFYONKARAHİSAR",
        "AKSARAY", "ESKİŞEHİR", "ANKARA", "KIRIKKALE", "KASTAMONU",
        "ÇANKIRI", "YOZGAT", "KIRŞEHİR", "KAYSERİ", "NEVŞEHİR",
        "NİĞDE", "ZONGULDAK", "BARTIN"
    ]
}

if 'crm_notes' not in st.session_state: st.session_state.crm_notes = {}

# --- VERİ YÜKLEME ---
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path): return None, None, None
    try:
        df = pd.read_excel(file_path)
        df.columns = [str(c).strip() for c in df.columns]
        if 'Dağıtıcı' in df.columns: df.rename(columns={'Dağıtıcı': 'Dağıtım Şirketi'}, inplace=True)
        
        # ŞEHİR İSİMLERİNİ TEMİZLE
        if 'İl' in df.columns: 
            df['İl'] = df['İl'].astype(str).str.upper().str.strip().str.replace('i', 'İ').str.replace('ı', 'I')
        if 'İlçe' in df.columns: 
            df['İlçe'] = df['İlçe'].astype(str).str.upper().str.strip().str.replace('i', 'İ').str.replace('ı', 'I')

        date_cols = [
            'Lisans Bitiş Tarihi', 
            'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi', 
            'Lisans Başlangıç Tarihi',
            'Dağıtıcı ile Yapılan Sözleşme Başlangıç Tarihi'
        ]
        
        for col in date_cols:
            if col in df.columns: df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

        target_col = 'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi' if 'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi' in df.columns else 'Lisans Bitiş Tarihi'
        start_col = 'Dağıtıcı ile Yapılan Sözleşme Başlangıç Tarihi'
        today = pd.to_datetime(date.today())
        
        if target_col in df.columns:
            df['Kalan_Gun'] = (df[target_col] - today).dt.days
            df['Bitis_Yili'] = df[target_col].dt.year
            df['Bitis_Ayi_No'] = df[target_col].dt.month
            
            month_map = {1:'Ocak', 2:'Şubat', 3:'Mart', 4:'Nisan', 5:'Mayıs', 6:'Haziran', 
                         7:'Temmuz', 8:'Ağustos', 9:'Eylül', 10:'Ekim', 11:'Kasım', 12:'Aralık'}
            df['Bitis_Ayi'] = df['Bitis_Ayi_No'].map(month_map)
        else: df['Kalan_Gun'] = np.nan

        if start_col in df.columns and target_col in df.columns:
            df['Sozlesme_Suresi_Gun'] = (df[target_col] - df[start_col]).dt.days
        else: df['Sozlesme_Suresi_Gun'] = np.nan

        df['Risk_Durumu'] = df['Kalan_Gun'].apply(lambda x: "KRİTİK" if x < 90 else "GÜVENLİ")
        
        return df, target_col, start_col
    except Exception as e: return None, str(e), None

def show_details_table(dataframe, target_date_col, extra_cols=None):
    if dataframe is None or dataframe.empty:
        st.info("Seçilen kriterlere uygun kayıt bulunamadı.")
        return
    
    if len(dataframe) > MAX_ROW_DISPLAY:
        st.markdown(f"<div class='warning-box'>⚠️ <b>Performans:</b> İlk <b>{MAX_ROW_DISPLAY:,}</b> kayıt gösteriliyor.</div>", unsafe_allow_html=True)
        display_df = dataframe.head(MAX_ROW_DISPLAY).copy()
    else:
        display_df = dataframe.copy()

    cols = ['Unvan', 'İl', 'İlçe', 'Dağıtım Şirketi', target_date_col, 'Kalan_Gun', 'Sozlesme_Suresi_Gun', 'Risk_Durumu']
    if extra_cols: cols.extend(extra_cols)
    final_cols = [c for c in cols if c in display_df.columns]
    display_df = display_df[final_cols]

    for col in display_df.columns:
        if "Tarihi" in col or "Tarih" in col:
            try: display_df[col] = pd.to_datetime(display_df[col]).dt.strftime('%d.%m.%Y')
            except: pass

    if 'Kalan_Gun' in display_df.columns: display_df = display_df.sort_values('Kalan_Gun')
    
    def highlight_risk(val):
        if not isinstance(val, (int, float)): return ''
        if val < 0: return 'background-color: #ffcccc'
        elif val < 90: return 'background-color: #ffe5cc'
        elif val < 180: return 'background-color: #ffffcc'
        return ''
    
    st.markdown(f"**📋 Listelenen Bayi:** {len(display_df)}")
    
    buffer = io.BytesIO()
    try:
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            dataframe.to_excel(writer, index=False, sheet_name='Bayi Listesi')
        st.download_button("📥 Excel İndir", buffer.getvalue(), "Bayi_Listesi.xlsx", "application/vnd.ms-excel")
    except: pass

    if 'Kalan_Gun' in display_df.columns:
        st.dataframe(display_df.style.map(highlight_risk, subset=['Kalan_Gun']), use_container_width=True, hide_index=True)
    else:
        st.dataframe(display_df, use_container_width=True, hide_index=True)

# ==========================================
# 🛠️ BAĞIMSIZ FİLTRE FONKSİYONU
# ==========================================
def create_tab_filters(df, key_prefix):
    st.markdown(f"#### 🔍 Filtre Paneli")
    st.markdown(f"<div class='filter-container'>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        region_opts = ["Tümü"] + list(BOLGE_TANIMLARI.keys())
        sel_reg = st.selectbox("🌍 Bölge", region_opts, key=f"{key_prefix}_reg")
    
    filtered = df.copy()
    if sel_reg != "Tümü": filtered = filtered[filtered['İl'].isin(BOLGE_TANIMLARI[sel_reg])]
        
    with c2:
        city_opts = sorted(filtered['İl'].unique().tolist())
        sel_city = st.multiselect("🏢 İl", city_opts, key=f"{key_prefix}_city")

    if sel_city: filtered = filtered[filtered['İl'].isin(sel_city)]
        
    with c3:
        dist_opts = sorted(filtered['İlçe'].unique().tolist()) if 'İlçe' in filtered.columns else []
        sel_dist = st.multiselect("📍 İlçe", dist_opts, key=f"{key_prefix}_dist")

    if sel_dist: filtered = filtered[filtered['İlçe'].isin(sel_dist)]
        
    with c4:
        comp_opts = sorted(filtered['Dağıtım Şirketi'].dropna().astype(str).unique().tolist())
        sel_comp = st.multiselect("⛽ Şirket", comp_opts, key=f"{key_prefix}_comp")
        
    if sel_comp: filtered = filtered[filtered['Dağıtım Şirketi'].isin(sel_comp)]
    
    st.markdown("</div>", unsafe_allow_html=True)
    return filtered

# --- ANA UYGULAMA ---
def main():
    show_intro_animation()
    data_result = load_data(SABIT_DOSYA_ADI)
    if data_result is None or data_result[0] is None:
        st.error(f"⚠️ Hata: {data_result[1] if data_result else 'Veri Yüklenemedi'}")
        st.stop()
    df, target_date_col, start_date_col = data_result
    
    # ----------------------------------------------------
    # 🛠️ KOORDİNAT SİMÜLASYONU (JITTER)
    # ----------------------------------------------------
    if 'Enlem' not in df.columns or 'Boylam' not in df.columns:
        np.random.seed(42)
        df['base_lat'] = df['İl'].map(lambda x: CITY_COORDINATES.get(x, [39.0, 35.0])[0])
        df['base_lon'] = df['İl'].map(lambda x: CITY_COORDINATES.get(x, [39.0, 35.0])[1])
        df['Enlem_Sim'] = df['base_lat'] + np.random.uniform(-0.05, 0.05, size=len(df))
        df['Boylam_Sim'] = df['base_lon'] + np.random.uniform(-0.05, 0.05, size=len(df))
        lat_col, lon_col = 'Enlem_Sim', 'Boylam_Sim'
    else:
        lat_col, lon_col = 'Enlem', 'Boylam'

    file_date_str = get_file_last_modified(SABIT_DOSYA_ADI)

    # --- ÜST BİLGİ PANELİ ---
    st.markdown("### 🚀 Akaryakıt Pazar & Risk Analizi")
    col_info1, col_info2, col_info3 = st.columns([1, 1, 1])
    
    with col_info1:
        st.success(f"🔄 **Veri Güncelleme:**\n\n{file_date_str}")
    with col_info2:
        st.info(f"📧 **İletişim:**\n\nkerim.aksu@milangaz.com.tr")
    with col_info3:
        st.warning("🔗 **Diğer Uygulamalar**")
        st.markdown("""
        <div style="font-size:0.9em;">
        • 📊 <a href="https://pazarpayi.streamlit.app/" target="_blank">EPDK LPG AYLIK SEKTÖR RAPORU ( AÇIK KAYNAK SATIŞ )</a><br>
        • 📰 <a href="https://newslpg.streamlit.app/" target="_blank">Haber Aracı</a><br>
        • 📱 <a href="https://lpg2026.streamlit.app/" target="_blank">Mobil Hesaplayıcı</a>
        </div>
        """, unsafe_allow_html=True)
    st.divider()

    # --- KPI ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Veri Tabanı", f"{len(df):,}")
    c2.metric("Aktif Şirket", df['Dağıtım Şirketi'].nunique())
    acil_durum = len(df[df['Kalan_Gun'] < 90]) if 'Kalan_Gun' in df.columns else 0
    c3.metric("Kritik Durum (Toplam)", acil_durum, delta="Acil Yenileme", delta_color="inverse")
    st.divider()

    # --- SEKMELER (GÖRSELE GÖRE YENİDEN SIRALANDI) ---
    tabs = st.tabs([
        "📊 Bölgesel & Durum",
        "📅 Takvim",
        "⚡ Hızlı Analiz",
        "⚔️ Karşılaştırma",
        "📄 İl Karnesi",
        "📍 İlçe Penetrasyonu",
        "📍 Yarıçap (Radar) [NEW]",
        "🚗 Rota Planlayıcı [NEW]",
        "🤖 Robo-Yönetici [NEW]",
        "💸 Vergi Zincir Analizi [NEW]",
        "🔍 Detaylı Arama [NEW]",
        "🔮 Simülasyon",
        "📡 Sözleşme Radar"
    ])

    # 1. BÖLGESEL & DURUM
    with tabs[0]:
        st.subheader("🗺️ Bölgesel Yoğunluk Haritası")
        st.info("💡 **İPUCU:** Haritayı büyütmek veya yakınlaştırmak için sağ üstteki araçları kullanabilirsiniz.")
        df_tab1 = create_tab_filters(df, "tab1")
        
        if len(df_tab1) > MAX_MAP_POINTS:
            st.warning("⚠️ Haritada çok fazla nokta var, lütfen filtreleyin.")
        elif not df_tab1.empty:
            map_data = df_tab1['İl'].value_counts().reset_index()
            map_data.columns = ['İl', 'Adet']
            map_data['lat'] = map_data['İl'].map(lambda x: CITY_COORDINATES.get(x, [None, None])[0])
            map_data['lon'] = map_data['İl'].map(lambda x: CITY_COORDINATES.get(x, [None, None])[1])
            map_data = map_data.dropna()

            if not map_data.empty:
                fig_map = px.scatter_mapbox(
                    map_data, lat="lat", lon="lon", size="Adet", color="Adet",
                    hover_name="İl", size_max=35, zoom=5, 
                    mapbox_style="open-street-map", color_continuous_scale=px.colors.sequential.Bluered
                )
                fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                st.plotly_chart(fig_map, use_container_width=True)

        st.divider()
        col_pie1, col_pie2 = st.columns(2)
        with col_pie1:
            st.metric("Seçili Bayi Sayısı", len(df_tab1))
            city_pie = df_tab1['İl'].value_counts().reset_index()
            city_pie.columns = ['İl', 'Adet']
            fig_cp = px.pie(city_pie, values='Adet', names='İl', hole=0.4, title="Şehir Dağılımı")
            st.plotly_chart(fig_cp, use_container_width=True)
        with col_pie2:
            dist_pie = df_tab1['Dağıtım Şirketi'].value_counts().reset_index()
            dist_pie.columns = ['Dağıtım Şirketi', 'Adet']
            fig_dp = px.pie(dist_pie, values='Adet', names='Dağıtım Şirketi', hole=0.4, title="Pazar Payı")
            st.plotly_chart(fig_dp, use_container_width=True)
        
        show_details_table(df_tab1, target_date_col)

    # 2. TAKVİM
    with tabs[1]:
        st.subheader("📅 Takvim")
        st.caption("👇 **Grafikteki sütunlara tıklayarak aşağıdaki tabloyu filtreleyebilirsiniz.**")
        
        df_cal = create_tab_filters(df, "tab5")
        if 'Bitis_Yili' in df_cal.columns:
            yrs = sorted(df_cal['Bitis_Yili'].dropna().astype(int).unique())
            sel_yr = st.selectbox("Yıl", yrs)
            df_yr = df_cal[df_cal['Bitis_Yili'] == sel_yr]
            
            if not df_yr.empty:
                mon_counts = df_yr.groupby(['Bitis_Ayi_No', 'Bitis_Ayi']).size().reset_index(name='Adet')
                mon_counts = mon_counts.sort_values('Bitis_Ayi_No')
                
                fig_cal = px.bar(mon_counts, x='Bitis_Ayi', y='Adet', text='Adet', title=f"{sel_yr} Yılı Sözleşme Bitiş Dağılımı")
                fig_cal.update_layout(xaxis_title="Ay", yaxis_title="Sözleşme Sayısı")
                
                selection = st.plotly_chart(fig_cal, use_container_width=True, on_select="rerun")
                
                selected_month = None
                if selection and selection['selection']['points']:
                    selected_month = selection['selection']['points'][0]['x']
                    st.info(f"🔍 **Seçilen Ay:** {selected_month}")
                    filtered_table = df_yr[df_yr['Bitis_Ayi'] == selected_month]
                else:
                    st.info("Tüm yıl gösteriliyor. Detay için grafiğe tıklayın.")
                    filtered_table = df_yr
                
                show_details_table(filtered_table, target_date_col)

    # 3. HIZLI ANALİZ
    with tabs[2]:
        st.subheader("⚡ Hızlı Analiz")
        df_tab2 = create_tab_filters(df, "tab2")
        
        if not df_tab2.empty:
            top_city = df_tab2['İl'].value_counts().idxmax()
            st.success(f"🏆 Bu filtredeki lider bölge: **{top_city}**")
            
            if 'Bitis_Yili' in df_tab2.columns:
                current_year = datetime.now().year
                future_expirations = df_tab2[df_tab2['Bitis_Yili'] >= current_year]['Bitis_Yili'].value_counts().sort_index()
                
                if not future_expirations.empty:
                    st.markdown("##### 📅 Filtre Kapsamındaki Sözleşme Bitiş Takvimi")
                    msg_list = "<ul>"
                    total_future = 0
                    for year, count in future_expirations.items():
                        yr_text = f"{int(year)} (Bu Yıl)" if year == current_year else f"{int(year)}"
                        msg_list += f"<li><b>{yr_text}:</b> {count} adet sözleşme bitiyor.</li>"
                        total_future += count
                    msg_list += "</ul>"
                    
                    st.markdown(f"""
                    <div class='insight-box-danger'>
                        <div style="font-size:1.1em; font-weight:bold; margin-bottom:5px;">⚠️ Kritik Dönemler</div>
                        Seçilen filtrede toplam <b>{total_future}</b> sözleşme sona erecek.
                        {msg_list}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("Bu filtrede yakın zamanda biten sözleşme bulunmuyor.")

            st.metric("Bu Filtredeki Toplam Bayi", len(df_tab2))
            comp_dist = df_tab2['Dağıtım Şirketi'].value_counts().reset_index()
            comp_dist.columns = ['Şirket', 'Adet']
            fig_my_share = px.pie(comp_dist, names='Şirket', values='Adet', hole=0.5, title="Filtre İçi Pazar Payı")
            st.plotly_chart(fig_my_share, use_container_width=True)
        else:
            st.warning("Veri yok.")

    # 4. KARŞILAŞTIRMA
    with tabs[3]:
        st.subheader("⚔️ Rakip Karşılaştırma")
        df_tab3 = create_tab_filters(df, "tab3")
        
        comps = sorted(df['Dağıtım Şirketi'].unique())
        c1, c2 = st.columns(2)
        comp_a = c1.selectbox("Şirket A", comps, index=0, key="ca")
        comp_b = c2.selectbox("Şirket B", comps, index=1 if len(comps)>1 else 0, key="cb")
        
        df_a = df_tab3[df_tab3['Dağıtım Şirketi'] == comp_a]
        df_b = df_tab3[df_tab3['Dağıtım Şirketi'] == comp_b]
        
        k1, k2 = st.columns(2)
        k1.metric(f"{comp_a}", len(df_a))
        k2.metric(f"{comp_b}", len(df_b), delta=len(df_b)-len(df_a))
        
        df_vs = df_tab3[df_tab3['Dağıtım Şirketi'].isin([comp_a, comp_b])]
        if not df_vs.empty:
            fig_vs = px.bar(df_vs.groupby(['İl','Dağıtım Şirketi']).size().reset_index(name='Adet'), 
                            x='İl', y='Adet', color='Dağıtım Şirketi', barmode='group')
            st.plotly_chart(fig_vs, use_container_width=True)

    # 5. İL KARNESİ
    with tabs[4]:
        st.subheader("📄 İl Karnesi (360° Analiz)")
        
        all_provinces = sorted(df['İl'].unique().tolist())
        report_city = st.selectbox("Analiz Edilecek İli Seçin:", all_provinces, key="report_city_sel")
        
        if report_city:
            city_df = df[df['İl'] == report_city]
            total_stations = len(city_df)
            comp_counts = city_df['Dağıtım Şirketi'].value_counts()
            market_leader = comp_counts.idxmax()
            leader_count = comp_counts.max()
            
            st.markdown("---")
            target_company = st.selectbox("Odaklanılacak Şirket:", sorted(city_df['Dağıtım Şirketi'].unique()), index=0, key="report_comp_sel")
            my_company_df = city_df[city_df['Dağıtım Şirketi'] == target_company]
            my_count = len(my_company_df)
            my_share = (my_count / total_stations) * 100
            
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("🏙️ Toplam Pazar", total_stations)
            k2.metric("👑 Pazar Lideri", f"{market_leader}", f"{leader_count} Bayi")
            k3.metric(f"⛽ {target_company}", my_count)
            k4.metric("📊 Pazar Payı", f"%{my_share:.1f}")
            
            st.markdown("---")
            g1, g2 = st.columns(2)
            with g1:
                st.markdown("##### 🍰 Pazar Payı Dağılımı")
                if len(comp_counts) > 10:
                    top10 = comp_counts.head(10)
                    others = pd.Series([comp_counts.iloc[10:].sum()], index=['DİĞER'])
                    final_counts = pd.concat([top10, others])
                else: final_counts = comp_counts
                fig_pie = px.pie(values=final_counts.values, names=final_counts.index, hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
            with g2:
                st.markdown(f"##### 📍 {target_company} İlçe Dağılımı")
                if not my_company_df.empty:
                    dist_counts = my_company_df['İlçe'].value_counts().reset_index()
                    dist_counts.columns = ['İlçe', 'Adet']
                    fig_bar = px.bar(dist_counts, x='Adet', y='İlçe', orientation='h', text='Adet')
                    st.plotly_chart(fig_bar, use_container_width=True)
                else: st.warning("Bu şirketin bu ilde bayisi yok.")

            st.markdown("---")
            c_exp, c_list = st.columns([1, 2])
            with c_exp:
                st.markdown("##### ⏳ Sözleşme Bitiş Takvimi")
                if 'Bitis_Yili' in my_company_df.columns and not my_company_df.empty:
                    exp_counts = my_company_df['Bitis_Yili'].value_counts().sort_index()
                    st.bar_chart(exp_counts)
                else: st.info("Veri yok.")
            with c_list:
                st.markdown("##### 📋 Bayi Listesi")
                if not my_company_df.empty:
                    cols_rep = ['Unvan', 'İlçe', 'Dağıtım Şirketi', 'Bitis_Yili', 'Kalan_Gun', target_date_col]
                    cols_use_rep = [c for c in cols_rep if c in my_company_df.columns]
                    display_df = my_company_df[cols_use_rep].sort_values('Kalan_Gun')
                    
                    if target_date_col in display_df.columns:
                        try: display_df[target_date_col] = pd.to_datetime(display_df[target_date_col]).dt.strftime('%d.%m.%Y')
                        except: pass
                        
                    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # 6. İLÇE PENETRASYONU
    with tabs[5]:
        st.subheader("📍 İlçe Analizi")
        df_dist = create_tab_filters(df, "tab7")
        if not df_dist.empty:
            cnt = df_dist['İlçe'].value_counts().reset_index()
            cnt.columns = ['İlçe', 'Adet']
            
            fig_bar = px.bar(cnt.head(20), x='Adet', y='İlçe', orientation='h', text='Adet')
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            
            st.caption("👇 **İlçelere tıklayarak aşağıda o ilçenin detaylı listesini görebilirsiniz.**")
            selection = st.plotly_chart(fig_bar, use_container_width=True, on_select="rerun")
            
            selected_district = None
            if selection and selection['selection']['points']:
                selected_district = selection['selection']['points'][0]['y']
                st.info(f"📍 **Seçilen İlçe:** {selected_district}")
                filtered_table = df_dist[df_dist['İlçe'] == selected_district]
            else:
                st.info("Tüm ilçeler gösteriliyor.")
                filtered_table = df_dist
                
            display_cols = ['Unvan', 'Dağıtım Şirketi', target_date_col, 'Kalan_Gun']
            available_cols = [c for c in display_cols if c in filtered_table.columns]
            table_to_show = filtered_table[available_cols].copy()
            if target_date_col in table_to_show.columns:
                try: table_to_show[target_date_col] = pd.to_datetime(table_to_show[target_date_col]).dt.strftime('%d.%m.%Y')
                except: pass
            st.dataframe(table_to_show, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("##### 🚀 Fırsat Analizi: Boş Noktalar")
            selected_cities = df_dist['İl'].unique()
            all_possible_districts = df[df['İl'].isin(selected_cities)]['İlçe'].unique()
            current_districts = df_dist['İlçe'].unique()
            missing = sorted(list(set(all_possible_districts) - set(current_districts)))
            
            if missing:
                 st.warning(f"⚠️ Şu anki filtrede varlık göstermediğiniz **{len(missing)}** ilçe tespit edildi.")
                 with st.expander("📄 Boş İlçe Listesini Göster"):
                     chips = ""
                     market_size_ref = df[df['İl'].isin(selected_cities)]['İlçe'].value_counts()
                     for m in missing:
                         size = market_size_ref.get(m, 0)
                         chips += f"<span class='district-chip' title='Toplam Pazar: {size}'>{m} ({size})</span> "
                     st.markdown(chips, unsafe_allow_html=True)
            else:
                st.success("Tebrikler! Seçili bölgedeki tüm ilçelerde varlık gösteriyorsunuz.")

    # 7. YARIÇAP ANALİZİ [NEW]
    with tabs[6]:
        st.subheader("📍 Yarıçap (Radar) Analizi")
        st.info("💡 **İPUCU:** Haritayı büyütmek veya yakınlaştırmak için sağ üstteki araçları kullanabilirsiniz.")
        
        df_radar = create_tab_filters(df, "tab_radar_new")
        
        if not df_radar.empty:
            station_list = sorted(df_radar['Unvan'].unique())
            center_station_name = st.selectbox("Merkez Bayi Seçin:", station_list)
            radius_km = st.slider("Tarama Yarıçapı (km)", 1, 50, 10)
            
            center_row = df_radar[df_radar['Unvan'] == center_station_name].iloc[0]
            pool = df[df['İl'] == center_row['İl']].copy()
            
            pool['Mesafe'] = pool.apply(lambda r: haversine(center_row[lat_col], center_row[lon_col], r[lat_col], r[lon_col]), axis=1)
            nearby_stations = pool[pool['Mesafe'] <= radius_km].sort_values('Mesafe')
            
            st.success(f"🎯 **{center_station_name}** merkezli **{radius_km} km** içinde **{len(nearby_stations)}** istasyon bulundu.")
            
            if not nearby_stations.empty:
                nearby_stations['Renk'] = np.where(nearby_stations['Unvan'] == center_station_name, 'MERKEZ', 'RAKİP')
                nearby_stations['Nokta_Buyukluk'] = np.where(nearby_stations['Unvan'] == center_station_name, 25, 10)
                
                fig_rad = px.scatter_mapbox(
                    nearby_stations, lat=lat_col, lon=lon_col, color='Renk', size='Nokta_Buyukluk', 
                    hover_name='Unvan', hover_data=['Dağıtım Şirketi', 'İlçe', 'Mesafe', 'Kalan_Gun'],
                    color_discrete_map={'MERKEZ': 'red', 'RAKİP': 'blue'},
                    zoom=10, mapbox_style="open-street-map"
                )
                st.plotly_chart(fig_rad, use_container_width=True)
                
                display_cols = ['Unvan', 'İlçe', 'Dağıtım Şirketi', target_date_col, 'Kalan_Gun', 'Mesafe']
                cols_to_use = [c for c in display_cols if c in nearby_stations.columns]
                
                table_df = nearby_stations[cols_to_use].copy()
                if target_date_col in table_df.columns:
                    try: table_df[target_date_col] = pd.to_datetime(table_df[target_date_col]).dt.strftime('%d.%m.%Y')
                    except: pass
                
                st.dataframe(table_df, use_container_width=True, hide_index=True)
        else:
            st.warning("Veri yok.")

    # 8. ROTA PLANLAYICI [NEW]
    with tabs[7]:
        st.subheader("🚗 Akıllı Rota Planlayıcı")
        st.info("💡 **İPUCU:** Haritayı büyütmek veya yakınlaştırmak için sağ üstteki araçları kullanabilirsiniz.")
        
        df_route = create_tab_filters(df, "tab_route_new")

        if not df_route.empty:
            stations_to_visit = st.multiselect("Ziyaret Listesi Oluştur:", df_route['Unvan'].unique())
            
            if len(stations_to_visit) > 1:
                visit_df = df_route[df_route['Unvan'].isin(stations_to_visit)].copy()
                ordered_route = []
                remaining = visit_df.copy()
                current_node = remaining.iloc[0]
                ordered_route.append(current_node)
                remaining = remaining.drop(current_node.name)
                
                while len(remaining) > 0:
                    remaining['dist'] = remaining.apply(lambda row: haversine(current_node[lat_col], current_node[lon_col], row[lat_col], row[lon_col]), axis=1)
                    nearest = remaining.loc[remaining['dist'].idxmin()]
                    ordered_route.append(nearest)
                    current_node = nearest
                    remaining = remaining.drop(nearest.name)
                
                route_df = pd.DataFrame(ordered_route)
                route_df['Sıra No'] = range(1, len(route_df) + 1)
                
                st.success("✅ En verimli rota oluşturuldu!")
                
                fig_rt = px.line_mapbox(
                    route_df, lat=lat_col, lon=lon_col, hover_name='Unvan', zoom=9, mapbox_style="open-street-map"
                )
                fig_rt.add_trace(go.Scattermapbox(
                    lat=route_df[lat_col], lon=route_df[lon_col], mode='markers+text',
                    marker=go.scattermapbox.Marker(size=14, color='green'),
                    text=route_df['Sıra No'], textposition="top center", hoverinfo='text', hovertext=route_df['Unvan']
                ))
                st.plotly_chart(fig_rt, use_container_width=True)
                st.dataframe(route_df[['Sıra No', 'Unvan', 'İlçe', 'Dağıtım Şirketi']], use_container_width=True)
            else:
                st.info("En az 2 bayi seçin.")
        else:
             st.warning("Veri yok.")

    # 9. ROBO-YÖNETİCİ [NEW]
    with tabs[8]:
        st.subheader("🤖 Robo-Yönetici: Stratejik İstihbarat Raporu (40+ Nokta)")
        st.info("💡 Bu rapor, seçili filtredeki pazar durumunu **GÜZEL ENERJİ AKARYAKIT A.Ş.** perspektifinden, İl ve İlçe kalelerini ayrıştırarak analiz eder.")
        
        df_robo = create_tab_filters(df, "tab_robo")
        
        # TAM KONUM (İL - İLÇE) OLUŞTURMA
        if 'İlçe' in df_robo.columns:
            df_robo['Tam_Konum'] = df_robo['İl'] + " - " + df_robo['İlçe']
        else:
            df_robo['Tam_Konum'] = df_robo['İl']

        HERO_COMPANY = "GÜZEL ENERJİ AKARYAKIT ANONİM ŞİRKETİ"
        
        if not df_robo.empty:
            # --- HESAPLAMA MOTORU ---
            total_stations = len(df_robo)
            
            # Rekabet
            brand_counts = df_robo['Dağıtım Şirketi'].value_counts()
            leader_brand = brand_counts.idxmax()
            leader_count = brand_counts.max()
            
            # Hero Durumu
            hero_count = brand_counts.get(HERO_COMPANY, 0)
            hero_rank = list(brand_counts.index).index(HERO_COMPANY) + 1 if HERO_COMPANY in brand_counts.index else -1
            hero_share = (hero_count / total_stations) * 100
            
            # Farklar
            gap_to_leader = leader_count - hero_count
            
            # En yakın takipçi
            followers = brand_counts[brand_counts < hero_count]
            nearest_follower = followers.index[0] if not followers.empty else "Yok"
            follower_gap = hero_count - followers.iloc[0] if not followers.empty else 0

            # Sözleşme Yılları (TÜM YILLAR - PAZAR vs HERO)
            current_year = datetime.now().year
            future_years_market = {}
            future_years_hero = {}
            if 'Bitis_Yili' in df_robo.columns:
                future_df = df_robo[df_robo['Bitis_Yili'] >= current_year]
                future_years_market = future_df['Bitis_Yili'].value_counts().sort_index().to_dict()
                
                hero_future_df = future_df[future_df['Dağıtım Şirketi'] == HERO_COMPANY]
                future_years_hero = hero_future_df['Bitis_Yili'].value_counts().sort_index().to_dict()

            # İLÇE HAKİMİYETİ (TAM KONUM KULLANARAK)
            hero_df = df_robo[df_robo['Dağıtım Şirketi'] == HERO_COMPANY]
            
            # 1. İL KALESİ (ŞEHİR)
            hero_city_counts = hero_df['İl'].value_counts()
            if not hero_city_counts.empty:
                top_hero_city = hero_city_counts.idxmax()
                top_hero_city_cnt = hero_city_counts.max()
                # O ildeki toplam istasyon (Pay hesaplamak için)
                total_in_top_city = len(df_robo[df_robo['İl'] == top_hero_city])
                share_in_top_city = (top_hero_city_cnt / total_in_top_city) * 100
            else:
                top_hero_city = "Yok"
                top_hero_city_cnt = 0
                share_in_top_city = 0

            # 2. İLÇE KALESİ (MAHALLE)
            hero_dist_counts = hero_df['Tam_Konum'].value_counts()
            if not hero_dist_counts.empty:
                top_hero_dist = hero_dist_counts.idxmax()
                top_hero_dist_cnt = hero_dist_counts.max()
                total_in_top_dist = len(df_robo[df_robo['Tam_Konum'] == top_hero_dist])
                share_in_top_dist = (top_hero_dist_cnt / total_in_top_dist) * 100
            else:
                top_hero_dist = "Yok"
                top_hero_dist_cnt = 0
                share_in_top_dist = 0

            # Market Genel Kaleleri
            market_top_districts = df_robo['Tam_Konum'].value_counts().head(5)
            market_top_city = df_robo['İl'].value_counts().idxmax()

            # Rakipler nerde güçlü?
            competitor_strongholds = df_robo[df_robo['Dağıtım Şirketi'] != HERO_COMPANY]['Tam_Konum'].value_counts().head(3).index.tolist()

            # RAPOR OLUŞTURMA
            c1, c2 = st.columns(2)
            
            # --- 1. GÜZEL ENERJİ ÖZEL DURUM ---
            with c1:
                st.markdown(f"#### 🦁 1. Bizim Durumumuz ({HERO_COMPANY})")
                if hero_count > 0:
                    status_emoji = "🥇" if hero_rank == 1 else "🥈" if hero_rank == 2 else "🥉" if hero_rank == 3 else "📊"
                    st.markdown(f"""
                    <div class="robo-card">
                    <ul class="robo-list">
                    <li><b>Sıralama:</b> Şu anki filtrede pazarın <span class="robo-highlight">{hero_rank}. oyuncusuyuz</span> {status_emoji}.</li>
                    <li><b>Toplam İstasyon:</b> Portföyümüzde <span class="robo-highlight">{hero_count}</span> aktif istasyon var.</li>
                    <li><b>Pazar Payı:</b> Toplam pastanın <span class="robo-highlight">%{hero_share:.1f}</span>'ine sahibiz.</li>
                    <li><b>Liderle Fark:</b> Lider <b>{leader_brand}</b> ile aramızda <b>{gap_to_leader}</b> istasyon makası var.</li>
                    <li><b>Takipçi Riski:</b> Ensemizdeki <b>{nearest_follower}</b> ile fark sadece <b>{follower_gap}</b> istasyon.</li>
                    <li><b>🏰 İL KALESİ:</b> En güçlü olduğumuz şehir <span class="robo-highlight">{top_hero_city}</span>. Orada <b>{top_hero_city_cnt}</b> istasyonla pazarın <b>%{share_in_top_city:.1f}</b>'ine hakimiz.</li>
                    <li><b>🏘️ İLÇE KALESİ:</b> En yoğunlaştığımız nokta <span class="robo-highlight">{top_hero_dist}</span>. Sadece bu ilçede <b>{top_hero_dist_cnt}</b> istasyonumuz var (Pay: %{share_in_top_dist:.1f}).</li>
                    <li><b>Ortalama Ömür:</b> İstasyonlarımızın ortalama sözleşme süresi <b>{int(hero_df['Kalan_Gun'].mean()) if 'Kalan_Gun' in hero_df.columns and not hero_df.empty else 0}</b> gün.</li>
                    <li><b>Coğrafi Yayılım:</b> Seçili bölgedeki <b>{df_robo['İl'].nunique()}</b> ilin <b>{hero_df['İl'].nunique()}</b> tanesinde bayrağımız dalgalanıyor.</li>
                    <li><b>Operasyonel Odak:</b> Tüm istasyonlarımızın %{int(hero_city_counts.head(1).sum()/hero_count*100) if hero_count>0 else 0}'i tek bir ilde ({top_hero_city}) toplanmış.</li>
                    <li><b>Şehir İçi Güç:</b> "MERKEZ" ilçelerinde toplam <b>{len(hero_df[hero_df['Tam_Konum'].str.contains('MERKEZ')])}</b> istasyonumuz var.</li>
                    </ul>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ **Kritik:** Bu filtrede GÜZEL ENERJİ'ye ait hiç istasyon yok!")

            # --- 2. RAKİP VE PAZAR DERİNLİĞİ ---
            with c2:
                st.markdown("#### ⚔️ 2. Rakip & Pazar Derinlik Analizi")
                st.markdown(f"""
                <div class="robo-card">
                <ul class="robo-list">
                <li><b>Pazar Hacmi:</b> Toplam <span class="robo-highlight">{total_stations}</span> istasyonluk bir arenadayız.</li>
                <li><b>Oyuncu Sayısı:</b> Bu alanda <span class="robo-highlight">{len(brand_counts)}</span> farklı marka rekabet ediyor.</li>
                <li><b>Liderin Gücü:</b> Lider marka pazarın <b>%{(leader_count/total_stations*100):.1f}</b>'ine hükmediyor.</li>
                <li><b>Pazarın Kalbi (İlçe):</b> En yoğun rekabet <b>{market_top_districts.index[0]}</b> bölgesinde dönüyor ({market_top_districts.iloc[0]} istasyon).</li>
                <li><b>Pazarın Kalbi (İl):</b> En büyük hacim <b>{market_top_city}</b> ilinde.</li>
                <li><b>Rakip Kalesi:</b> Rakiplerin en yoğun olduğu bölge <b>{competitor_strongholds[0] if competitor_strongholds else 'Yok'}</b>.</li>
                <li><b>Konsolidasyon:</b> İlk 3 büyük marka pazarın <b>%{int(brand_counts.head(3).sum()/total_stations*100)}</b>'ini domine ediyor.</li>
                <li><b>Küçük Oyuncular:</b> Pazarın %{int(brand_counts[brand_counts < 10].sum()/total_stations*100)}'lik kısmı yerel oyuncularda.</li>
                <li><b>Büyüme Alanı:</b> Henüz doymamış, rekabetin düşük olduğu <b>{len(df_robo['Tam_Konum'].unique()) - len(market_top_districts)}</b> farklı nokta var.</li>
                <li><b>Liderin Zayıf Karnı:</b> Lider markanın hiç olmadığı <b>{len(df_robo[df_robo['Dağıtım Şirketi'] != leader_brand]['Tam_Konum'].unique())}</b> farklı lokasyon tespit edildi.</li>
                <li><b>Genel Trend:</b> Pazar yapısı {("Lidere Endeksli" if (leader_count/total_stations) > 0.3 else "Parçalı ve Rekabetçi")}.</li>
                </ul>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            c3, c4 = st.columns(2)

            # --- 3. COĞRAFİ HAKİMİYET ---
            with c3:
                st.markdown("#### 🗺️ 3. Coğrafi Hakimiyet (Detaylı)")
                # Bizim Olup Rakiplerin Az Olduğu (Mavi Okyanus)
                if not hero_df.empty:
                    market_avgs = df_robo.groupby('Tam_Konum').size()
                    my_locs = hero_df['Tam_Konum'].unique()
                    strong_presence = []
                    ghost_zones = [] # Bizim olmadığımız ama pazarın olduğu
                    
                    # Güçlü olduğumuz yerler
                    for loc in my_locs:
                        market_count = market_avgs.get(loc, 0)
                        my_c = len(hero_df[hero_df['Tam_Konum'] == loc])
                        share = my_c / market_count
                        if share > 0.25: # %25'ten fazla payımız varsa
                            strong_presence.append(f"{loc} (%{int(share*100)})")
                            
                    # Hayalet Bölgeler (Biz yokuz, pazar var)
                    all_market_locs = df_robo['Tam_Konum'].unique()
                    for loc in all_market_locs:
                        if loc not in my_locs:
                            market_count = market_avgs.get(loc, 0)
                            if market_count > 5: # En az 5 istasyon olan yerler
                                ghost_zones.append(f"{loc} ({market_count} İstasyon)")
                    
                    st.markdown(f"""
                    <div class="robo-card">
                    <ul class="robo-list">
                    <li><b>Dominant Bölgeler (>%25 Pay):</b> <b>{', '.join(strong_presence[:5]) if strong_presence else 'Yok'}</b>.</li>
                    <li><b>Hayalet Bölgeler (Biz Yokuz!):</b> Rakiplerin cirit attığı ama bizim olmadığımız yerler: <b>{', '.join(ghost_zones[:5]) if ghost_zones else 'Yok'}</b>.</li>
                    <li><b>Saldırı Altındaki Kale:</b> En güçlü ilçemiz <b>{top_hero_dist}</b> bölgesinde toplam <b>{market_avgs.get(top_hero_dist, 0)}</b> rakip var.</li>
                    <li><b>Bölge Verimliliği:</b> Bulunduğumuz ilçelerde ortalama pazar payımız <b>%{int(hero_df.groupby('Tam_Konum').size().mean() / df_robo.groupby('Tam_Konum').size().mean() * 100)}</b>.</li>
                    <li><b>Riskli Bölge:</b> En az istasyonumuzun olduğu (1 adet) <b>{len(hero_df[hero_df.groupby('Tam_Konum')['Tam_Konum'].transform('count') == 1])}</b> farklı ilçe var. Buralarda varlığımız pamuk ipliğine bağlı.</li>
                    </ul>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("Coğrafi analiz için veri yetersiz.")

            # --- 4. SÖZLEŞME PROJEKSİYONU ---
            with c4:
                st.markdown("#### 📅 4. Gelecek Projeksiyonu (Yıl Yıl)")
                
                if 'Bitis_Yili' in df_robo.columns and future_years_market:
                    years_list = sorted(list(future_years_market.keys()))
                    
                    st.write("**Pazar Geneli vs. GÜZEL ENERJİ Sözleşme Bitişleri:**")
                    
                    # Tablo verisi hazırlayalım
                    proj_data = []
                    for y in years_list:
                        m_val = future_years_market.get(y, 0)
                        h_val = future_years_hero.get(y, 0)
                        share_potential = (h_val / m_val * 100) if m_val > 0 else 0
                        proj_data.append({
                            "Yıl": int(y),
                            "Toplam Pazar (Adet)": m_val,
                            "Güzel Enerji (Adet)": h_val,
                            "Payımız (%)": f"%{share_potential:.1f}"
                        })
                    
                    st.dataframe(pd.DataFrame(proj_data), use_container_width=True, hide_index=True)
                        
                    # Yorum
                    peak_year = max(future_years_market, key=future_years_market.get)
                    hero_peak = max(future_years_hero, key=future_years_hero.get) if future_years_hero else "Yok"
                    
                    st.markdown(f"""
                    <div class="robo-card">
                    <ul class="robo-list">
                    <li><b>En Hareketli Yıl:</b> Pazar için <b>{int(peak_year)}</b>, Bizim için <b>{int(hero_peak) if hero_peak!='Yok' else 'Yok'}</b>.</li>
                    </ul>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("İleri tarihli sözleşme verisi bulunamadı.")

        else:
            st.warning("Rapor oluşturmak için lütfen yukarıdan en az bir filtre seçimi yapın.")

    # 10. VERGİ ZİNCİR ANALİZİ [NEW]
    with tabs[9]:
        st.subheader("💸 Vergi Zincir Haritası (Holding/Grup Analizi)")
        st.info("💡 Bu ekran, **aynı Vergi Numarasına (VKN)** sahip olan ve toplam istasyon sayısı **8'den fazla** olan dev zincirleri/grupları listeler.")
        
        df_chain = create_tab_filters(df, "tab_tax_chain")
        
        # VERGİ NO SÜTUNUNU BULMA
        cols_upper = [c.upper().replace('İ','I') for c in df_chain.columns]
        tax_col_name = None
        possible_names = ["VERGI", "VKN", "TCKN", "VERGI KIMLIK", "VERGI NO"]
        
        for col in df_chain.columns:
            u_col = col.upper().replace('İ','I')
            if any(p in u_col for p in possible_names):
                tax_col_name = col
                break
        
        if tax_col_name and not df_chain.empty:
            # 1. VERİ TEMİZLİĞİ: Vergi Numarasını Metne Çevir (Noktalı formatı temizle)
            df_chain[tax_col_name] = df_chain[tax_col_name].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

            # 2. SADECE 8'DEN FAZLA İSTASYONU OLANLARI FİLTRELE
            vkn_counts = df_chain[tax_col_name].value_counts()
            big_bosses = vkn_counts[vkn_counts > 8].index.tolist()
            
            if not big_bosses:
                st.warning("⚠️ Seçilen filtrede **8'den fazla** istasyona sahip bir Vergi Grubu bulunamadı.")
            else:
                # --- ÖZET TABLO OLUŞTURMA (GROUPBY) ---
                st.markdown("### 🏆 Grup Liderleri (Özet)")
                
                # Aggregation logic: Add 'Ana_Unvan'
                summary_df = df_chain[df_chain[tax_col_name].isin(big_bosses)].groupby(tax_col_name).agg(
                    Ana_Unvan=('Unvan', lambda x: x.mode()[0] if not x.mode().empty else x.iloc[0]), # En çok geçen unvanı al
                    Toplam_İstasyon=('Unvan', 'count'),
                    En_Çok_Bulunan_İl=('İl', lambda x: x.mode()[0] if not x.mode().empty else '-')
                ).reset_index().sort_values('Toplam_İstasyon', ascending=False)

                # Sütun isimlerini ve sırasını düzeltelim
                summary_df = summary_df[[tax_col_name, 'Ana_Unvan', 'Toplam_İstasyon', 'En_Çok_Bulunan_İl']] # Sıralama
                summary_df.columns = ['Vergi No / Grup', 'Ana Firma Unvanı (Temsili)', 'Toplam İstasyon', 'En Yoğun İl']
                
                st.dataframe(summary_df, use_container_width=True, hide_index=True)

                st.markdown("---")

                # --- DETAYLI LİSTE (EXPANDER İLE) ---
                st.markdown("### 📂 Grup Detayları (Tıklayıp Açınız)")
                
                # Bu kısım kullanıcının "içine tıklayınca görsün" isteğini karşılar
                matrix_data = df_chain[df_chain[tax_col_name].isin(big_bosses)].copy()
                
                # Sırayla her patron için bir kutu açalım
                for index, row in summary_df.iterrows():
                    vkn = row['Vergi No / Grup']
                    unvan = row['Ana Firma Unvanı (Temsili)']
                    count = row['Toplam İstasyon']
                    
                    with st.expander(f"🔻 {vkn} - {unvan} ({count} İstasyon)"):
                        # O gruba ait veriyi süz
                        sub_df = matrix_data[matrix_data[tax_col_name] == vkn]
                        # Gösterilecek kolonlar
                        disp_cols = ['Unvan', 'Dağıtım Şirketi', 'İl', 'İlçe', target_date_col]
                        final_cols = [c for c in disp_cols if c in sub_df.columns]
                        
                        # Tarih düzeltme
                        if target_date_col in sub_df.columns:
                             try: sub_df[target_date_col] = pd.to_datetime(sub_df[target_date_col]).dt.strftime('%d.%m.%Y')
                             except: pass
                        
                        st.dataframe(sub_df[final_cols], use_container_width=True, hide_index=True)
                    
        else:
            if not tax_col_name:
                st.error("Excel dosyasında 'Vergi No', 'VKN' veya benzeri bir sütun bulunamadı.")
            else:
                st.warning("Veri yok.")

    # 11. DETAYLI ARAMA [NEW]
    with tabs[10]:
        st.subheader("🔍 Detaylı Arama & Bayi Kimlik Kartı")
        st.info("💡 Aşağıdaki kutudan bayi seçimi yapın, sistem tüm bilgileri sizin için derlesin.")
        
        # 1. AKILLI ARAMA LİSTESİ OLUŞTURMA
        if 'Dağıtım Şirketi' in df.columns:
            dist_col = 'Dağıtım Şirketi'
        else:
            dist_col = df.columns[0] # Fallback
            
        df['Arama_Etiketi'] = df['Unvan'].astype(str) + " | " + df['İl'].astype(str) + " - " + df.get('İlçe', '').astype(str) + " (" + df[dist_col].astype(str) + ")"
        
        search_options = sorted(df['Arama_Etiketi'].unique().tolist())
        
        # Arama kutusu
        selected_label = st.selectbox(
            "🔎 Bayi Seçin (Yazmaya başlayın...):",
            options=[""] + search_options,
            index=0,
            placeholder="Örn: YILDIZ PETROL"
        )
        
        # 2. BAYİ KİMLİK KARTI (GÜVENLİ NATIVE KART)
        if selected_label:
            row = df[df['Arama_Etiketi'] == selected_label].iloc[0]
            
            # Verileri Çek
            unvan = row['Unvan']
            dagitici = row.get('Dağıtım Şirketi', '-')
            il = row.get('İl', '-')
            ilce = row.get('İlçe', '-')
            
            # Akıllı Adres Bulucu
            adres_col = None
            for c in df.columns:
                if "ADRES" in c.upper():
                    adres_col = c
                    break
            
            if adres_col:
                adres = row.get(adres_col)
                if pd.isna(adres) or str(adres).lower() == 'nan':
                    adres = f"{ilce} / {il} (Detay Yok)"
            else:
                adres = f"{ilce} / {il}"

            # Vergi No Bulucu
            vergi_no = '-'
            for c in df.columns:
                clean_c = c.upper().replace('İ','I')
                if "VERGI" in clean_c or "VKN" in clean_c:
                    vergi_no = row[c]
                    break
            
            # Tarihler (Hata veren yer burasıydı, düzeltildi)
            baslangic = row[start_date_col].strftime('%d.%m.%Y') if pd.notnull(row.get(start_date_col)) else "-"
            bitis = row[target_date_col].strftime('%d.%m.%Y') if pd.notnull(row.get(target_date_col)) else "-"
            kalan = int(row['Kalan_Gun']) if pd.notnull(row.get('Kalan_Gun')) else 0
            
            # --- NATIVE STREAMLIT KART TASARIMI ---
            # HTML yerine native kullanarak hatayı önlüyoruz
            with st.container(border=True):
                c_header1, c_header2 = st.columns([3, 1])
                with c_header1:
                    st.subheader(f"⛽ {unvan}")
                    st.caption(f"📍 {il} / {ilce}")
                with c_header2:
                    st.info(f"{dagitici}")

                st.divider()
                
                c_info1, c_info2 = st.columns(2)
                
                with c_info1:
                    st.markdown(f"**📍 Adres:** \n{adres}")
                    st.write("") # Boşluk
                    st.markdown(f"**🆔 Vergi / TC No:** \n`{vergi_no}`")
                
                with c_info2:
                    st.markdown(f"**📅 Sözleşme Başlangıç:** \n{baslangic}")
                    st.write("") # Boşluk
                    
                    # Renkli ve vurgulu bitiş tarihi
                    kalan_renk = "red" if kalan < 90 else "green"
                    st.markdown(f"**⏳ Sözleşme Bitiş:** \n{bitis} (:{kalan_renk}[**{kalan} Gün Kaldı**])")
                
                st.divider()
                st.success("📜 **Lisans Durumu:** AKTİF")

    # 12. SİMÜLASYON
    with tabs[11]:
        st.subheader("🔮 Simülasyon")
        df_sim = create_tab_filters(df, "tab4")
        all_comp = sorted(df['Dağıtım Şirketi'].dropna().unique().tolist())
        c1, c2 = st.columns(2)
        my_c = c1.selectbox("Sizin Şirket", all_comp, index=0)
        tar_c = c2.selectbox("Hedef Rakip", [x for x in all_comp if x != my_c])
        rate = st.slider("Kazanma Oranı (%)", 0, 100, 10)
        curr = len(df_sim[df_sim['Dağıtım Şirketi'] == my_c])
        tgt = len(df_sim[df_sim['Dağıtım Şirketi'] == tar_c])
        gain = int(tgt * rate / 100)
        st.metric("Yeni Toplam", curr + gain, delta=f"+{gain}")

    # 13. İL HAKİMİYET HARİTASI (LOGO) - DÜZELTİLMİŞ SÜRÜM
    # 13. İL HAKİMİYET HARİTASI (LOGO) - HILKE1010 ÖZEL VERSİYON
   # 13. İL HAKİMİYET HARİTASI (LOGO) - HILKE1010 FİNAL VERSİYON
   # 13. İL HAKİMİYET HARİTASI (LOGO) - KÜÇÜLTÜLMÜŞ VERSİYON
    with tabs[12]:
        st.subheader("🦁 İl Hakimiyet Haritası (Lider Markalar)")
        st.info("💡 Bu harita, GitHub'daki logoları çekerek her ilin lider markasını gösterir.")
        
        # --- GITHUB ADRESİN ---
        LOGO_URL_BASLANGIC = "https://raw.githubusercontent.com/hilke1010/akrtakip/main/"
        
        # Dosya Eşleştirmeleri
        LOGO_MAP = {
            "OPET": "opet.png",
            "SHELL": "shell.png",
            "PETROL OFİSİ": "po.png",
            "GÜZEL ENERJİ": "ge.png",
            "BP": "bp.png",
            "TOTAL": "total.png",
            "AYGAZ": "aygaz.png",
            "İPRAGAZ": "ipragaz.png",
            "MİLANGAZ": "milangaz.png",
            "TP": "tp.png"
        }
        
        DEFAULT_LOGO = "https://img.icons8.com/color/48/gas-station.png" 

        # --- VERİ HAZIRLIĞI ---
        df_dom = create_tab_filters(df, "tab_dominance")
        
        if not df_dom.empty:
            # 1. Hesaplama
            city_stats = df_dom.groupby(['İl', 'Dağıtım Şirketi']).size().reset_index(name='Adet')
            idx = city_stats.groupby(['İl'])['Adet'].transform(max) == city_stats['Adet']
            leaders = city_stats[idx].drop_duplicates(subset=['İl']).copy()
            
            # 2. Koordinatlar
            leaders['lat'] = leaders['İl'].map(lambda x: CITY_COORDINATES.get(x, [39.0, 35.0])[0])
            leaders['lon'] = leaders['İl'].map(lambda x: CITY_COORDINATES.get(x, [39.0, 35.0])[1])
            
            # 3. İKON PAKETLEME
            def create_icon_data(company_name):
                url = DEFAULT_LOGO
                comp_upper = str(company_name).upper()
                for key, filename in LOGO_MAP.items():
                    if key in comp_upper:
                        url = LOGO_URL_BASLANGIC + filename
                        break
                return {
                    "url": url,
                    "width": 242,
                    "height": 242,
                    "anchorY": 242
                }

            leaders['icon_data'] = leaders['Dağıtım Şirketi'].apply(create_icon_data)
            
            # --- HARİTA ÇİZİMİ ---
            view_state = pdk.ViewState(latitude=39.0, longitude=35.0, zoom=5.5, pitch=0)

            # --- BOYUT AYARI BURADA YAPILDI ---
            icon_layer = pdk.Layer(
                type="IconLayer",
                data=leaders,
                get_icon="icon_data",
                get_position='[lon, lat]',
                # BURAYI DEĞİŞTİRDİK:
                get_size=30,     # Temel boyut (45'ten 30'a indi)
                size_scale=1,    # Çarpan (15'ten 1'e indi - asıl büyüten buydu)
                pickable=True,
            )

            tooltip = {
                "html": "<b>{İl}</b><br/>👑 Lider: <b>{Dağıtım Şirketi}</b><br/>📊 İstasyon: {Adet}",
                "style": {"backgroundColor": "steelblue", "color": "white"}
            }

            r = pdk.Deck(
                map_style=None,
                initial_view_state=view_state,
                layers=[icon_layer],
                tooltip=tooltip
            )

            st.pydeck_chart(r)
            
            # --- ALT TABLO ---
            st.markdown("### 🏆 İl Liderleri Listesi")
            st.dataframe(
                leaders[['İl', 'Dağıtım Şirketi', 'Adet']].sort_values('Adet', ascending=False),
                use_container_width=True,
                hide_index=True
            )
            
        else:
            st.warning("Veri yok.")

if __name__ == "__main__":
    main()











