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
    try:
        if not os.path.exists(file_path):
            return "DOSYA BULUNAMADI"
        timestamp = os.path.getmtime(file_path)
        utc_time = datetime.datetime.utcfromtimestamp(timestamp)
        turkey_time = utc_time + datetime.timedelta(hours=3)
        tr_months = {
            1: 'OCAK', 2: 'ŞUBAT', 3: 'MART', 4: 'NİSAN', 5: 'MAYIS', 6: 'HAZİRAN',
            7: 'TEMMUZ', 8: 'AĞUSTOS', 9: 'EYLÜL', 10: 'EKİM', 11: 'KASIM', 12: 'ARALIK'
        }
        month_name = tr_months.get(turkey_time.month, "")
        return f"{turkey_time.day} {month_name} {turkey_time.year} SAAT {turkey_time.strftime('%H:%M')}"
    except:
        return "TARİH ALINAMADI"

# --- 🎬 CAFCAFLI YÜKLEME ANİMASYONU (ORİJİNAL) ---
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
                position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                background: linear-gradient(-45deg, #021B79, #0575E6, #FF8C00, #ff4e00);
                background-size: 400% 400%; animation: gradientBG 6s ease infinite;
                z-index: 999999; display: flex; flex-direction: column;
                justify-content: center; align-items: center; color: white;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            @keyframes gradientBG { 0% {background-position: 0% 50%;} 50% {background-position: 100% 50%;} 100% {background-position: 0% 50%;} }
            .intro-icon { font-size: 8rem; margin-bottom: 20px; animation: bounce 2s infinite; text-shadow: 0 10px 30px rgba(0,0,0,0.5); }
            .intro-title { font-size: 5rem; font-weight: 900; text-transform: uppercase; color: #ffffff; text-shadow: 4px 4px 0px #021B79, 8px 8px 20px rgba(0,0,0,0.4); animation: fadeInUp 1.2s ease-out; text-align: center; letter-spacing: 4px; margin: 0; padding: 0; }
            .intro-subtitle { font-size: 1.8rem; color: #FFD700; margin-top: 15px; font-weight: 600; text-shadow: 1px 1px 5px rgba(0,0,0,0.5); animation: fadeInUp 1.6s ease-out; letter-spacing: 2px; }
            .loading-bar-container { width: 350px; height: 8px; background: rgba(255,255,255,0.3); margin-top: 50px; border-radius: 10px; overflow: hidden; box-shadow: 0 0 15px rgba(255, 140, 0, 0.5); }
            .loading-bar { width: 100%; height: 100%; background: #fff; transform-origin: left; animation: load 2.5s cubic-bezier(0.4, 0, 0.2, 1) forwards; }
            @keyframes bounce { 0%, 20%, 50%, 80%, 100% {transform: translateY(0);} 40% {transform: translateY(-30px);} 60% {transform: translateY(-15px);} }
            @keyframes fadeInUp { from { opacity: 0; transform: translateY(50px); } to { opacity: 1; transform: translateY(0); } }
            @keyframes load { 0% { transform: scaleX(0); } 100% { transform: scaleX(1); } }
        </style>
        <div class="intro-overlay">
            <div class="intro-icon">⛽</div>
            <h1 class="intro-title">AKARYAKIT<br>BAYİ ANALİZİ</h1>
            <div class="intro-subtitle">GÜNCEL PAZAR VERİLERİ YÜKLENİYOR...</div>
            <div class="loading-bar-container"><div class="loading-bar"></div></div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(2.5)
    placeholder.empty()
    st.session_state['intro_played'] = True

# --- 2. AYARLAR VE CSS (ORİJİNAL) ---
MAX_ROW_DISPLAY = 1000  
MAX_MAP_POINTS = 50000 
PREVIEW_ROW_LIMIT = 100
SABIT_DOSYA_ADI = "asatis.xlsx"

st.markdown("""
<style>
    .stMetric { background-color: #f0f2f6; border-left: 5px solid #2980b9; padding: 15px; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .warning-box { padding: 1rem; background-color: #ffeba0; border-left: 6px solid #ffa500; color: #5c3a00; border-radius: 4px; font-weight: bold; }
    .year-box { background-color: #e8f4f8; padding: 10px; border-radius: 5px; text-align: center; border: 1px solid #b3e5fc; margin-bottom: 5px; }
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

# --- 3. KOORDİNAT VERİTABANI (ORİJİNAL) ---
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

BOLGE_TANIMLARI = {
    "Orta Anadolu": ["DÜZCE", "KARABÜK", "KONYA", "BOLU", "AFYONKARAHİSAR", "AKSARAY", "ESKİŞEHİR", "ANKARA", "KIRIKKALE", "KASTAMONU", "ÇANKIRI", "YOZGAT", "KIRŞEHİR", "KAYSERİ", "NEVŞEHİR", "NİĞDE", "ZONGULDAK", "BARTIN"]
}

# --- 4. VERİ YÜKLEME (ORİJİNAL) ---
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path): return None, None, None
    try:
        df = pd.read_excel(file_path)
        df.columns = [str(c).strip() for c in df.columns]
        if 'Dağıtıcı' in df.columns: df.rename(columns={'Dağıtıcı': 'Dağıtım Şirketi'}, inplace=True)
        date_cols = ['Lisans Başlangıç Tarihi', 'Lisans Bitiş Tarihi', 'Dağıtıcı ile Yapılan Sözleşme Başlangıç Tarihi', 'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi']
        for col in date_cols:
            if col in df.columns: df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
        
        target_col = 'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi' if 'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi' in df.columns else 'Lisans Bitiş Tarihi'
        start_col = 'Dağıtıcı ile Yapılan Sözleşme Başlangıç Tarihi' if 'Dağıtıcı ile Yapılan Sözleşme Başlangıç Tarihi' in df.columns else 'Lisans Başlangıç Tarihi'
        
        today = pd.to_datetime(datetime.date.today())
        df['Kalan_Gun'] = (df[target_col] - today).dt.days
        df['Bitis_Yili'] = df[target_col].dt.year
        df['Bitis_Ayi_No'] = df[target_col].dt.month
        month_map = {1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan', 5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos', 9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'}
        df['Bitis_Ayi'] = df['Bitis_Ayi_No'].map(month_map)
        df['Sozlesme_Suresi_Gun'] = (df[target_col] - df[start_col]).dt.days
        df['Risk_Durumu'] = df['Kalan_Gun'].apply(lambda x: "SÜRESİ DOLDU 🚨" if x<0 else ("KRİTİK (<3 Ay) ⚠️" if x<90 else ("YAKLAŞIYOR (<6 Ay) ⏳" if x<180 else "GÜVENLİ ✅")))
        df['İl'] = df['İl'].astype(str).str.upper().str.replace('i', 'İ').str.replace('ı', 'I')
        df['İlçe'] = df['İlçe'].astype(str).str.upper().str.replace('i', 'İ').str.replace('ı', 'I')
        return df, target_col, start_col
    except Exception as e: return None, str(e), None

def show_details_table(dataframe, target_date_col, extra_cols=None):
    if dataframe is None or dataframe.empty:
        st.info("Seçilen kriterlere uygun kayıt bulunamadı.")
        return
    record_count = len(dataframe)
    if record_count > MAX_ROW_DISPLAY:
        st.markdown(f"<div class='warning-box'>⚠️ <b>Performans Uyarısı:</b> Listede toplam <b>{record_count:,}</b> kayıt var. Sadece ilk <b>{MAX_ROW_DISPLAY:,}</b> tanesi gösteriliyor.</div>", unsafe_allow_html=True)
        display_df_limit = dataframe.head(MAX_ROW_DISPLAY)
    else: display_df_limit = dataframe

    cols = ['Unvan', 'İl', 'İlçe', 'Dağıtım Şirketi', target_date_col, 'Kalan_Gun', 'Sozlesme_Suresi_Gun', 'Risk_Durumu']
    if extra_cols: cols.extend(extra_cols)
    final_cols = []
    seen = set()
    for c in cols:
        if c in display_df_limit.columns and c not in seen:
            final_cols.append(c)
            seen.add(c)
    
    display_df = display_df_limit[final_cols].copy()
    for c in [col for col in display_df.columns if "Tarihi" in col]:
        try: display_df[c] = pd.to_datetime(display_df[c]).dt.strftime('%d.%m.%Y')
        except: pass
    
    st.markdown(f"**📋 Listelenen Bayi Sayısı:** {len(dataframe)}")
    
    # EXCEL MOTORU HATASI DÜZELTİLDİ
    if record_count > 0:
        buf = io.BytesIO()
        dataframe.to_excel(buf, index=False)
        st.download_button(label=f"📥 Tüm Listeyi Excel İndir ({record_count} Kayıt)", data=buf.getvalue(), file_name="Bayi_Listesi.xlsx")

    st.dataframe(display_df, use_container_width=True, hide_index=True)

# --- 🛰️ SAYFA İÇİ FİLTRE MOTORU ---
def local_filter_ui(df_base, suffix, include_comp=True):
    st.markdown("#### 🔍 Bu Sayfa İçin Filtrele")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        reg = st.selectbox("🌍 Bölge", ["Tümü"] + list(BOLGE_TANIMLARI.keys()), key=f"reg_{suffix}")
    
    df_temp = df_base.copy()
    if reg != "Tümü": df_temp = df_temp[df_temp['İl'].isin(BOLGE_TANIMLARI[reg])]
    
    with c2:
        cities = sorted(df_temp['İl'].unique().tolist())
        sel_cities = st.multiselect("🏢 Şehir", cities, key=f"city_{suffix}")
    if sel_cities: df_temp = df_temp[df_temp['İl'].isin(sel_cities)]
    
    with c3:
        districts = sorted(df_temp['İlçe'].unique().tolist())
        sel_dist = st.multiselect("📍 İlçe", districts, key=f"dist_{suffix}")
    if sel_dist: df_temp = df_temp[df_temp['İlçe'].isin(sel_dist)]
    
    if include_comp:
        with c4:
            comps = sorted(df_temp['Dağıtım Şirketi'].dropna().unique().tolist())
            sel_comp = st.multiselect("⛽ Şirket", comps, key=f"comp_{suffix}")
        if sel_comp: df_temp = df_temp[df_temp['Dağıtım Şirketi'].isin(sel_comp)]
    
    return df_temp

# --- ANA UYGULAMA ---
def main():
    show_intro_animation()
    df, target_date_col, start_date_col = load_data(SABIT_DOSYA_ADI)
    if df is None: st.error("Veri yüklenemedi."); st.stop()
    
    file_date_str = get_file_last_modified(SABIT_DOSYA_ADI)

    # SIDEBAR TEMİZLENDİ
    with st.sidebar:
        st.success(f"🔄 **VERİ GÜNCELLEME:**\n\n{file_date_str}")
        st.info("💡 **Gelişmeye destek olur musunuz?**\n\n📧 kerim.aksu@milangaz.com.tr")
        st.markdown("---")
        st.header("🔗 Diğer Uygulamalar")
        st.markdown("[📊 EPDK LPG Sektör Raporu](https://pazarpayi.streamlit.app/)")
        st.markdown("[📰 Haber Aracı](https://newslpg.streamlit.app/)")
        st.markdown("[📱 Mobil Hesaplayıcı](https://lpg2026.streamlit.app/)")

    st.title("🚀 Akaryakıt Pazar & Risk Analizi")
    st.divider()

    tab_overview, tab_machine, tab_compare, tab_sim, tab_calendar, tab_radar, tab_ilce, tab_report, tab_crm, tab_data = st.tabs([
        "📊 Bölgesel", "🤖 Makine Analizi", "⚔️ Karşılaştırma", "🔮 Simülasyon", "📅 Takvim", "📡 Radar", "📍 İlçe", "📄 İl Karnesi", "📝 CRM Lite", "📋 Ham Veri"
    ])

    # 1. BÖLGESEL & DURUM
    with tab_overview:
        df_f = local_filter_ui(df, "ov")
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Toplam İstasyon", f"{len(df_f):,}")
        c2.metric("Acil Sözleşme", len(df_f[df_f['Kalan_Gun'] < 90]), delta="Acil Yenileme", delta_color="inverse")
        c3.metric("Aktif Dağıtıcı", df_f['Dağıtım Şirketi'].nunique())
        
        # HARİTA (ORİJİNAL RENK VE BOYUTLAR GERİ GELDİ)
        if not df_f.empty:
            map_data = df_f['İl'].value_counts().reset_index()
            map_data.columns = ['İl', 'Adet']
            map_data['lat'] = map_data['İl'].map(lambda x: CITY_COORDINATES.get(x, [None, None])[0])
            map_data['lon'] = map_data['İl'].map(lambda x: CITY_COORDINATES.get(x, [None, None])[1])
            map_data = map_data.dropna()
            fig_map = px.scatter_mapbox(
                map_data, lat="lat", lon="lon", size="Adet", color="Adet",
                hover_name="İl", size_max=35, zoom=4.8, 
                mapbox_style="open-street-map", color_continuous_scale=px.colors.sequential.Bluered,
                title="İl Bazlı Bayi Yoğunluğu"
            )
            fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
            st.plotly_chart(fig_map, use_container_width=True)
            show_details_table(df_f, target_date_col)

    # 2. MAKİNE ANALİZİ
    with tab_machine:
        st.subheader("🤖 Makine Analizi (Akıllı Asistan)")
        m_df = local_filter_ui(df, "mch", include_comp=False)
        st.divider()
        my_comp = "GÜZEL ENERJİ AKARYAKIT ANONİM ŞİRKETİ"
        my_df = m_df[m_df['Dağıtım Şirketi'] == my_comp]
        
        if not m_df.empty:
            if not my_df.empty:
                st.markdown(f"<div class='insight-box-success'><b>🏆 En Güçlü Kale:</b> {my_df['İl'].value_counts().idxmax()} ({my_df['İl'].value_counts().max()} Bayi)</div>", unsafe_allow_html=True)
            
            missing = sorted(list(set(m_df['İlçe'].unique()) - set(my_df['İlçe'].unique())))
            st.markdown(f"<div class='insight-box-warning'><b>🚀 Boş Noktalar:</b> Seçili alandaki {len(missing)} ilçede hiç bayiniz yok.</div>", unsafe_allow_html=True)
            
            p_val = [len(my_df), len(m_df)-len(my_df)]
            fig_p = px.pie(names=['GÜZEL ENERJİ', 'RAKİPLER'], values=p_val, hole=0.5, title="Pazar Hakimiyeti", color_discrete_sequence=['#2ecc71', '#e74c3c'])
            st.plotly_chart(fig_p)

    # 3. KARŞILAŞTIRMA (VS.)
    with tab_compare:
        st.subheader("⚔️ Head-to-Head Rakip Analizi")
        df_vs = local_filter_ui(df, "vss", include_comp=False)
        st.divider()
        comps = sorted(df_vs['Dağıtım Şirketi'].dropna().unique().tolist())
        if len(comps) > 1:
            v1, v2 = st.columns(2)
            c_a = v1.selectbox("Şirket A", comps, index=0, key="va")
            c_b = v2.selectbox("Şirket B", comps, index=1 if len(comps)>1 else 0, key="vb")
            res_a = df_vs[df_vs['Dağıtım Şirketi']==c_a]
            res_b = df_vs[df_vs['Dağıtım Şirketi']==c_b]
            k1, k2 = st.columns(2)
            k1.metric(c_a, len(res_a))
            k2.metric(c_b, len(res_b), delta=len(res_b)-len(res_a))
            vs_data = df_vs[df_vs['Dağıtım Şirketi'].isin([c_a, c_b])].groupby(['İl', 'Dağıtım Şirketi']).size().reset_index(name='Adet')
            st.plotly_chart(px.bar(vs_data, x='İl', y='Adet', color='Dağıtım Şirketi', barmode='group'))

    # 4. SİMÜLASYON
    with tab_sim:
        st.subheader("🔮 Simülasyon Analizi")
        df_s = local_filter_ui(df, "sim", include_comp=False)
        st.divider()
        my_c = "GÜZEL ENERJİ AKARYAKIT ANONİM ŞİRKETİ"
        target_c = st.selectbox("Hedef Rakip", [c for c in sorted(df_s['Dağıtım Şirketi'].unique()) if c != my_c])
        oran = st.slider("Kazanma Oranı (%)", 0, 100, 10)
        curr = len(df_s[df_s['Dağıtım Şirketi']==my_c])
        gain = int(len(df_s[df_s['Dağıtım Şirketi']==target_c]) * oran / 100)
        st.metric("Öngörülen Yeni Bayi Toplamı", curr + gain, delta=f"+{gain}")

    # 5. TAKVİM
    with tab_calendar:
        st.subheader("📅 Aylık Sözleşme Takvimi")
        df_c = local_filter_ui(df, "cal")
        yrs = sorted(df_c['Bitis_Yili'].dropna().unique().astype(int))
        if yrs:
            sel_y = st.selectbox("Yıl Seçin", yrs, key="sy")
            cal_data = df_c[df_c['Bitis_Yili']==sel_y].groupby('Bitis_Ayi').size().reindex(['Ocak','Şubat','Mart','Nisan','Mayıs','Haziran','TEMMUZ','Ağustos','Eylül','Ekim','Kasım','Aralık']).fillna(0)
            st.plotly_chart(px.bar(cal_data, title=f"{sel_y} Yılı Sözleşme Bitiş Dağılımı"))
            show_details_table(df_c[df_c['Bitis_Yili']==sel_y], target_date_col)

    # 6. SÖZLEŞME RADAR
    with tab_radar:
        st.subheader("📡 Sözleşme Radar")
        df_r = local_filter_ui(df, "rad")
        st.divider()
        radar_df = df_r[(df_r['Sozlesme_Suresi_Gun'] < 90) & (df_r['Sozlesme_Suresi_Gun'] >= 0)]
        if not radar_df.empty:
            st.error(f"⚠️ Kritik Durumda olan {len(radar_df)} sözleşme bulundu.")
            show_details_table(radar_df, target_date_col)
        else: st.success("Seçili kriterlerde kritik sözleşme bulunmamaktadır.")

    # 7. İLÇE PENETRASYONU
    with tab_ilce:
        st.subheader("📍 İlçe Bazlı Derinlik")
        df_i = local_filter_ui(df, "ilc")
        if not df_i.empty:
            d_cnt = df_i.groupby('İlçe').size().reset_index(name='Adet').sort_values('Adet', ascending=False)
            st.plotly_chart(px.bar(d_cnt.head(20), x='İlçe', y='Adet', title="İstasyon Sayısına Göre En Yoğun 20 İlçe"))
            show_details_table(df_i, target_date_col)

    # 8. İL KARNESİ
    with tab_report:
        st.subheader("📄 İl Karnesi")
        report_city = st.selectbox("İl Seçin", sorted(df['İl'].unique()), key="rep_city")
        city_df = df[df['İl'] == report_city]
        st.markdown(f"### {report_city} Pazar Özeti")
        r1, r2, r3 = st.columns(3)
        r1.metric("Toplam İstasyon", len(city_df))
        r2.metric("Pazar Lideri", city_df['Dağıtım Şirketi'].value_counts().idxmax() if not city_df.empty else "N/A")
        r3.metric("Güzel Enerji", len(city_df[city_df['Dağıtım Şirketi']=="GÜZEL ENERJİ AKARYAKIT ANONİM ŞİRKETİ"]))
        st.plotly_chart(px.pie(city_df['Dağıtım Şirketi'].value_counts().head(5), names=city_df['Dağıtım Şirketi'].value_counts().head(5).index, title="Pazar Payı Dağılımı"))

    # 9. CRM LITE
    with tab_crm:
        st.subheader("📝 CRM Lite")
        df_crm = local_filter_ui(df, "crm")
        if not df_crm.empty:
            sel_b = st.selectbox("Bayi Unvanı", sorted(df_crm['Unvan'].unique()), key="sb")
            note = st.text_area("Bayi Notu")
            if st.button("Kaydet"): st.success("Not kaydedildi (Veritabanı bağlantısı kapalı olduğu için simüle edildi).")

    # 10. HAM VERİ
    with tab_data:
        st.subheader("📋 Ham Veri")
        df_v = local_filter_ui(df, "raw")
        st.dataframe(df_v.head(PREVIEW_ROW_LIMIT), use_container_width=True)
        # EXCEL MOTORU HATASI DÜZELTİLDİ
        buf = io.BytesIO()
        df_v.to_excel(buf, index=False)
        st.download_button("📥 Seçili Listeyi Excel İndir", buf.getvalue(), "bayi_listesi.xlsx")

if __name__ == "__main__":
    main()
