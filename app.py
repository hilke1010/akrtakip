import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import numpy as np
import os
import io

# --- 1. SAYFA VE GENEL AYARLAR ---
st.set_page_config(
    page_title="EPDK Akaryakıt Pazar Analizi",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    .block-container { padding-top: 2rem; }
    /* CRM Notları için stil */
    .crm-box {
        background-color: #fff9c4;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #fbc02d;
        margin-bottom: 10px;
    }
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

# --- CRM İÇİN SESSION STATE BAŞLATMA ---
if 'crm_notes' not in st.session_state:
    st.session_state.crm_notes = {}  # { 'Bayi Unvanı': 'Not' }

# --- 6. EXCEL VERİ YÜKLEME ---
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path):
        return None, None
    try:
        df = pd.read_excel(file_path)
        df.columns = [c.strip() for c in df.columns]

        if 'Dağıtıcı' in df.columns and 'Dağıtım Şirketi' not in df.columns:
            df.rename(columns={'Dağıtıcı': 'Dağıtım Şirketi'}, inplace=True)

        date_cols = ['Lisans Başlangıç Tarihi', 'Lisans Bitiş Tarihi',
                     'Dağıtıcı ile Yapılan Sözleşme Başlangıç Tarihi',
                     'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi']

        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

        target_col = 'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi'
        if target_col not in df.columns:
            target_col = 'Lisans Bitiş Tarihi'

        today = pd.to_datetime(datetime.date.today())

        if target_col in df.columns:
            df['Kalan_Gun'] = (df[target_col] - today).dt.days
            df['Bitis_Yili'] = df[target_col].dt.year
            df['Bitis_Ayi'] = df[target_col].dt.month_name(locale='Turkish' if 'Turkish' in datetime.date.today().strftime('%B') else None)
            df['Bitis_Ayi_No'] = df[target_col].dt.month
        else:
            df['Kalan_Gun'] = np.nan
            df['Bitis_Yili'] = np.nan
            df['Bitis_Ayi'] = np.nan
            df['Bitis_Ayi_No'] = np.nan

        def get_risk(days):
            if pd.isna(days): return "Bilinmiyor"
            if days < 0: return "SÜRESİ DOLDU 🚨"
            if days < 90: return "KRİTİK (<3 Ay) ⚠️"
            if days < 180: return "YAKLAŞIYOR (<6 Ay) ⏳"
            return "GÜVENLİ ✅"

        df['Risk_Durumu'] = df['Kalan_Gun'].apply(get_risk)

        if 'İl' in df.columns: 
            df['İl'] = df['İl'].astype(str).str.upper().str.replace('i', 'İ').str.replace('ı', 'I')
        if 'İlçe' in df.columns: 
            df['İlçe'] = df['İlçe'].astype(str).str.upper().str.replace('i', 'İ').str.replace('ı', 'I')

        return df, target_col
    except Exception as e:
        st.error(f"Excel okuma hatası: {e}")
        return None, None


# --- YARDIMCI FONKSİYON: DETAY TABLOSU ---
def show_details_table(dataframe, target_date_col):
    if dataframe.empty:
        st.info("Seçilen kriterlere uygun kayıt bulunamadı.")
        return

    cols = ['Unvan', 'İl', 'İlçe', 'Dağıtım Şirketi', target_date_col, 'Kalan_Gun', 'Risk_Durumu']
    final_cols = [c for c in cols if c in dataframe.columns]
    
    display_df = dataframe[final_cols].copy()
    if target_date_col in display_df.columns:
        display_df[target_date_col] = display_df[target_date_col].dt.strftime('%d.%m.%Y')

    display_df = display_df.sort_values('Kalan_Gun')

    def highlight_risk(val):
        if val < 0: color = '#ffcccc' 
        elif val < 90: color = '#ffe5cc' 
        elif val < 180: color = '#ffffcc' 
        else: color = '' 
        return f'background-color: {color}'

    st.markdown(f"**📋 Listelenen Bayi Sayısı:** {len(display_df)}")
    
    st.dataframe(
        display_df.style.map(highlight_risk, subset=['Kalan_Gun']),
        use_container_width=True,
        hide_index=True
    )


def main():
    # --- VERİ ÇEKME ---
    df, target_date_col = load_data(SABIT_DOSYA_ADI)

    if df is None:
        st.warning(f"⚠️ '{SABIT_DOSYA_ADI}' dosyası bulunamadı. Lütfen proje klasörüne ekleyin.")
        st.stop()

    # --- SIDEBAR ---
    with st.sidebar:
        st.info("🕒 Not: Veriler her gün saat 10:00'da yenilenmektedir.")
        st.markdown("---")
        
        st.title("🔍 Filtre Paneli")

        # Bölge Filtresi
        region_options = ["Tümü"] + list(BOLGE_TANIMLARI.keys())
        selected_region = st.selectbox("🌍 Bölge Seç", region_options)

        if selected_region != "Tümü":
            target_cities = BOLGE_TANIMLARI[selected_region]
            df_for_sidebar = df[df['İl'].isin(target_cities)]
        else:
            df_for_sidebar = df.copy()

        # İl Filtresi
        if 'İl' in df_for_sidebar.columns:
            all_cities = sorted(df_for_sidebar['İl'].unique().tolist())
            selected_cities = st.multiselect("🏢 Şehir Seç", all_cities)
        else:
            selected_cities = []

        # İlçe Filtresi
        if 'İlçe' in df_for_sidebar.columns:
            if selected_cities:
                filtered_districts = sorted(df_for_sidebar[df_for_sidebar['İl'].isin(selected_cities)]['İlçe'].unique().tolist())
            else:
                filtered_districts = sorted(df_for_sidebar['İlçe'].unique().tolist())
            selected_districts = st.multiselect("📍 İlçe Seç", filtered_districts)
        else:
            selected_districts = []

        # Şirket Filtresi
        if 'Dağıtım Şirketi' in df.columns:
            all_companies = sorted(df['Dağıtım Şirketi'].dropna().unique().tolist())
            selected_companies = st.multiselect("⛽ Şirket Seç", all_companies)
        else:
            selected_companies = []
            st.warning("Excel'de 'Dağıtım Şirketi' sütunu bulunamadı.")

        st.markdown("---")
        st.header("📧 İletişim")
        st.info("kerim.aksu@milangaz.com.tr")

    # --- FİLTRELEME İŞLEMİ ---
    df_filtered = df.copy()

    if selected_region != "Tümü":
        region_cities = BOLGE_TANIMLARI[selected_region]
        df_filtered = df_filtered[df_filtered['İl'].isin(region_cities)]

    if selected_cities: df_filtered = df_filtered[df_filtered['İl'].isin(selected_cities)]
    if selected_districts: df_filtered = df_filtered[df_filtered['İlçe'].isin(selected_districts)]
    if selected_companies: df_filtered = df_filtered[df_filtered['Dağıtım Şirketi'].isin(selected_companies)]

    # --- BAŞLIK VE KPI ---
    st.title("🚀 Akaryakıt Pazar & Risk Analizi")
    if selected_region != "Tümü":
        st.caption(f"📍 Şu anda **{selected_region}** verileri görüntüleniyor.")

    # KPI KISMI
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam İstasyon", f"{len(df_filtered):,}")

    acil_durum = len(df_filtered[df_filtered['Kalan_Gun'] < 90])
    c2.metric("Acil Sözleşme", acil_durum, delta="Acil Yenileme", delta_color="inverse")

    if 'Dağıtım Şirketi' in df_filtered.columns:
        aktif_dagitici = df_filtered['Dağıtım Şirketi'].nunique()
    else:
        aktif_dagitici = 0
    c3.metric("Aktif Dağıtıcı", aktif_dagitici)

    st.divider()

    # --- SEKMELER ---
    tab_overview, tab_compare, tab_sim, tab_calendar, tab_ilce, tab_crm, tab_data = st.tabs([
        "📊 Bölgesel & Durum",
        "⚔️ Karşılaştırma (Vs.)", 
        "🔮 Simülasyon",         
        "📅 Takvim", 
        "📍 Penetrasyon",
        "📝 CRM Lite",           
        "📋 Ham Veri"
    ])

    # 1. BÖLGESEL HARİTA & DURUM
    with tab_overview:
        st.subheader("🗺️ Bölgesel Yoğunluk Haritası")
        
        if not df_filtered.empty:
            map_data = df_filtered['İl'].value_counts().reset_index()
            map_data.columns = ['İl', 'Adet']
            map_data['lat'] = map_data['İl'].map(lambda x: CITY_COORDINATES.get(x, [None, None])[0])
            map_data['lon'] = map_data['İl'].map(lambda x: CITY_COORDINATES.get(x, [None, None])[1])
            map_data = map_data.dropna(subset=['lat', 'lon'])

            if not map_data.empty:
                fig_map = px.scatter_mapbox(
                    map_data, lat="lat", lon="lon", size="Adet", color="Adet",
                    hover_name="İl", size_max=35, zoom=5 if selected_region == "Tümü" else 6, 
                    mapbox_style="open-street-map", color_continuous_scale=px.colors.sequential.Bluered
                )
                if selected_region != "Tümü":
                    center_lat, center_lon = map_data['lat'].mean(), map_data['lon'].mean()
                    fig_map.update_layout(mapbox_center={"lat": center_lat, "lon": center_lon})
                else:
                    fig_map.update_layout(mapbox_center={"lat": 39.0, "lon": 35.0}, mapbox_zoom=4.8)
                
                fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                st.plotly_chart(fig_map, use_container_width=True)

            st.divider()
            st.subheader("📊 İstatistikler")
            st.info("👇 **İpucu:** Grafikteki çubuklara tıklayarak detaylı listeyi görebilirsiniz.")

            c_bar, c_pie1, c_pie2 = st.columns([2, 1, 1])
            
            with c_bar:
                fig_city = px.bar(map_data, x='İl', y='Adet', text='Adet', title="Şehir Sıralaması",
                                  color='Adet', color_continuous_scale='Blues')
                st.plotly_chart(fig_city, use_container_width=True, on_select="rerun", key="overview_bar_chart")
            
            with c_pie1:
                city_pie_data = df_filtered['İl'].value_counts().reset_index()
                city_pie_data.columns = ['İl', 'Adet']
                if len(city_pie_data) > 10:
                    top_10 = city_pie_data.iloc[:10]
                    others = pd.DataFrame({'İl': ['DİĞER'], 'Adet': [city_pie_data.iloc[10:]['Adet'].sum()]})
                    city_pie_data = pd.concat([top_10, others])
                
                fig_city_pie = px.pie(city_pie_data, values='Adet', names='İl', hole=0.4, title="Şehir Dağılımı (%)")
                st.plotly_chart(fig_city_pie, use_container_width=True)

            with c_pie2:
                risk_counts = df_filtered['Risk_Durumu'].value_counts().reset_index()
                risk_counts.columns = ['Risk_Durumu', 'Adet']
                fig_risk_pie = px.pie(risk_counts, values='Adet', names='Risk_Durumu', hole=0.4,
                                 title="Risk Dağılımı (%)",
                                 color_discrete_map={"SÜRESİ DOLDU 🚨": "red", "KRİTİK (<3 Ay) ⚠️": "orange",
                                                     "YAKLAŞIYOR (<6 Ay) ⏳": "#FFD700", "GÜVENLİ ✅": "green"})
                st.plotly_chart(fig_risk_pie, use_container_width=True)

            # Liste Gösterimi
            selected_chart_city = None
            if st.session_state.get("overview_bar_chart") and st.session_state["overview_bar_chart"]['selection']['points']:
                selected_chart_city = st.session_state["overview_bar_chart"]['selection']['points'][0]['x']
                st.success(f"📌 **{selected_chart_city}** detayları listeleniyor:")
                filtered_table = df_filtered[df_filtered['İl'] == selected_chart_city]
            else:
                filtered_table = df_filtered
            show_details_table(filtered_table, target_date_col)

    # 2. KARŞILAŞTIRMA (VS.) MODU (GÜNCELLENDİ)
    with tab_compare:
        st.subheader("⚔️ Head-to-Head Rakip Analizi")
        st.markdown("İki farklı dağıtım şirketini seçerek seçilen bölgedeki (veya tüm Türkiye'deki) güçlerini kıyaslayın.")
        
        comp_list = sorted(df['Dağıtım Şirketi'].dropna().unique().tolist())
        
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            comp_a = st.selectbox("1. Şirket (Taraf A)", comp_list, index=0)
        with col_sel2:
            def_idx = 1 if len(comp_list) > 1 else 0
            comp_b = st.selectbox("2. Şirket (Taraf B)", comp_list, index=def_idx)

        # Verileri Filtrele
        if selected_region != "Tümü":
            base_df = df[df['İl'].isin(BOLGE_TANIMLARI[selected_region])]
        else:
            base_df = df.copy()

        df_a = base_df[base_df['Dağıtım Şirketi'] == comp_a]
        df_b = base_df[base_df['Dağıtım Şirketi'] == comp_b]

        # Metrikler
        c_k1, c_k2, c_k3 = st.columns(3)
        
        # 1. Metrik: Toplam İstasyon
        c_k1.markdown(f"### ⛽ Toplam İstasyon")
        c_k1.metric(f"{comp_a}", len(df_a))
        c_k1.metric(f"{comp_b}", len(df_b), delta=len(df_b)-len(df_a), delta_color="off")

        # 2. Metrik: En Güçlü ve En Zayıf Şehir (GÜNCELLENDİ)
        # En Güçlü
        top_city_a = df_a['İl'].value_counts().idxmax() if not df_a.empty else "-"
        top_city_b = df_b['İl'].value_counts().idxmax() if not df_b.empty else "-"
        # En Zayıf (Var olup en az olduğu yer)
        min_city_a = df_a['İl'].value_counts().idxmin() if not df_a.empty else "-"
        min_city_b = df_b['İl'].value_counts().idxmin() if not df_b.empty else "-"

        c_k2.markdown(f"### 🏰 En Güçlü İl")
        c_k2.info(f"**{comp_a}:** {top_city_a}")
        c_k2.warning(f"**{comp_b}:** {top_city_b}")

        c_k3.markdown("### 🏚️ En Zayıf İl")
        c_k3.info(f"**{comp_a}:** {min_city_a}")
        c_k3.warning(f"**{comp_b}:** {min_city_b}")


        st.divider()
        
        # Yan Yana Karşılaştırmalı Grafik (GÜNCELLENDİ - TÜM ŞEHİRLER)
        st.subheader("📊 Şehirlere Göre Kıyaslama (Tümü)")
        df_vs = base_df[base_df['Dağıtım Şirketi'].isin([comp_a, comp_b])]
        
        if not df_vs.empty:
            city_vs = df_vs.groupby(['İl', 'Dağıtım Şirketi']).size().reset_index(name='Adet')
            
            # İlk 15 sınırı kaldırıldı, hepsi gösteriliyor
            fig_vs = px.bar(city_vs, x='İl', y='Adet', color='Dağıtım Şirketi', barmode='group',
                            title="Tüm Şehirlerde Karşılaştırma", text='Adet')
            
            st.plotly_chart(fig_vs, use_container_width=True)
            st.info("💡 **Bilgi:** Şehir sayısı fazla olduğunda grafiği yakınlaştırarak (zoom) veya kaydırarak detayları inceleyebilirsiniz.")
        else:
            st.warning("Seçilen şirketlerin bu bölgede verisi yok.")


    # 3. SİMÜLASYON (SENARYO) (GÜNCELLENDİ - FİLTRE EKLENDİ)
    with tab_sim:
        st.subheader("🔮 'What-If' Senaryo Analizi")
        st.markdown("Bir rakibi hedef alıp, onun bayilerinin belirli bir yüzdesini kazandığımızda pazar payımızın nasıl değişeceğini simüle edin.")

        # --- Simülasyon Özel Filtreleri (YENİ) ---
        with st.expander("⚙️ Simülasyon Kapsamını Daralt (İsteğe Bağlı)", expanded=True):
            col_sim_filter1, col_sim_filter2 = st.columns(2)
            with col_sim_filter1:
                # Bölge seçimi (Sidebar'dan bağımsız veya ona bağlı olabilir, burada bağımsız yapalım)
                sim_regions = ["Tümü"] + list(BOLGE_TANIMLARI.keys())
                selected_sim_region = st.selectbox("Simülasyon Bölgesi", sim_regions)
            
            with col_sim_filter2:
                # İl seçimi (Seçilen bölgeye göre dolsun)
                if selected_sim_region != "Tümü":
                    sim_cities = sorted(BOLGE_TANIMLARI[selected_sim_region])
                else:
                    sim_cities = sorted(df['İl'].unique().tolist())
                
                selected_sim_city = st.selectbox("Simülasyon İli (Opsiyonel)", ["Tümü"] + sim_cities)
        
        # Simülasyon Veri Setini Hazırla
        sim_df = df.copy()
        if selected_sim_region != "Tümü":
            sim_df = sim_df[sim_df['İl'].isin(BOLGE_TANIMLARI[selected_sim_region])]
        if selected_sim_city != "Tümü":
            sim_df = sim_df[sim_df['İl'] == selected_sim_city]

        # --- Şirket Seçimleri ---
        st.markdown("---")
        if selected_companies:
            my_company = selected_companies[0]
        else:
            if not df.empty:
                my_company = df['Dağıtım Şirketi'].value_counts().idxmax()
            else:
                my_company = ""
        
        st.info(f"🎯 **Odak Şirket (Biz):** {my_company}")

        comp_list_sim = sorted(df['Dağıtım Şirketi'].dropna().unique().tolist())
        if my_company in comp_list_sim: comp_list_sim.remove(my_company)
        
        col_sim1, col_sim2 = st.columns(2)
        with col_sim1:
            target_competitor = st.selectbox("Hedef Rakip Seçiniz:", comp_list_sim)
        with col_sim2:
            conversion_rate = st.slider("Dönüşüm Oranı (Rakibin % kaçını alacağız?)", 0, 100, 10, format="%%%d")

        # Hesaplamalar (Filtrelenmiş sim_df üzerinden)
        current_my_count = len(sim_df[sim_df['Dağıtım Şirketi'] == my_company])
        current_target_count = len(sim_df[sim_df['Dağıtım Şirketi'] == target_competitor])
        
        gained_stations = int(current_target_count * (conversion_rate / 100))
        new_my_count = current_my_count + gained_stations
        
        st.divider()
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric(f"Mevcut Bayi ({selected_sim_city if selected_sim_city!='Tümü' else selected_sim_region})", current_my_count)
        col_res2.metric("Kazanılacak Bayi", f"+{gained_stations}")
        growth_pct = ((new_my_count-current_my_count)/current_my_count*100) if current_my_count > 0 else 100
        col_res3.metric("Hedeflenen Yeni Sayı", new_my_count, delta=f"%{growth_pct:.1f} Büyüme")

        sim_data = pd.DataFrame({'Durum': ['Mevcut', 'Kazanılan'], 'Adet': [current_my_count, gained_stations]})
        fig_sim = px.pie(sim_data, values='Adet', names='Durum', title=f"Simülasyon Sonrası {my_company} Yapısı", hole=0.6,
                         color_discrete_sequence=['#2980b9', '#2ecc71'])
        fig_sim.add_annotation(text=f"TOPLAM\n{new_my_count}", showarrow=False, font_size=20)
        st.plotly_chart(fig_sim, use_container_width=True)


    # 4. TAKVİM
    with tab_calendar:
        st.subheader("📅 Aylık Sözleşme Bitiş Takvimi")
        all_years = sorted(df_filtered['Bitis_Yili'].dropna().unique().astype(int).tolist())
        current_year = datetime.date.today().year
        default_ix = all_years.index(current_year) if current_year in all_years else 0
        selected_year = st.selectbox("Yıl Seçiniz:", all_years, index=default_ix)
        df_year = df_filtered[df_filtered['Bitis_Yili'] == selected_year]
        if not df_year.empty:
            monthly_counts = df_year.groupby(['Bitis_Ayi_No']).agg(Adet=('Unvan', 'count'), Ay_Ismi=('Bitis_Ayi', 'first')).reset_index().sort_values('Bitis_Ayi_No')
            fig_cal = px.bar(monthly_counts, x='Ay_Ismi', y='Adet', text='Adet', title=f"{selected_year} Yılı Aylık Dağılım")
            fig_cal.update_traces(marker_color='#2980b9')
            selection = st.plotly_chart(fig_cal, use_container_width=True, on_select="rerun", key="calendar_chart")
            if selection and selection['selection']['points']:
                selected_month_name = selection['selection']['points'][0]['x']
                st.success(f"🗓️ **{selected_month_name} {selected_year}** detayları:")
                df_table = df_year[df_year['Bitis_Ayi'] == selected_month_name]
            else:
                df_table = df_year
            show_details_table(df_table, target_date_col)

    # 5. İLÇE PENETRASYONU
    with tab_ilce:
        st.subheader("📍 İlçe Bazlı Derinlik Analizi")
        if not selected_cities:
            st.warning("Lütfen sol menüden bir **Şehir** seçiniz.")
        else:
            district_breakdown = df_filtered.groupby(['İlçe']).size().reset_index(name='Adet').sort_values('Adet', ascending=True)
            if not district_breakdown.empty:
                fig_ilce = px.bar(district_breakdown, x='Adet', y='İlçe', orientation='h', title="İlçelere Göre Dağılım", text='Adet', height=600)
                fig_ilce.update_traces(marker_color='#0066cc')
                selection_ilce = st.plotly_chart(fig_ilce, use_container_width=True, on_select="rerun", key="ilce_chart")
                if selection_ilce and selection_ilce['selection']['points']:
                    selected_district = selection_ilce['selection']['points'][0]['y']
                    st.success(f"📍 **{selected_district}** ilçesi detayları listeleniyor:")
                    df_ilce_table = df_filtered[df_filtered['İlçe'] == selected_district]
                else:
                    df_ilce_table = df_filtered
                show_details_table(df_ilce_table, target_date_col)
            
            st.divider()
            tum_ilceler_ref = df[df['İl'].isin(selected_cities)]['İlçe'].unique()
            mevcut_ilceler = df_filtered['İlçe'].unique()
            bos_ilceler = sorted(list(set(tum_ilceler_ref) - set(mevcut_ilceler)))
            if bos_ilceler:
                st.markdown("#### ⚠️ Hiç Bayi Olmayan İlçeler (Fırsatlar)")
                cols = st.columns(4)
                for i, ilce in enumerate(bos_ilceler): cols[i % 4].warning(f"📍 {ilce}")

    # 6. CRM LITE (GÜNCELLENDİ - EXCEL İNDİRME EKLENDİ)
    with tab_crm:
        st.subheader("📝 CRM Lite - Bayi Notları")
        st.markdown("Bayilerle ilgili saha notlarını buradan ekleyip takip edebilirsiniz. _(Not: Sayfa yenilenince veriler sıfırlanır)_")
        
        if not df_filtered.empty:
            bayi_listesi = sorted(df_filtered['Unvan'].unique().tolist())
            
            c_crm1, c_crm2 = st.columns([1, 2])
            
            with c_crm1:
                st.markdown("### ➕ Yeni Not Ekle")
                selected_bayi = st.selectbox("Bayi Seçiniz", bayi_listesi)
                note_input = st.text_area("Notunuzu Girin", height=100)
                
                if st.button("💾 Notu Kaydet", type="primary"):
                    if note_input:
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        if selected_bayi in st.session_state.crm_notes:
                            st.session_state.crm_notes[selected_bayi].append(f"[{timestamp}] {note_input}")
                        else:
                            st.session_state.crm_notes[selected_bayi] = [f"[{timestamp}] {note_input}"]
                        st.success("Not kaydedildi!")
            
            with c_crm2:
                # Başlık ve İndirme Butonu Yan Yana
                c_head, c_btn = st.columns([2,1])
                c_head.markdown("### 📋 Kayıtlı Notlar")
                
                if st.session_state.crm_notes:
                    # Notları DataFrame'e çevir
                    crm_data = []
                    for bayi, notlar in st.session_state.crm_notes.items():
                        for tek_not in notlar:
                            crm_data.append({"Bayi Unvanı": bayi, "Not": tek_not})
                    df_crm_export = pd.DataFrame(crm_data)
                    
                    # Excel İndirme Butonu
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        df_crm_export.to_excel(writer, index=False, sheet_name='CRM Notlari')
                    
                    c_btn.download_button(
                        label="📥 Excel Olarak İndir",
                        data=buffer.getvalue(),
                        file_name="CRM_Notlari.xlsx",
                        mime="application/vnd.ms-excel"
                    )

                    for bayi, notlar in st.session_state.crm_notes.items():
                        with st.expander(f"🏢 {bayi} ({len(notlar)} Not)", expanded=True):
                            for not_metni in notlar:
                                st.markdown(f"- {not_metni}")
                else:
                    st.info("Henüz eklenmiş bir not yok.")
        else:
            st.warning("Not eklenecek bayi bulunamadı.")

    # 7. HAM VERİ
    with tab_data:
        st.dataframe(df_filtered, use_container_width=True)

if __name__ == "__main__":
    main()
