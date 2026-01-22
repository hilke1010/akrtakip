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

# --- DOSYA TARİHİ HESAPLAMA ---
def get_file_last_modified(file_path):
    try:
        if not os.path.exists(file_path):
            return "DOSYA BULUNAMADI"
        timestamp = os.path.getmtime(file_path)
        utc_time = datetime.datetime.utcfromtimestamp(timestamp)
        turkey_time = utc_time + datetime.timedelta(hours=3)
        tr_months = {1: 'OCAK', 2: 'ŞUBAT', 3: 'MART', 4: 'NİSAN', 5: 'MAYIS', 6: 'HAZİRAN',
                     7: 'TEMMUZ', 8: 'AĞUSTOS', 9: 'EYLÜL', 10: 'EKİM', 11: 'KASIM', 12: 'ARALIK'}
        month_name = tr_months.get(turkey_time.month, "")
        return f"{turkey_time.day} {month_name} {turkey_time.year} SAAT {turkey_time.strftime('%H:%M')}"
    except:
        return "TARİH ALINAMADI"

# --- CAFCAFLI YÜKLEME ANİMASYONU ---
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
            }
            @keyframes gradientBG { 0% {background-position: 0% 50%;} 50% {background-position: 100% 50%;} 100% {background-position: 0% 50%;} }
            .intro-title { font-size: 5rem; font-weight: 900; text-align: center; }
            .loading-bar { width: 350px; height: 8px; background: #fff; transform-origin: left; animation: load 2.5s forwards; }
            @keyframes load { 0% { transform: scaleX(0); } 100% { transform: scaleX(1); } }
        </style>
        <div class="intro-overlay">
            <div style="font-size:8rem;">⛽</div>
            <h1 class="intro-title">AKARYAKIT<br>ANALİZ SİSTEMİ</h1>
            <div class="loading-bar"></div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(2.5)
    placeholder.empty()
    st.session_state['intro_played'] = True

# --- PERFORMANS VE SABİTLER ---
MAX_ROW_DISPLAY = 1000  
SABIT_DOSYA_ADI = "asatis.xlsx"
PREVIEW_ROW_LIMIT = 100

# --- CSS ---
st.markdown("""
<style>
    .stMetric { background-color: #f0f2f6; border-left: 5px solid #2980b9; padding: 15px; border-radius: 5px; }
    .insight-box-success { padding: 15px; border-radius: 8px; background-color: #d4edda; border-left: 5px solid #28a745; margin-bottom: 10px; }
    .insight-box-warning { padding: 15px; border-radius: 8px; background-color: #fff3cd; border-left: 5px solid #ffc107; margin-bottom: 10px; }
    .insight-box-danger { padding: 15px; border-radius: 8px; background-color: #f8d7da; border-left: 5px solid #dc3545; margin-bottom: 10px; }
    .insight-box-info { padding: 15px; border-radius: 8px; background-color: #d1ecf1; border-left: 5px solid #17a2b8; margin-bottom: 10px; }
    .district-chip { display: inline-block; background-color: #f1f3f5; padding: 5px 10px; margin: 3px; border-radius: 15px; font-size: 0.9em; border: 1px solid #ddd; }
    .warning-box { padding: 1rem; background-color: #ffeba0; border-left: 6px solid #ffa500; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# --- KOORDİNATLAR ---
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

# --- DATA LOADING ---
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

def show_details_table(dataframe, target_date_col):
    if dataframe is None or dataframe.empty:
        st.info("Kayıt bulunamadı.")
        return
    st.markdown(f"**📋 Kayıt Sayısı:** {len(dataframe)}")
    display_df = dataframe.head(MAX_ROW_DISPLAY).copy()
    date_cols = [c for c in display_df.columns if "Tarihi" in c]
    for c in date_cols: display_df[c] = pd.to_datetime(display_df[c]).dt.strftime('%d.%m.%Y')
    st.dataframe(display_df, use_container_width=True, hide_index=True)

# --- FİLTRE MOTORU (HER SAYFA İÇİN AYRI) ---
def local_filters(df_base, key_suffix):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        reg = st.selectbox("🌍 Bölge", ["Tümü"] + list(BOLGE_TANIMLARI.keys()), key=f"reg_{key_suffix}")
    
    temp_df = df_base.copy()
    if reg != "Tümü": temp_df = temp_df[temp_df['İl'].isin(BOLGE_TANIMLARI[reg])]
    
    with c2:
        cities = sorted(temp_df['İl'].unique().tolist())
        sel_cities = st.multiselect("🏢 Şehir", cities, key=f"city_{key_suffix}")
    
    if sel_cities: temp_df = temp_df[temp_df['İl'].isin(sel_cities)]
    
    with c3:
        districts = sorted(temp_df['İlçe'].unique().tolist())
        sel_dist = st.multiselect("📍 İlçe", districts, key=f"dist_{key_suffix}")
    
    if sel_dist: temp_df = temp_df[temp_df['İlçe'].isin(sel_dist)]
    
    with c4:
        comps = sorted(temp_df['Dağıtım Şirketi'].dropna().unique().tolist())
        sel_comp = st.multiselect("⛽ Şirket", comps, key=f"comp_{key_suffix}")
    
    if sel_comp: temp_df = temp_df[temp_df['Dağıtım Şirketi'].isin(sel_comp)]
    
    return temp_df

# --- ANA UYGULAMA ---
def main():
    show_intro_animation()
    df, target_date_col, start_date_col = load_data(SABIT_DOSYA_ADI)
    if df is None: st.error("Veri yüklenemedi"); st.stop()
    
    file_date_str = get_file_last_modified(SABIT_DOSYA_ADI)

    with st.sidebar:
        st.success(f"🔄 **GÜNCELLEME:**\n\n{file_date_str}")
        st.info("📧 kerim.aksu@milangaz.com.tr")
        st.markdown("---")
        st.header("🔗 Diğer Uygulamalar")
        st.markdown("[📊 EPDK LPG Raporu](https://pazarpayi.streamlit.app/)")
        st.markdown("[📰 Haber Aracı](https://newslpg.streamlit.app/)")
        st.markdown("[📱 Mobil Hesaplayıcı](https://lpg2026.streamlit.app/)")

    st.title("🚀 Akaryakıt Pazar Analiz Sistemi")
    
    tab_overview, tab_machine, tab_compare, tab_sim, tab_calendar, tab_radar, tab_ilce, tab_report, tab_crm, tab_data = st.tabs([
        "📊 Bölgesel", "🤖 Makine Analizi", "⚔️ Karşılaştırma", "🔮 Simülasyon", "📅 Takvim", "📡 Radar", "📍 İlçe", "📄 Karne", "📝 CRM", "📋 Veri"
    ])

    # 1. BÖLGESEL
    with tab_overview:
        df_f = local_filters(df, "ov")
        st.divider()
        col1, col2, col3 = st.columns(3)
        col1.metric("İstasyon", len(df_f))
        col2.metric("Acil (90 Gün)", len(df_f[df_f['Kalan_Gun']<90]))
        col3.metric("Dağıtıcı", df_f['Dağıtım Şirketi'].nunique())
        
        map_data = df_f['İl'].value_counts().reset_index()
        map_data.columns = ['İl', 'Adet']
        map_data['lat'] = map_data['İl'].map(lambda x: CITY_COORDINATES.get(x, [None, None])[0])
        map_data['lon'] = map_data['İl'].map(lambda x: CITY_COORDINATES.get(x, [None, None])[1])
        fig_map = px.scatter_mapbox(map_data.dropna(), lat="lat", lon="lon", size="Adet", color="Adet", hover_name="İl", mapbox_style="open-street-map", zoom=4.5)
        st.plotly_chart(fig_map, use_container_width=True)
        show_details_table(df_f, target_date_col)

    # 2. MAKİNE ANALİZİ
    with tab_machine:
        # Şirket filtresiz hali üzerinden analiz yapacağı için local_filters yerine özel yapı
        c1, c2, c3 = st.columns(3)
        with c1: m_reg = st.selectbox("🌍 Bölge", ["Tümü"] + list(BOLGE_TANIMLARI.keys()), key="m_reg")
        m_df = df.copy()
        if m_reg != "Tümü": m_df = m_df[m_df['İl'].isin(BOLGE_TANIMLARI[m_reg])]
        with c2: 
            m_cities = st.multiselect("🏢 Şehir", sorted(m_df['İl'].unique()), key="m_city")
            if m_cities: m_df = m_df[m_df['İl'].isin(m_cities)]
        
        my_comp = "GÜZEL ENERJİ AKARYAKIT ANONİM ŞİRKETİ"
        my_df = m_df[m_df['Dağıtım Şirketi'] == my_comp]
        
        st.subheader("🤖 Stratejik Çıkarımlar")
        if not m_df.empty:
            if not my_df.empty:
                st.markdown(f"<div class='insight-box-success'><b>🏆 Hakimiyet:</b> En güçlü olduğunuz il: {my_df['İl'].value_counts().idxmax()}</div>", unsafe_allow_html=True)
            
            missing = sorted(list(set(m_df['İlçe'].unique()) - set(my_df['İlçe'].unique())))
            st.markdown(f"<div class='insight-box-warning'><b>🚀 Fırsat:</b> Bu seçimde hiç olmadığınız {len(missing)} ilçe var.</div>", unsafe_allow_html=True)
            
            p_val = [len(my_df), len(m_df)-len(my_df)]
            fig_p = px.pie(names=['GÜZEL ENERJİ', 'DİĞER'], values=p_val, hole=0.5, title="Pazar Payı")
            st.plotly_chart(fig_p)

    # 3. KARŞILAŞTIRMA
    with tab_compare:
        df_vs_base = local_filters(df, "vs")
        st.divider()
        comps = sorted(df_vs_base['Dağıtım Şirketi'].dropna().unique().tolist())
        if len(comps) > 1:
            v1, v2 = st.columns(2)
            c_a = v1.selectbox("Şirket A", comps, index=0)
            c_b = v2.selectbox("Şirket B", comps, index=1)
            
            res_a = df_vs_base[df_vs_base['Dağıtım Şirketi']==c_a]
            res_b = df_vs_base[df_vs_base['Dağıtım Şirketi']==c_b]
            
            k1, k2 = st.columns(2)
            k1.metric(c_a, len(res_a))
            k2.metric(c_b, len(res_b), delta=len(res_b)-len(res_a))
            
            vs_data = df_vs_base[df_vs_base['Dağıtım Şirketi'].isin([c_a, c_b])].groupby(['İl', 'Dağıtım Şirketi']).size().reset_index(name='Adet')
            st.plotly_chart(px.bar(vs_data, x='İl', y='Adet', color='Dağıtım Şirketi', barmode='group'))

    # 4. SİMÜLASYON
    with tab_sim:
        df_s = local_filters(df, "sim")
        st.divider()
        my_c = "GÜZEL ENERJİ AKARYAKIT ANONİM ŞİRKETİ"
        target_c = st.selectbox("Hedef Rakip", [c for c in sorted(df_s['Dağıtım Şirketi'].unique()) if c != my_c])
        oran = st.slider("Kazanma Oranı (%)", 0, 100, 10)
        
        curr = len(df_s[df_s['Dağıtım Şirketi']==my_c])
        gain = int(len(df_s[df_s['Dağıtım Şirketi']==target_c]) * oran / 100)
        st.metric("Yeni Hedef Bayi Sayısı", curr + gain, delta=f"+{gain}")

    # 5. TAKVİM
    with tab_calendar:
        df_c = local_filters(df, "cal")
        yrs = sorted(df_c['Bitis_Yili'].dropna().unique().astype(int))
        if yrs:
            sel_y = st.selectbox("Yıl", yrs)
            cal_data = df_c[df_c['Bitis_Yili']==sel_y]['Bitis_Ayi'].value_counts().reindex(['Ocak','Şubat','Mart','Nisan','Mayıs','Haziran','Temmuz','Ağustos','Eylül','Ekim','Kasım','Aralık']).fillna(0)
            st.plotly_chart(px.bar(cal_data, title=f"{sel_y} Bitiş Takvimi"))

    # 6. RADAR
    with tab_radar:
        df_r = local_filters(df, "rad")
        radar = df_r[df_r['Sozlesme_Suresi_Gun']<90]
        st.subheader("📡 90 Günden Kısa Sözleşmeler")
        show_details_table(radar, target_date_col)

    # 7. İLÇE
    with tab_ilce:
        df_i = local_filters(df, "dist_p")
        if not df_i.empty:
            st.plotly_chart(px.bar(df_i['İlçe'].value_counts().head(20), orientation='h', title="İlçe Yoğunluğu"))

    # 8. KARNE
    with tab_report:
        sel_city = st.selectbox("İl Seçin", sorted(df['İl'].unique()), key="karne_city")
        c_df = df[df['İl']==sel_city]
        st.header(f"📄 {sel_city} Pazar Karnesi")
        r1, r2, r3 = st.columns(3)
        r1.metric("Toplam", len(c_df))
        r2.metric("Güzel Enerji", len(c_df[c_df['Dağıtım Şirketi']=="GÜZEL ENERJİ AKARYAKIT ANONİM ŞİRKETİ"]))
        r3.metric("Lider", c_df['Dağıtım Şirketi'].value_counts().idxmax())
        st.plotly_chart(px.pie(c_df['Dağıtım Şirketi'].value_counts().head(5), names=c_df['Dağıtım Şirketi'].value_counts().head(5).index, title="Pazar Payı"))

    # 9. CRM
    with tab_crm:
        df_crm = local_filters(df, "crm")
        sel_bayi = st.selectbox("Bayi Seç", sorted(df_crm['Unvan'].unique()))
        not_al = st.text_area("Notunuz")
        if st.button("Kaydet"): st.success(f"{sel_bayi} için not kaydedildi (Simüle edildi)")

    # 10. VERİ
    with tab_data:
        df_v = local_filters(df, "raw")
        st.dataframe(df_v.head(PREVIEW_ROW_LIMIT))
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_v.to_excel(writer, index=False)
        st.download_button("📥 Excel İndir", buffer.getvalue(), "bayi_listesi.xlsx")

if __name__ == "__main__":
    main()
