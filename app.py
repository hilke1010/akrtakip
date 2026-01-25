import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import io
import time
import math
import streamlit.components.v1 as components 
from datetime import datetime, timedelta, date

# --- HARİTA KÜTÜPHANELERİ KONTROLÜ ---
try:
    import folium
    from streamlit_folium import st_folium
except ImportError:
    st.error("⚠️ Lütfen terminalden şu komutu çalıştırıp kütüphaneleri kur: pip install folium streamlit-folium")
    st.stop()

# --- 1. SAYFA VE GENEL AYARLAR ---
st.set_page_config(
    page_title="EPDK Akaryakıt Pazar Analizi",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- HAVERSINE (MESAFE HESAPLAMA) ---
def haversine(lat1, lon1, lat2, lon2):
    if any(x is None for x in [lat1, lon1, lat2, lon2]): return 99999
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# --- DOSYA TARİHİ ---
def get_file_last_modified(file_path):
    try:
        if not os.path.exists(file_path): return "DOSYA BULUNAMADI"
        timestamp = os.path.getmtime(file_path)
        utc_time = datetime.fromtimestamp(timestamp)
        turkey_time = utc_time + timedelta(hours=3)
        tr_months = {1: 'OCAK', 2: 'ŞUBAT', 3: 'MART', 4: 'NİSAN', 5: 'MAYIS', 6: 'HAZİRAN',
                     7: 'TEMMUZ', 8: 'AĞUSTOS', 9: 'EYLÜL', 10: 'EKİM', 11: 'KASIM', 12: 'ARALIK'}
        return f"{turkey_time.day} {tr_months.get(turkey_time.month)} {turkey_time.year}"
    except: return "TARİH ALINAMADI"

# --- GİRİŞ ANİMASYONU ---
def show_intro_animation():
    if 'intro_played' not in st.session_state: st.session_state['intro_played'] = False
    if st.session_state['intro_played']: return
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("""<div class='insight-box-danger'><b>⚠️ Sistem Yükleniyor...</b> Veriler ilçe bazlı işleniyor.</div>""", unsafe_allow_html=True)
        time.sleep(1)
    placeholder.empty()
    st.session_state['intro_played'] = True

# --- CSS ---
st.markdown("""
<style>
    .stMetric { background-color: #f0f2f6; border-left: 5px solid #2980b9; padding: 15px; border-radius: 5px; }
    .insight-box-danger { padding: 15px; border-radius: 8px; background-color: #f8d7da; border-left: 5px solid #dc3545; color: #721c24; margin-bottom: 10px; }
    .district-chip { display: inline-block; background-color: #f1f3f5; padding: 5px 10px; margin: 3px; border-radius: 15px; font-size: 0.9em; border: 1px solid #ddd; }
    .filter-container { background-color: #e3f2fd; padding: 15px; border-radius: 10px; border: 1px solid #bbdefb; margin-bottom: 15px; }
    button[data-testid="stTab"]:nth-child(14) p { color: #ff2b2b !important; font-weight: 800 !important; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 🌍 KOORDİNAT VERİTABANI (İL VE KRİTİK İLÇELER)
# -----------------------------------------------------------------------------
CITY_COORDINATES = {
    "ADANA": [37.0000, 35.3213], "ANKARA": [39.9334, 32.8597], "ANTALYA": [36.8969, 30.7133],
    "BURSA": [40.1885, 29.0610], "İSTANBUL": [41.0082, 28.9784], "İZMİR": [38.4189, 27.1287],
    "ZONGULDAK": [41.4564, 31.7987], "TRABZON": [41.0015, 39.7178], "SAMSUN": [41.2928, 36.3313],
    "KOCAELİ": [40.8533, 29.8815], "ESKİŞEHİR": [39.7767, 30.5206], "KONYA": [37.8667, 32.4833]
}

DISTRICT_COORDINATES = {
    # ZONGULDAK
    "ZONGULDAK_MERKEZ": [41.4564, 31.7987], "ZONGULDAK_KOZLU": [41.4292, 31.7456],
    "ZONGULDAK_KİLİMLİ": [41.4886, 31.8344], "ZONGULDAK_EREĞLİ": [41.2825, 31.4307],
    "ZONGULDAK_ÇAYCUMA": [41.4222, 32.0792], "ZONGULDAK_DEVREK": [41.2206, 31.9567],
    "ZONGULDAK_ALAPLI": [41.1764, 31.3853], "ZONGULDAK_GÖKÇEBEY": [41.3142, 32.1764],
    # İSTANBUL
    "İSTANBUL_KADIKÖY": [40.9819, 29.0254], "İSTANBUL_BEŞİKTAŞ": [41.0422, 29.0077],
    "İSTANBUL_ŞİŞLİ": [41.0529, 28.9814], "İSTANBUL_ÜSKÜDAR": [41.0267, 29.0167],
    "İSTANBUL_ESENYURT": [41.0343, 28.6801], "İSTANBUL_SARIYER": [41.1663, 29.0500],
    "İSTANBUL_ATAŞEHİR": [40.9936, 29.1128], "İSTANBUL_BAŞAKŞEHİR": [41.1070, 28.8055],
    # ANKARA
    "ANKARA_ÇANKAYA": [39.9208, 32.8541], "ANKARA_KEÇİÖREN": [39.9725, 32.8660],
    "ANKARA_YENİMAHALLE": [39.9723, 32.7959], "ANKARA_MAMAK": [39.9322, 32.9150],
    "ANKARA_ETİMESGUT": [39.9483, 32.6733], "ANKARA_SİNCAN": [39.9610, 32.5768],
    # İZMİR
    "İZMİR_KONAK": [38.4189, 27.1287], "İZMİR_BORNOVA": [38.4623, 27.2166],
    "İZMİR_KARŞIYAKA": [38.4578, 27.1122], "İZMİR_BUCA": [38.3867, 27.1706],
    "İZMİR_ÇEŞME": [38.3233, 26.3039],
}

# --- BÖLGE TANIMLARI ---
BOLGE_TANIMLARI = {
    "Orta Anadolu": ["ANKARA", "KONYA", "ESKİŞEHİR", "KAYSERİ", "KIRIKKALE", "AKSARAY", "KARAMAN", "NİĞDE", "NEVŞEHİR", "YOZGAT", "SİVAS", "ÇANKIRI", "KIRŞEHİR"],
    "Marmara": ["İSTANBUL", "BURSA", "KOCAELİ", "BALIKESİR", "TEKİRDAĞ", "SAKARYA", "ÇANAKKALE", "EDİRNE", "KIRKLARELİ", "YALOVA", "BİLECİK"],
    "Karadeniz": ["TRABZON", "SAMSUN", "ORDU", "ZONGULDAK", "RİZE", "TOKAT", "DÜZCE", "KASTAMONU", "GİRESUN", "AMASYA", "BOLU", "KARABÜK", "ÇORUM", "SİNOP", "BARTIN", "ARTVİN", "GÜMÜŞHANE", "BAYBURT"]
}

SABIT_DOSYA_ADI = "asatis.xlsx"

# --- YARDIMCI FONKSİYONLAR ---
def get_coordinates(row):
    """
    Satır için en iyi koordinatı bulur.
    1. Önce "İL_İLÇE" kombinasyonuna bakar.
    2. Bulamazsa "İL" merkezine bakar.
    3. Hiçbiri yoksa varsayılan (39, 35) döner.
    """
    il = str(row['İl']).upper().strip()
    ilce = str(row.get('İlçe', '')).upper().strip()
    key = f"{il}_{ilce}"
    
    if key in DISTRICT_COORDINATES: return DISTRICT_COORDINATES[key]
    elif il in CITY_COORDINATES: return CITY_COORDINATES[il]
    else: return [39.0, 35.0]

@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path): return None, None, None
    try:
        df = pd.read_excel(file_path)
        df.columns = [str(c).strip() for c in df.columns]
        if 'Dağıtıcı' in df.columns: df.rename(columns={'Dağıtıcı': 'Dağıtım Şirketi'}, inplace=True)
        
        # Karakter düzeltme
        for col in ['İl', 'İlçe']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.upper().str.strip().str.replace('i', 'İ').str.replace('ı', 'I')

        date_cols = [c for c in df.columns if 'Tarihi' in c]
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

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

        return df, target_col, start_col
    except Exception as e: return None, str(e), None

def create_tab_filters(df, key_prefix):
    st.markdown(f"<div class='filter-container'>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        sel_reg = st.selectbox("🌍 Bölge", ["Tümü"] + list(BOLGE_TANIMLARI.keys()), key=f"{key_prefix}_reg")
    filtered = df.copy()
    if sel_reg != "Tümü": filtered = filtered[filtered['İl'].isin(BOLGE_TANIMLARI[sel_reg])]
    with c2:
        sel_city = st.multiselect("🏢 İl", sorted(filtered['İl'].unique()), key=f"{key_prefix}_city")
    if sel_city: filtered = filtered[filtered['İl'].isin(sel_city)]
    with c3:
        dist_opts = sorted(filtered['İlçe'].unique()) if 'İlçe' in filtered.columns else []
        sel_dist = st.multiselect("📍 İlçe", dist_opts, key=f"{key_prefix}_dist")
    if sel_dist: filtered = filtered[filtered['İlçe'].isin(sel_dist)]
    with c4:
        comp_opts = sorted(filtered['Dağıtım Şirketi'].dropna().astype(str).unique())
        sel_comp = st.multiselect("⛽ Şirket", comp_opts, key=f"{key_prefix}_comp")
    if sel_comp: filtered = filtered[filtered['Dağıtım Şirketi'].isin(sel_comp)]
    st.markdown("</div>", unsafe_allow_html=True)
    return filtered

def show_details_table(dataframe, target_date_col):
    if dataframe is None or dataframe.empty:
        st.info("Kayıt bulunamadı.")
        return
    st.markdown(f"**📋 Listelenen Bayi:** {len(dataframe)}")
    cols = ['Unvan', 'İl', 'İlçe', 'Dağıtım Şirketi', target_date_col, 'Kalan_Gun']
    final_cols = [c for c in cols if c in dataframe.columns]
    
    # Tarih Formatlama
    disp_df = dataframe[final_cols].copy()
    if target_date_col in disp_df.columns:
        try: disp_df[target_date_col] = pd.to_datetime(disp_df[target_date_col]).dt.strftime('%d.%m.%Y')
        except: pass

    st.dataframe(disp_df, use_container_width=True, hide_index=True)

# --- ANA UYGULAMA ---
def main():
    show_intro_animation()
    data_result = load_data(SABIT_DOSYA_ADI)
    if data_result is None or data_result[0] is None:
        st.error("Veri yüklenemedi. Lütfen 'asatis.xlsx' dosyasını kontrol et.")
        st.stop()
    df, target_date_col, start_date_col = data_result
    
    # -------------------------------------------------------------------------
    # 🛠️ KOORDİNAT HESAPLAMA (AKILLI DAĞITIM - FIXED)
    # -------------------------------------------------------------------------
    if 'Enlem' not in df.columns:
        # 1. Her satır için Merkez Koordinatı Bul (İlçe veya İl)
        coords = df.apply(get_coordinates, axis=1)
        df['base_lat'] = [x[0] for x in coords]
        df['base_lon'] = [x[1] for x in coords]
        
        # 2. SAÇILIM (Micro-Jitter) - Denize uçurmayan küçük sapma (0.003 ~ 300 metre)
        np.random.seed(42)
        df['Enlem_Sim'] = df['base_lat'] + np.random.uniform(-0.003, 0.003, size=len(df))
        df['Boylam_Sim'] = df['base_lon'] + np.random.uniform(-0.003, 0.003, size=len(df))
        lat_col, lon_col = 'Enlem_Sim', 'Boylam_Sim'
    else:
        lat_col, lon_col = 'Enlem', 'Boylam'

    # --- ÜST PANEL ---
    st.markdown("### 🚀 Akaryakıt Pazar & Risk Analizi")
    st.info(f"📍 **Konum Modu:** {'Gerçek Koordinat' if lat_col == 'Enlem' else 'Akıllı İlçe Dağıtımı (Simülasyon)'}")
    
    # --- SEKMELER ---
    tabs = st.tabs([
        "📊 Bölgesel", "📅 Takvim", "⚡ Hızlı Analiz", "⚔️ Karşılaştırma", 
        "📄 İl Karnesi", "📍 İlçe Penetrasyonu", "📍 Yarıçap (Radar)", 
        "🚗 Rota", "🤖 Robo-Yönetici", "💸 Vergi Zincir", "🔍 Detaylı Arama", 
        "🔮 Simülasyon", "📡 Sözleşme Radar", "🚦 Trafik & İstasyon"
    ])

    # 1. BÖLGESEL
    with tabs[0]:
        df_tab1 = create_tab_filters(df, "tab1")
        if not df_tab1.empty:
            fig_map = px.scatter_mapbox(
                df_tab1, lat=lat_col, lon=lon_col, color="Dağıtım Şirketi",
                hover_name="Unvan", size_max=10, zoom=6, mapbox_style="open-street-map"
            )
            st.plotly_chart(fig_map, use_container_width=True)
            show_details_table(df_tab1, target_date_col)

    # 2. TAKVİM
    with tabs[1]:
        df_cal = create_tab_filters(df, "tab5")
        if 'Bitis_Yili' in df_cal.columns:
            yrs = sorted(df_cal['Bitis_Yili'].dropna().astype(int).unique())
            sel_yr = st.selectbox("Yıl", yrs)
            df_yr = df_cal[df_cal['Bitis_Yili'] == sel_yr]
            if not df_yr.empty:
                mon_counts = df_yr.groupby(['Bitis_Ayi_No', 'Bitis_Ayi']).size().reset_index(name='Adet').sort_values('Bitis_Ayi_No')
                fig_cal = px.bar(mon_counts, x='Bitis_Ayi', y='Adet', text='Adet')
                st.plotly_chart(fig_cal, use_container_width=True)
                show_details_table(df_yr, target_date_col)

    # 3. HIZLI ANALİZ
    with tabs[2]:
        df_tab2 = create_tab_filters(df, "tab2")
        if not df_tab2.empty:
            c1, c2 = st.columns(2)
            c1.metric("Toplam Bayi", len(df_tab2))
            fig_pie = px.pie(df_tab2['Dağıtım Şirketi'].value_counts().reset_index(), values='count', names='Dağıtım Şirketi')
            c2.plotly_chart(fig_pie, use_container_width=True)

    # 4. KARŞILAŞTIRMA
    with tabs[3]:
        df_tab3 = create_tab_filters(df, "tab3")
        comps = sorted(df['Dağıtım Şirketi'].unique())
        c1, c2 = st.columns(2)
        ca = c1.selectbox("Şirket A", comps, index=0)
        cb = c2.selectbox("Şirket B", comps, index=1 if len(comps)>1 else 0)
        df_vs = df_tab3[df_tab3['Dağıtım Şirketi'].isin([ca, cb])]
        if not df_vs.empty:
            fig_vs = px.bar(df_vs.groupby(['İl','Dağıtım Şirketi']).size().reset_index(name='Adet'), x='İl', y='Adet', color='Dağıtım Şirketi', barmode='group')
            st.plotly_chart(fig_vs, use_container_width=True)

    # 5. İL KARNESİ
    with tabs[4]:
        rep_city = st.selectbox("İl Seç:", sorted(df['İl'].unique()))
        city_df = df[df['İl'] == rep_city]
        st.metric("Toplam İstasyon", len(city_df))
        st.plotly_chart(px.pie(city_df['Dağıtım Şirketi'].value_counts().reset_index(), values='count', names='Dağıtım Şirketi'), use_container_width=True)
        show_details_table(city_df, target_date_col)

    # 6. İLÇE PENETRASYONU
    with tabs[5]:
        df_dist = create_tab_filters(df, "tab7")
        if not df_dist.empty:
            cnt = df_dist['İlçe'].value_counts().reset_index()
            cnt.columns = ['İlçe', 'Adet']
            st.plotly_chart(px.bar(cnt.head(20), x='Adet', y='İlçe', orientation='h'), use_container_width=True)

    # 7. YARIÇAP (RADAR)
    with tabs[6]:
        st.subheader("📍 Yarıçap (Radar)")
        st.info("İlçe merkezli dağıtım sayesinde mesafe ölçümü artık daha tutarlı.")
        df_radar = create_tab_filters(df, "radar")
        if not df_radar.empty:
            center_station = st.selectbox("Merkez Bayi:", sorted(df_radar['Unvan'].unique()))
            radius = st.slider("Mesafe (km)", 1, 50, 5)
            
            center_row = df_radar[df_radar['Unvan'] == center_station].iloc[0]
            pool = df[df['İl'] == center_row['İl']].copy()
            pool['Mesafe'] = pool.apply(lambda r: haversine(center_row[lat_col], center_row[lon_col], r[lat_col], r[lon_col]), axis=1)
            
            nearby = pool[pool['Mesafe'] <= radius].sort_values('Mesafe')
            st.write(f"**{radius} km** içinde **{len(nearby)}** istasyon var.")
            
            nearby['Tip'] = np.where(nearby['Unvan'] == center_station, 'MERKEZ', 'RAKİP')
            fig_rad = px.scatter_mapbox(nearby, lat=lat_col, lon=lon_col, color='Tip', size_max=15, zoom=11, mapbox_style="open-street-map")
            st.plotly_chart(fig_rad, use_container_width=True)
            show_details_table(nearby, target_date_col)

    # 8. ROTA PLANLAYICI
    with tabs[7]:
        df_route = create_tab_filters(df, "tab_route_new")
        if not df_route.empty:
            stations_to_visit = st.multiselect("Ziyaret Listesi Oluştur:", df_route['Unvan'].unique())
            if len(stations_to_visit) > 1:
                visit_df = df_route[df_route['Unvan'].isin(stations_to_visit)].copy()
                ordered = [visit_df.iloc[0]] # Basit sıralama
                st.info("Rota sıralaması (Basit): " + " -> ".join([x['Unvan'] for x in ordered]))
                fig_rt = px.line_mapbox(visit_df, lat=lat_col, lon=lon_col, zoom=9, mapbox_style="open-street-map")
                st.plotly_chart(fig_rt, use_container_width=True)

    # 9. ROBO-YÖNETİCİ
    with tabs[8]:
        st.info("GÜZEL ENERJİ AKARYAKIT A.Ş. Perspektifinden Analiz")
        df_robo = create_tab_filters(df, "robo")
        if not df_robo.empty:
            hero_count = len(df_robo[df_robo['Dağıtım Şirketi'] == "GÜZEL ENERJİ AKARYAKIT ANONİM ŞİRKETİ"])
            st.markdown(f"""<div class="robo-card"><h4>🦁 Bizim Durumumuz</h4>Toplam <b>{hero_count}</b> istasyonumuz var.</div>""", unsafe_allow_html=True)

    # 10. VERGİ ZİNCİR
    with tabs[9]:
        df_chain = create_tab_filters(df, "chain")
        tax_col = next((c for c in df_chain.columns if "VERGI" in c.upper() or "VKN" in c.upper()), None)
        if tax_col:
            vkn_counts = df_chain[tax_col].value_counts()
            big_bosses = vkn_counts[vkn_counts > 8].index
            st.dataframe(df_chain[df_chain[tax_col].isin(big_bosses)][[tax_col, 'Unvan', 'İl']].sort_values(tax_col), use_container_width=True)
        else:
            st.warning("Vergi No sütunu bulunamadı.")

    # 11. DETAYLI ARAMA
    with tabs[10]:
        search_term = st.text_input("Bayi Ara:", "")
        if search_term:
            res = df[df['Unvan'].str.contains(search_term, case=False, na=False)]
            show_details_table(res, target_date_col)

    # 12. SİMÜLASYON
    with tabs[11]:
        st.info("Bayi kazanım simülasyonu.")

    # 13. SÖZLEŞME RADAR
    with tabs[12]:
        if 'Sozlesme_Suresi_Gun' in df.columns:
            risk = df[(df['Sozlesme_Suresi_Gun'] < 90) & (df['Sozlesme_Suresi_Gun'] >= 0)]
            st.error(f"{len(risk)} Kritik Bayi")
            show_details_table(risk, target_date_col)

    # 14. CANLI TRAFİK (FOLIUM - FINAL FIXED)
    with tabs[13]:
        st.subheader("🚦 Canlı Trafik & İstasyonlar")
        
        c_filter1, c_filter2 = st.columns([1, 3])
        with c_filter1:
            trafik_il_sec = st.selectbox("İl Seç:", ["TÜMÜ"] + sorted(df['İl'].dropna().unique().tolist()))
        
        if trafik_il_sec != "TÜMÜ":
            map_df = df[df['İl'] == trafik_il_sec].copy()
            zoom_lvl = 11
        else:
            map_df = df.copy()
            zoom_lvl = 6

        if not map_df.empty:
            center_lat = map_df[lat_col].mean()
            center_lon = map_df[lon_col].mean()
            
            m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_lvl)
            folium.TileLayer('https://mt1.google.com/vt/lyrs=m,traffic&x={x}&y={y}&z={z}', attr='Google', name='Trafik').add_to(m)

            # Limit koyalım kasmasın (İlk 2000 kayıt)
            for idx, row in map_df.head(2000).iterrows():
                icon_color = 'red' if row.get('Kalan_Gun', 999) < 90 else 'blue'
                html = f"""
                <div style='font-family:sans-serif; width:180px;'>
                    <b>{row['Unvan']}</b><br>
                    <span style='color:gray; font-size:0.9em'>{row['İlçe']}</span><br>
                    <hr style='margin:3px 0'>
                    <b>Kalan:</b> <span style='color:{icon_color}'>{row.get('Kalan_Gun','-')} gün</span>
                </div>
                """
                # CLUSTER YOK - DİREKT MARKER
                folium.Marker(
                    [row[lat_col], row[lon_col]],
                    popup=folium.Popup(html, max_width=200),
                    tooltip=row['Unvan'],
                    icon=folium.Icon(color=icon_color, icon='gas-pump', prefix='fa')
                ).add_to(m)

            st_folium(m, width=1200, height=600)
        else:
            st.warning("Veri yok.")

if __name__ == "__main__":
    main()
