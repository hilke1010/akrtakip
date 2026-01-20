import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import numpy as np
import os

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
</style>
""", unsafe_allow_html=True)

# --- 4. KOORDİNAT VERİTABANI (İL MERKEZLERİ) ---
# Excel'de koordinat olmadığı için illeri haritada göstermek adına bu listeyi kullanıyoruz.
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

    # KPI KISMI (Ortalama Kalan Gün Kaldırıldı)
    c1, c2, c3 = st.columns(3) # Kolon sayısı 3'e düşürüldü
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
    tab_overview, tab_calendar, tab_ilce, tab_market, tab_data = st.tabs([
        "📊 Bölgesel Harita & Durum", 
        "📅 Sözleşme Takvimi", 
        "📍 İlçe Penetrasyonu",
        "🏢 Pazar & Rekabet",
        "📋 Ham Veri"
    ])

    # 1. BÖLGESEL HARİTA & DURUM
    with tab_overview:
        st.subheader("🗺️ Bölgesel Yoğunluk Haritası")
        
        # HARİTA AÇIKLAMASI
        st.info("""
        ℹ️ **Harita Nasıl Okunur?**
        - **Noktaların Büyüklüğü:** O ildeki toplam bayi sayısını temsil eder. Büyük nokta = Çok Bayi.
        - **Renk Tonu:** Koyu renkli iller yoğunluğun en fazla olduğu bölgelerdir.
        - Harita üzerinde yakınlaştırma (zoom) yapabilir, noktaların üzerine gelerek sayıları görebilirsiniz.
        """)

        if not df_filtered.empty:
            # 1. Harita Verisini Hazırla (İllere Göre Grupla)
            map_data = df_filtered['İl'].value_counts().reset_index()
            map_data.columns = ['İl', 'Adet']
            
            # Koordinatları Eşle
            map_data['lat'] = map_data['İl'].map(lambda x: CITY_COORDINATES.get(x, [None, None])[0])
            map_data['lon'] = map_data['İl'].map(lambda x: CITY_COORDINATES.get(x, [None, None])[1])
            
            # Koordinatı bulunamayanları çıkar (örn: hatalı yazım)
            map_data = map_data.dropna(subset=['lat', 'lon'])

            if not map_data.empty:
                # Harita Çizimi
                fig_map = px.scatter_mapbox(
                    map_data, 
                    lat="lat", lon="lon", 
                    size="Adet", 
                    color="Adet",
                    hover_name="İl",
                    size_max=35, 
                    zoom=5 if selected_region == "Tümü" else 6, # Bölge seçiliyse biraz daha yakınlaş
                    mapbox_style="open-street-map",
                    color_continuous_scale=px.colors.sequential.Bluered,
                    title="İl Bazlı Bayi Yoğunluğu"
                )
                
                # Eğer bölge seçiliyse haritayı o bölgenin merkezine odakla
                if selected_region != "Tümü":
                    center_lat = map_data['lat'].mean()
                    center_lon = map_data['lon'].mean()
                    fig_map.update_layout(mapbox_center={"lat": center_lat, "lon": center_lon})
                else:
                    # Türkiye Merkezi
                    fig_map.update_layout(mapbox_center={"lat": 39.0, "lon": 35.0}, mapbox_zoom=4.8)
                
                fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.warning("Harita için uygun koordinat verisi eşleştirilemedi.")

            st.divider()
            
            # --- Grafik ve Liste ---
            st.subheader("📊 Şehir Bazlı İstatistikler")
            
            col_chart, col_pie = st.columns([2, 1])
            
            with col_chart:
                fig_city = px.bar(map_data, x='İl', y='Adet', text='Adet', 
                                  title="Şehir Bayi Sıralaması",
                                  color='Adet', color_continuous_scale='Blues')
                st.plotly_chart(fig_city, use_container_width=True, on_select="rerun", key="overview_bar_chart")
            
            with col_pie:
                risk_status_counts = df_filtered['Risk_Durumu'].value_counts().reset_index()
                risk_status_counts.columns = ['Risk_Durumu', 'Adet']
                fig_pie = px.pie(risk_status_counts, values='Adet', names='Risk_Durumu', hole=0.4,
                                 title="Genel Risk Dağılımı",
                                 color_discrete_map={"SÜRESİ DOLDU 🚨": "red", "KRİTİK (<3 Ay) ⚠️": "orange",
                                                     "YAKLAŞIYOR (<6 Ay) ⏳": "#FFD700", "GÜVENLİ ✅": "green"})
                st.plotly_chart(fig_pie, use_container_width=True)

            # --- ETKİLEŞİMLİ LİSTE ---
            selected_chart_city = None
            if st.session_state.get("overview_bar_chart") and st.session_state["overview_bar_chart"]['selection']['points']:
                selected_chart_city = st.session_state["overview_bar_chart"]['selection']['points'][0]['x']
                st.success(f"📌 **{selected_chart_city}** detayları listeleniyor:")
                filtered_table = df_filtered[df_filtered['İl'] == selected_chart_city]
            else:
                st.markdown("### 📋 Detaylı Liste")
                filtered_table = df_filtered
                
            show_details_table(filtered_table, target_date_col)
            
        else:
            st.warning("Seçilen kriterlere uygun veri bulunamadı.")

    # 2. SÖZLEŞME TAKVİMİ
    with tab_calendar:
        st.subheader("📅 Aylık Sözleşme Bitiş Takvimi")
        st.info("👇 Grafikteki ayların üzerine tıklayarak o aydaki bayilerin listesini aşağıda görebilirsiniz.")

        all_years = sorted(df_filtered['Bitis_Yili'].dropna().unique().astype(int).tolist())
        current_year = datetime.date.today().year
        default_ix = all_years.index(current_year) if current_year in all_years else 0
        
        selected_year = st.selectbox("Yıl Seçiniz:", all_years, index=default_ix)
        df_year = df_filtered[df_filtered['Bitis_Yili'] == selected_year]
        
        if not df_year.empty:
            monthly_counts = df_year.groupby(['Bitis_Ayi_No']).agg(
                Adet=('Unvan', 'count'),
                Ay_Ismi=('Bitis_Ayi', 'first')
            ).reset_index().sort_values('Bitis_Ayi_No')
            
            fig_cal = px.bar(monthly_counts, x='Ay_Ismi', y='Adet', text='Adet',
                             title=f"{selected_year} Yılı Aylık Dağılım",
                             hover_data=['Ay_Ismi'])
            fig_cal.update_traces(marker_color='#2980b9')
            
            selection = st.plotly_chart(fig_cal, use_container_width=True, on_select="rerun", key="calendar_chart")
            
            if selection and selection['selection']['points']:
                selected_month_name = selection['selection']['points'][0]['x']
                st.success(f"🗓️ **{selected_month_name} {selected_year}** detayları:")
                df_table = df_year[df_year['Bitis_Ayi'] == selected_month_name]
            else:
                st.markdown("**Tüm Yıl Listesi:**")
                df_table = df_year

            show_details_table(df_table, target_date_col)
        else:
            st.warning("Bu yıl için veri bulunamadı.")

    # 3. İLÇE PENETRASYONU
    with tab_ilce:
        st.subheader("📍 İlçe Bazlı Derinlik Analizi")
        st.info("👇 Grafikteki ilçelerin üzerine tıklayarak o ilçedeki bayilerin listesini aşağıda görebilirsiniz.")
        
        if not selected_cities:
            st.warning("Lütfen sol menüden bir **Şehir** seçiniz.")
        else:
            district_breakdown = df_filtered.groupby(['İlçe']).size().reset_index(name='Adet').sort_values('Adet', ascending=True)
            
            if not district_breakdown.empty:
                fig_ilce = px.bar(district_breakdown, x='Adet', y='İlçe', 
                                  orientation='h', title="İlçelere Göre Dağılım",
                                  text='Adet', height=600)
                fig_ilce.update_traces(marker_color='#0066cc')
                fig_ilce.update_layout(yaxis={'categoryorder': 'total ascending'})
                
                selection_ilce = st.plotly_chart(fig_ilce, use_container_width=True, on_select="rerun", key="ilce_chart")
                
                if selection_ilce and selection_ilce['selection']['points']:
                    selected_district = selection_ilce['selection']['points'][0]['y']
                    st.success(f"📍 **{selected_district}** ilçesi detayları listeleniyor:")
                    df_ilce_table = df_filtered[df_filtered['İlçe'] == selected_district]
                else:
                    st.markdown("**Seçilen Şehirlerin Tümü:**")
                    df_ilce_table = df_filtered

                show_details_table(df_ilce_table, target_date_col)
            else:
                st.warning("Veri bulunamadı.")
            
            st.divider()
            st.markdown("#### ⚠️ Hiç Bayi Olmayan İlçeler (Fırsatlar)")
            tum_ilceler_ref = df[df['İl'].isin(selected_cities)]['İlçe'].unique()
            mevcut_ilceler = df_filtered['İlçe'].unique()
            bos_ilceler = set(tum_ilceler_ref) - set(mevcut_ilceler)
            
            if bos_ilceler:
                bos_ilceler_list = sorted(list(bos_ilceler))
                cols = st.columns(4)
                for i, ilce in enumerate(bos_ilceler_list):
                    cols[i % 4].warning(f"📍 {ilce}")
            else:
                st.success("Tebrikler! Seçilen şehirlerin tüm ilçelerinde varlık gösteriliyor.")

    # 4. PAZAR ANALİZİ
    with tab_market:
        if 'Dağıtım Şirketi' in df_filtered.columns and 'İl' in df_filtered.columns and not df_filtered.empty:
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                st.subheader("Treemap (Şirket > İl)")
                st.plotly_chart(px.treemap(df_filtered, path=['Dağıtım Şirketi', 'İl'], color='Dağıtım Şirketi'),
                                use_container_width=True)
            with c_m2:
                st.subheader("Pazar Payı Pastası")
                cc = df_filtered['Dağıtım Şirketi'].value_counts().reset_index()
                cc.columns = ['Şirket', 'Adet']
                tot = cc['Adet'].sum()
                if len(cc) > 10:
                    cc = pd.concat(
                        [cc.iloc[:10], pd.DataFrame({'Şirket': ['DİĞER'], 'Adet': [cc.iloc[10:]['Adet'].sum()]})])

                fig = px.pie(cc, values='Adet', names='Şirket', hole=0.5)
                fig.add_annotation(text=f"{tot}", x=0.5, y=0.5, font_size=20, showarrow=False)
                st.plotly_chart(fig, use_container_width=True)

    # 5. HAM VERİ
    with tab_data:
        st.dataframe(df_filtered, use_container_width=True)


if __name__ == "__main__":
    main()
