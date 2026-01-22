import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import io
import time
import math
from datetime import datetime, timedelta, date

# --- 1. SAYFA VE GENEL AYARLAR ---
st.set_page_config(
    page_title="EPDK Akaryakıt Pazar Analizi",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="collapsed" 
)

# --- YARDIMCI FONKSİYONLAR ---

def haversine(lat1, lon1, lat2, lon2):
    """İki koordinat arası mesafe (km)"""
    if any(x is None for x in [lat1, lon1, lat2, lon2]): return 99999
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

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

def show_intro_animation():
    if 'intro_played' not in st.session_state: st.session_state['intro_played'] = False
    if st.session_state['intro_played']: return
    placeholder = st.empty()
    with placeholder.container():
       st.markdown("""
        <div style="background-color:#f8d7da; padding:20px; border-radius:10px; border-left:6px solid #dc3545; text-align:center;">
            <h2 style="color:#721c24; margin:0;">🚀 SİSTEM YÜKLENİYOR...</h2>
            <p>Veriler işleniyor, haritalar oluşturuluyor.</p>
        </div>
        """, unsafe_allow_html=True)
       time.sleep(1.2)
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
    .insight-box-danger { padding: 15px; border-radius: 8px; background-color: #f8d7da; border-left: 5px solid #dc3545; color: #721c24; margin-bottom: 10px; }
    .insight-box-info { padding: 15px; border-radius: 8px; background-color: #d1ecf1; border-left: 5px solid #17a2b8; color: #0c5460; margin-bottom: 10px; }
    .district-chip { display: inline-block; background-color: #f1f3f5; padding: 5px 10px; margin: 3px; border-radius: 15px; font-size: 0.9em; border: 1px solid #ddd; cursor: help; }
    .filter-container { background-color: #e3f2fd; padding: 15px; border-radius: 10px; border: 1px solid #bbdefb; margin-bottom: 15px; }
    
    /* Chatbot Stili */
    .chat-user { text-align: right; background-color: #dcf8c6; padding: 10px; border-radius: 10px; margin: 5px; display: inline-block; float: right; clear: both; }
    .chat-bot { text-align: left; background-color: #f1f0f0; padding: 10px; border-radius: 10px; margin: 5px; display: inline-block; float: left; clear: both; }
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

BOLGE_TANIMLARI = {
    "Orta Anadolu": ["DÜZCE", "KARABÜK", "KONYA", "BOLU", "AFYONKARAHİSAR", "AKSARAY", "ESKİŞEHİR", "ANKARA", "KIRIKKALE"]
}

if 'crm_notes' not in st.session_state: st.session_state.crm_notes = {}
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

# --- VERİ YÜKLEME ---
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path): return None, None, None
    try:
        df = pd.read_excel(file_path)
        df.columns = [str(c).strip() for c in df.columns]
        if 'Dağıtıcı' in df.columns: df.rename(columns={'Dağıtıcı': 'Dağıtım Şirketi'}, inplace=True)
        
        date_cols = ['Lisans Bitiş Tarihi', 'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi', 'Lisans Başlangıç Tarihi']
        for col in date_cols:
            if col in df.columns: df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

        target_col = 'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi' if 'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi' in df.columns else 'Lisans Bitiş Tarihi'
        start_col = 'Dağıtıcı ile Yapılan Sözleşme Başlangıç Tarihi'
        today = pd.to_datetime(date.today())
        
        if target_col in df.columns:
            df['Kalan_Gun'] = (df[target_col] - today).dt.days
            df['Bitis_Yili'] = df[target_col].dt.year
            df['Bitis_Ayi_No'] = df[target_col].dt.month
        else: df['Kalan_Gun'] = np.nan

        if start_col in df.columns and target_col in df.columns:
            df['Sozlesme_Suresi_Gun'] = (df[target_col] - df[start_col]).dt.days
        else: df['Sozlesme_Suresi_Gun'] = np.nan

        df['Risk_Durumu'] = df['Kalan_Gun'].apply(lambda x: "KRİTİK" if x < 90 else "GÜVENLİ")
        if 'İl' in df.columns: df['İl'] = df['İl'].astype(str).str.upper().str.replace('i', 'İ').str.replace('ı', 'I')
        
        return df, target_col, start_col
    except Exception as e: return None, str(e), None

def show_details_table(dataframe, target_date_col):
    if dataframe is None or dataframe.empty:
        st.info("Kayıt bulunamadı.")
        return
    if len(dataframe) > MAX_ROW_DISPLAY:
        st.markdown(f"<div class='warning-box'>⚠️ Performans: İlk {MAX_ROW_DISPLAY} kayıt gösteriliyor.</div>", unsafe_allow_html=True)
        display_df = dataframe.head(MAX_ROW_DISPLAY).copy()
    else: display_df = dataframe.copy()

    for col in display_df.columns:
        if "Tarih" in col:
            try: display_df[col] = pd.to_datetime(display_df[col]).dt.strftime('%d.%m.%Y')
            except: pass

    st.markdown(f"**📋 Kayıt:** {len(display_df)}")
    buffer = io.BytesIO()
    try:
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as w: dataframe.to_excel(w, index=False)
        st.download_button("📥 Excel İndir", buffer.getvalue(), "Liste.xlsx", "application/vnd.ms-excel")
    except: pass
    st.dataframe(display_df, use_container_width=True, hide_index=True)

# ==========================================
# 🛠️ BAĞIMSIZ FİLTRE FONKSİYONU
# ==========================================
def create_tab_filters(df, key_prefix):
    st.markdown(f"#### 🔍 Filtre Paneli")
    st.markdown(f"<div class='filter-container'>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        reg = st.selectbox("🌍 Bölge", ["Tümü"] + list(BOLGE_TANIMLARI.keys()), key=f"{key_prefix}_r")
    f = df.copy()
    if reg != "Tümü": f = f[f['İl'].isin(BOLGE_TANIMLARI[reg])]
    with c2:
        cit = st.multiselect("🏢 İl", sorted(f['İl'].unique()), key=f"{key_prefix}_c")
    if cit: f = f[f['İl'].isin(cit)]
    with c3:
        dst = st.multiselect("📍 İlçe", sorted(f['İlçe'].unique()) if 'İlçe' in f.columns else [], key=f"{key_prefix}_d")
    if dst: f = f[f['İlçe'].isin(dst)]
    with c4:
        cmp = st.multiselect("⛽ Şirket", sorted(f['Dağıtım Şirketi'].dropna().astype(str).unique()), key=f"{key_prefix}_co")
    if cmp: f = f[f['Dağıtım Şirketi'].isin(cmp)]
    st.markdown("</div>", unsafe_allow_html=True)
    return f

# --- ANA UYGULAMA ---
def main():
    show_intro_animation()
    data_result = load_data(SABIT_DOSYA_ADI)
    if data_result is None or data_result[0] is None:
        st.error(f"⚠️ Hata: {data_result[1]}")
        st.stop()
    df, target_date_col, start_date_col = data_result
    
    # KOORDİNAT SİMÜLASYONU
    if 'Enlem' not in df.columns:
        np.random.seed(42)
        df['base_lat'] = df['İl'].map(lambda x: CITY_COORDINATES.get(x, [39.0, 35.0])[0])
        df['base_lon'] = df['İl'].map(lambda x: CITY_COORDINATES.get(x, [39.0, 35.0])[1])
        df['Enlem_Sim'] = df['base_lat'] + np.random.uniform(-0.05, 0.05, size=len(df))
        df['Boylam_Sim'] = df['base_lon'] + np.random.uniform(-0.05, 0.05, size=len(df))
        lat_col, lon_col = 'Enlem_Sim', 'Boylam_Sim'
    else: lat_col, lon_col = 'Enlem', 'Boylam'

    file_date_str = get_file_last_modified(SABIT_DOSYA_ADI)

    # --- ÜST BİLGİ PANELİ ---
    st.markdown("### 🚀 Akaryakıt Pazar & Risk Analizi")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1: st.success(f"🔄 **Güncelleme:**\n{file_date_str}")
    with c2: st.info(f"📧 **İletişim:**\nkerim.aksu@milangaz.com.tr")
    with c3: 
        st.warning("🔗 **Uygulamalar**")
        st.markdown("<a href='https://pazarpayi.streamlit.app/'>Rapor</a> | <a href='https://newslpg.streamlit.app/'>Haber</a> | <a href='https://lpg2026.streamlit.app/'>Mobil</a>", unsafe_allow_html=True)
    st.divider()

    # --- KPI ---
    k1, k2, k3 = st.columns(3)
    k1.metric("Toplam İstasyon", f"{len(df):,}")
    k2.metric("Şirket Sayısı", df['Dağıtım Şirketi'].nunique())
    k3.metric("Kritik Kayıt", len(df[df['Kalan_Gun'] < 90]), delta="Acil", delta_color="inverse")
    st.divider()

    # --- SEKMELER ---
    tabs = st.tabs([
        "📊 Bölgesel", "🤖 Makine", "⚔️ Karşılaştırma", 
        "📍 Yarıçap Analizi", "🚗 Rota Planlayıcı", # <-- AYRILDI
        "🔮 Simülasyon", "📅 Takvim", "📡 Sözleşme Radar", 
        "📍 İlçe", "📄 Karne", "💬 Chatbot Lite", "📝 CRM", "📋 Veri" # <-- CHATBOT EKLENDİ
    ])

    # 1. BÖLGESEL
    with tabs[0]:
        st.subheader("🗺️ Bölgesel Yoğunluk")
        df_t1 = create_tab_filters(df, "t1")
        if not df_t1.empty:
            map_data = df_t1['İl'].value_counts().reset_index()
            map_data.columns = ['İl', 'Adet']
            map_data['lat'] = map_data['İl'].map(lambda x: CITY_COORDINATES.get(x, [None, None])[0])
            map_data['lon'] = map_data['İl'].map(lambda x: CITY_COORDINATES.get(x, [None, None])[1])
            map_data = map_data.dropna()
            
            fig_map = px.scatter_mapbox(map_data, lat="lat", lon="lon", size="Adet", color="Adet", hover_name="İl", zoom=5, mapbox_style="open-street-map", color_continuous_scale=px.colors.sequential.Bluered)
            fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig_map, use_container_width=True)
            
            c_pie, d_pie = st.columns(2)
            with c_pie:
                st.plotly_chart(px.pie(df_t1['İl'].value_counts().reset_index(), values='count', names='İl', title="Şehir Dağılımı"), use_container_width=True)
            with d_pie:
                st.plotly_chart(px.pie(df_t1['Dağıtım Şirketi'].value_counts().reset_index(), values='count', names='Dağıtım Şirketi', title="Pazar Payı"), use_container_width=True)
            show_details_table(df_t1, target_date_col)

    # 2. MAKİNE
    with tabs[1]:
        st.subheader("🤖 Makine Analizi")
        df_t2 = create_tab_filters(df, "t2")
        if not df_t2.empty:
            top_city = df_t2['İl'].value_counts().idxmax()
            st.success(f"🏆 Lider Bölge: **{top_city}**")
            st.plotly_chart(px.pie(df_t2['Dağıtım Şirketi'].value_counts().reset_index(), values='count', names='Dağıtım Şirketi', hole=0.5, title="Filtre İçi Pay"), use_container_width=True)
        else: st.warning("Veri yok.")

    # 3. KARŞILAŞTIRMA
    with tabs[2]:
        st.subheader("⚔️ Rakip Analizi")
        df_t3 = create_tab_filters(df, "t3")
        comps = sorted(df['Dağıtım Şirketi'].dropna().unique())
        ca, cb = st.columns(2)
        comp_a = ca.selectbox("Şirket A", comps, index=0)
        comp_b = cb.selectbox("Şirket B", comps, index=1 if len(comps)>1 else 0)
        
        d_a = df_t3[df_t3['Dağıtım Şirketi'] == comp_a]
        d_b = df_t3[df_t3['Dağıtım Şirketi'] == comp_b]
        ca.metric(f"{comp_a}", len(d_a))
        cb.metric(f"{comp_b}", len(d_b), delta=len(d_b)-len(d_a))
        
        common = df_t3[df_t3['Dağıtım Şirketi'].isin([comp_a, comp_b])]
        if not common.empty:
            st.plotly_chart(px.bar(common.groupby(['İl','Dağıtım Şirketi']).size().reset_index(name='Adet'), x='İl', y='Adet', color='Dağıtım Şirketi', barmode='group'), use_container_width=True)

    # 4. YARIÇAP ANALİZİ (YENİ TAB)
    with tabs[3]:
        st.subheader("📍 Yarıçap (Radar) Analizi")
        st.info("Bir bayi seçin ve çevresindeki (X km) rakipleri tarayın.")
        df_rad = create_tab_filters(df, "t_radar")
        
        if not df_rad.empty:
            station_list = sorted(df_rad['Unvan'].unique())
            center_station = st.selectbox("Merkez Bayi:", station_list)
            radius = st.slider("Mesafe (KM)", 1, 50, 10)
            
            center_row = df_rad[df_rad['Unvan'] == center_station].iloc[0]
            pool = df[df['İl'] == center_row['İl']].copy() # Sadece aynı ilde ara (Hız için)
            
            pool['Mesafe'] = pool.apply(lambda r: haversine(center_row[lat_col], center_row[lon_col], r[lat_col], r[lon_col]), axis=1)
            nearby = pool[pool['Mesafe'] <= radius].sort_values('Mesafe')
            
            st.success(f"🎯 **{radius} km** içinde **{len(nearby)}** istasyon bulundu.")
            if not nearby.empty:
                nearby['Tip'] = np.where(nearby['Unvan'] == center_station, 'MERKEZ', 'RAKİP')
                fig_rad = px.scatter_mapbox(nearby, lat=lat_col, lon=lon_col, color='Tip', size='Mesafe', 
                                            hover_data=['Unvan', 'Dağıtım Şirketi', 'Mesafe'],
                                            color_discrete_map={'MERKEZ':'red', 'RAKİP':'blue'}, zoom=11, mapbox_style="open-street-map")
                st.plotly_chart(fig_rad, use_container_width=True)
                st.dataframe(nearby[['Unvan', 'Dağıtım Şirketi', 'İlçe', 'Mesafe']])

    # 5. ROTA PLANLAYICI (YENİ TAB)
    with tabs[4]:
        st.subheader("🚗 Akıllı Rota Planlayıcı")
        st.info("Gidilecek bayileri seçin, en mantıklı sırayı biz oluşturalım.")
        df_rot = create_tab_filters(df, "t_rota")
        
        if not df_rot.empty:
            targets = st.multiselect("Ziyaret Listesi:", df_rot['Unvan'].unique())
            if len(targets) > 1:
                visit_df = df_rot[df_rot['Unvan'].isin(targets)].copy()
                # Basit Nearest Neighbor
                route = []
                rem = visit_df.copy()
                curr = rem.iloc[0]
                route.append(curr)
                rem = rem.drop(curr.name)
                
                while len(rem) > 0:
                    rem['dist'] = rem.apply(lambda r: haversine(curr[lat_col], curr[lon_col], r[lat_col], r[lon_col]), axis=1)
                    nearest = rem.loc[rem['dist'].idxmin()]
                    route.append(nearest)
                    curr = nearest
                    rem = rem.drop(nearest.name)
                
                route_df = pd.DataFrame(route)
                route_df['Sıra'] = range(1, len(route_df)+1)
                
                st.success("✅ Rota Oluşturuldu!")
                fig_rt = px.line_mapbox(route_df, lat=lat_col, lon=lon_col, zoom=10, mapbox_style="open-street-map")
                fig_rt.add_trace(go.Scattermapbox(lat=route_df[lat_col], lon=route_df[lon_col], mode='markers+text', 
                                                  marker=go.scattermapbox.Marker(size=15, color='green'),
                                                  text=route_df['Sıra'], textposition="top center"))
                st.plotly_chart(fig_rt, use_container_width=True)
                st.dataframe(route_df[['Sıra', 'Unvan', 'İlçe', 'Dağıtım Şirketi']])

    # 6. SİMÜLASYON
    with tabs[5]:
        st.subheader("🔮 Simülasyon")
        df_sim = create_tab_filters(df, "t_sim")
        comps = sorted(df['Dağıtım Şirketi'].dropna().unique())
        c1, c2 = st.columns(2)
        my_c = c1.selectbox("Biz", comps, index=0)
        tr_c = c2.selectbox("Hedef", [x for x in comps if x!=my_c])
        rate = st.slider("Kazanma %", 0, 100, 10)
        
        curr = len(df_sim[df_sim['Dağıtım Şirketi'] == my_c])
        tgt = len(df_sim[df_sim['Dağıtım Şirketi'] == tr_c])
        gain = int(tgt * rate / 100)
        st.metric("Yeni Toplam", curr + gain, delta=f"+{gain}")

    # 7. TAKVİM
    with tabs[6]:
        st.subheader("📅 Takvim")
        df_cal = create_tab_filters(df, "t_cal")
        if 'Bitis_Yili' in df_cal.columns:
            yrs = sorted(df_cal['Bitis_Yili'].dropna().astype(int).unique())
            yr = st.selectbox("Yıl", yrs)
            d_yr = df_cal[df_cal['Bitis_Yili'] == yr]
            if not d_yr.empty:
                st.bar_chart(d_yr['Bitis_Ayi_No'].value_counts())
                show_details_table(d_yr, target_date_col)

    # 8. SÖZLEŞME RADAR
    with tabs[7]:
        st.subheader("📡 Sözleşme Radar")
        df_sr = create_tab_filters(df, "t_sr")
        if 'Sozlesme_Suresi_Gun' in df_sr.columns:
            risk = df_sr[(df_sr['Sozlesme_Suresi_Gun'] < 90) & (df_sr['Sozlesme_Suresi_Gun'] >= 0)]
            if not risk.empty: 
                st.error(f"{len(risk)} Riskli Kayıt")
                show_details_table(risk, target_date_col)
            else: st.success("Temiz")

    # 9. İLÇE
    with tabs[8]:
        st.subheader("📍 İlçe Analiz")
        df_ilce = create_tab_filters(df, "t_ilce")
        if not df_ilce.empty:
            cnt = df_ilce['İlçe'].value_counts().reset_index()
            cnt.columns = ['İlçe', 'Adet']
            st.plotly_chart(px.bar(cnt.head(20), x='Adet', y='İlçe', orientation='h'), use_container_width=True)

    # 10. KARNE
    with tabs[9]:
        st.subheader("📄 İl Karnesi")
        city = st.selectbox("İl", sorted(df['İl'].unique()))
        cdf = df[df['İl'] == city]
        comp = st.selectbox("Şirket", sorted(cdf['Dağıtım Şirketi'].unique()))
        mdf = cdf[cdf['Dağıtım Şirketi'] == comp]
        
        c1, c2 = st.columns(2)
        c1.metric("Toplam Pazar", len(cdf))
        c2.metric(f"{comp} Payı", len(mdf))
        
        if 'Bitis_Yili' in mdf.columns:
            st.bar_chart(mdf['Bitis_Yili'].value_counts().sort_index())
            st.dataframe(mdf[['Unvan', 'İlçe', 'Bitis_Yili']].sort_values('Bitis_Yili'), use_container_width=True)

    # 11. CHATBOT LİTE (YENİ TAB)
    with tabs[10]:
        st.subheader("💬 Chatbot Lite (Veriyle Konuş)")
        st.info("Örnekler: 'Ankara'da kaç bayi var?', 'Opet toplam sayısı?', 'En büyük il hangisi?', 'Muğla detay'")
        
        # Chat Arayüzü
        for msg in st.session_state.chat_history:
            role_class = "chat-user" if msg["role"] == "user" else "chat-bot"
            st.markdown(f"<div class='{role_class}'>{msg['content']}</div>", unsafe_allow_html=True)
            
        prompt = st.chat_input("Sorunuzu buraya yazın...")
        if prompt:
            # Kullanıcı mesajını ekle
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.markdown(f"<div class='chat-user'>{prompt}</div>", unsafe_allow_html=True)
            
            # Basit Cevaplama Mantığı
            q = prompt.upper()
            answer = "Bunu tam anlayamadım, ama filtreleri kullanabilirsin."
            
            # 1. İl Sorgusu
            found_cities = [c for c in df['İl'].unique() if c in q]
            if found_cities:
                city = found_cities[0]
                count = len(df[df['İl'] == city])
                answer = f"📍 **{city}** ilinde toplam **{count}** adet istasyon bulunuyor."
                
            # 2. Şirket Sorgusu
            found_comps = [c for c in df['Dağıtım Şirketi'].dropna().unique() if c in q]
            if found_comps:
                comp = found_comps[0]
                count = len(df[df['Dağıtım Şirketi'] == comp])
                answer = f"⛽ **{comp}** şirketinin toplam **{count}** bayisi var."
                
            # 3. Genel Sorular
            if "EN BÜYÜK" in q or "EN ÇOK" in q:
                top_city = df['İl'].value_counts().idxmax()
                top_comp = df['Dağıtım Şirketi'].value_counts().idxmax()
                answer = f"🏆 En çok istasyon **{top_city}** ilinde.\n👑 Pazar lideri ise **{top_comp}**."
                
            if "TOPLAM" in q:
                answer = f"📊 Veritabanında toplam **{len(df):,}** kayıt var."

            # Bot Cevabını Ekle
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.markdown(f"<div class='chat-bot'>{answer}</div>", unsafe_allow_html=True)

    # 12. CRM
    with tabs[11]:
        st.subheader("📝 CRM")
        df_crm = create_tab_filters(df, "t_crm")
        bayi = st.selectbox("Bayi", df_crm['Unvan'].unique())
        note = st.text_area("Not")
        if st.button("Kaydet"):
            ts = datetime.now().strftime("%d.%m %H:%M")
            if bayi not in st.session_state.crm_notes: st.session_state.crm_notes[bayi] = []
            st.session_state.crm_notes[bayi].append(f"[{ts}] {note}")
            st.success("OK")
        
        if st.session_state.crm_notes:
            for b, n in st.session_state.crm_notes.items():
                with st.expander(b):
                    for i in n: st.write(i)

    # 13. HAM VERİ
    with tabs[12]:
        st.subheader("📋 Ham Veri")
        df_raw = create_tab_filters(df, "t_raw")
        buffer = io.BytesIO()
        try:
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as w: df_raw.to_excel(w, index=False)
            st.download_button("📥 İndir", buffer.getvalue(), "Data.xlsx", "application/vnd.ms-excel")
        except: pass
        st.dataframe(df_raw.head(PREVIEW_ROW_LIMIT), use_container_width=True)

if __name__ == "__main__":
    main()
