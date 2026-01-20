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

# --- PERFORMANS AYARLARI ---
MAX_ROW_DISPLAY = 5000
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
    .block-container { padding-top: 2rem; }
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
    .insight-box-success {
        padding: 15px; border-radius: 8px; background-color: #d4edda; border-left: 5px solid #28a745; color: #155724; margin-bottom: 10px;
    }
    .insight-box-warning {
        padding: 15px; border-radius: 8px; background-color: #fff3cd; border-left: 5px solid #ffc107; color: #856404; margin-bottom: 10px;
    }
    .insight-box-danger {
        padding: 15px; border-radius: 8px; background-color: #f8d7da; border-left: 5px solid #dc3545; color: #721c24; margin-bottom: 10px;
    }
    .insight-box-info {
        padding: 15px; border-radius: 8px; background-color: #d1ecf1; border-left: 5px solid #17a2b8; color: #0c5460; margin-bottom: 10px;
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

# --- CRM SESSION ---
if 'crm_notes' not in st.session_state:
    st.session_state.crm_notes = {}

# --- 6. EXCEL VERİ YÜKLEME ---
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path): return None, None
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

        def get_risk(days):
            if pd.isna(days): return "Bilinmiyor"
            if days < 0: return "SÜRESİ DOLDU 🚨"
            if days < 90: return "KRİTİK (<3 Ay) ⚠️"
            if days < 180: return "YAKLAŞIYOR (<6 Ay) ⏳"
            return "GÜVENLİ ✅"
        df['Risk_Durumu'] = df['Kalan_Gun'].apply(get_risk)

        if 'İl' in df.columns: df['İl'] = df['İl'].astype(str).str.upper().str.replace('i', 'İ').str.replace('ı', 'I')
        if 'İlçe' in df.columns: df['İlçe'] = df['İlçe'].astype(str).str.upper().str.replace('i', 'İ').str.replace('ı', 'I')
        return df, target_col
    except Exception as e: return None, str(e)

# --- DETAY TABLOSU ---
def show_details_table(dataframe, target_date_col):
    if dataframe is None or dataframe.empty:
        st.info("Seçilen kriterlere uygun kayıt bulunamadı.")
        return
    record_count = len(dataframe)
    if record_count > MAX_ROW_DISPLAY:
        st.markdown(f"<div class='warning-box'>⚠️ Performans: {record_count:,} kayıt var. Filtreleyerek {MAX_ROW_DISPLAY} altına düşürün.</div>", unsafe_allow_html=True)
        return
    cols = ['Unvan', 'İl', 'İlçe', 'Dağıtım Şirketi', target_date_col, 'Kalan_Gun', 'Risk_Durumu']
    final_cols = [c for c in cols if c in dataframe.columns]
    display_df = dataframe[final_cols].copy()
    if target_date_col in display_df.columns:
        try: display_df[target_date_col] = pd.to_datetime(display_df[target_date_col]).dt.strftime('%d.%m.%Y')
        except: pass
    if 'Kalan_Gun' in display_df.columns: display_df = display_df.sort_values('Kalan_Gun')
    
    def highlight_risk(val):
        if not isinstance(val, (int, float)): return ''
        if val < 0: return 'background-color: #ffcccc'
        elif val < 90: return 'background-color: #ffe5cc'
        elif val < 180: return 'background-color: #ffffcc'
        return ''
    
    st.markdown(f"**📋 Listelenen Bayi Sayısı:** {len(display_df)}")
    if 'Kalan_Gun' in display_df.columns:
        st.dataframe(display_df.style.map(highlight_risk, subset=['Kalan_Gun']), use_container_width=True, hide_index=True)
    else:
        st.dataframe(display_df, use_container_width=True, hide_index=True)

# --- ANA UYGULAMA ---
def main():
    data_result = load_data(SABIT_DOSYA_ADI)
    if data_result is None or data_result[0] is None:
        st.error(f"⚠️ Hata: {data_result[1] if data_result else 'Veri Yüklenemedi'}")
        st.stop()
    df, target_date_col = data_result

    with st.sidebar:
        st.info("🕒 Veriler her gün saat 10:00'da yenilenmektedir.")
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
        st.header("📧 İletişim")
        st.info("kerim.aksu@milangaz.com.tr")

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
    st.divider()

    # --- SEKMELER ---
    tab_overview, tab_machine, tab_compare, tab_sim, tab_calendar, tab_ilce, tab_crm, tab_data = st.tabs([
        "📊 Bölgesel & Durum",
        "🤖 Makine Analizi",     
        "⚔️ Karşılaştırma (Vs.)", 
        "🔮 Simülasyon",         
        "📅 Takvim", 
        "📍 İlçe Penetrasyonu",
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
                
                st.info("""
                ℹ️ **Harita Lejandı:**
                *   🔴 **Koyu Renkler:** Yoğunluğun yüksek olduğu bölgeler.
                *   🔵 **Açık Renkler:** Yoğunluğun düşük olduğu bölgeler.
                *   ⚪ **Daire Büyüklüğü:** Toplam istasyon sayısı ile orantılıdır.
                """)

        st.divider()
        st.subheader("📊 İstatistikler")
        
        # Çubuk Grafik
        fig_city = px.bar(map_data, x='İl', y='Adet', text='Adet', title="Şehir Sıralaması", color='Adet', color_continuous_scale='Blues')
        st.plotly_chart(fig_city, use_container_width=True, on_select="rerun", key="overview_bar_chart")
        st.caption("ℹ️ *Grafiği sağ üst köşesinden büyütebilir, üzerine gelerek detayları görebilirsiniz.*")

        st.markdown("---")
        
        # İki Pasta Yan Yana (Şehir ve Dağıtıcı)
        col_pie1, col_pie2 = st.columns(2)
        
        with col_pie1:
            # Şehir Pastası (İlk 10 + Diğer)
            city_pie_data = df_filtered['İl'].value_counts().reset_index()
            city_pie_data.columns = ['İl', 'Adet']
            if len(city_pie_data) > 10:
                top_10 = city_pie_data.iloc[:10]
                others = pd.DataFrame({'İl': ['DİĞER'], 'Adet': [city_pie_data.iloc[10:]['Adet'].sum()]})
                city_pie_data = pd.concat([top_10, others])
            
            fig_city_pie = px.pie(city_pie_data, values='Adet', names='İl', hole=0.4, title="Şehir Dağılımı (%)")
            st.plotly_chart(fig_city_pie, use_container_width=True)

        with col_pie2:
            # Dağıtıcı Pastası (İlk 5 + Diğer)
            if 'Dağıtım Şirketi' in df_filtered.columns:
                dist_pie_data = df_filtered['Dağıtım Şirketi'].value_counts().reset_index()
                dist_pie_data.columns = ['Dağıtım Şirketi', 'Adet']
                if len(dist_pie_data) > 5:
                    top_5 = dist_pie_data.iloc[:5]
                    others = pd.DataFrame({'Dağıtım Şirketi': ['DİĞER'], 'Adet': [dist_pie_data.iloc[5:]['Adet'].sum()]})
                    dist_pie_data = pd.concat([top_5, others])
                fig_dist_pie = px.pie(dist_pie_data, values='Adet', names='Dağıtım Şirketi', hole=0.4, title="Pazar Payı (Dağıtıcı)")
                st.plotly_chart(fig_dist_pie, use_container_width=True)

        # Tablo
        selected_chart_city = None
        try:
            if st.session_state.get("overview_bar_chart") and st.session_state["overview_bar_chart"]['selection']['points']:
                selected_chart_city = st.session_state["overview_bar_chart"]['selection']['points'][0]['x']
                st.success(f"📌 **{selected_chart_city}** detayları listeleniyor:")
                filtered_table = df_filtered[df_filtered['İl'] == selected_chart_city]
            else: filtered_table = df_filtered
        except: filtered_table = df_filtered
        show_details_table(filtered_table, target_date_col)

    # 2. MAKİNE ANALİZİ (GÜNCELLENDİ: TÜM İLÇELERİ GÖSTER)
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
            
            st.markdown(f"""
            <div class="insight-box-success">
                <b>🏆 En Güçlü Kale:</b> <br>
                Şirketin bu bölgedeki en yoğun olduğu il <b>{top_city}</b> ({top_city_count} Bayi).
            </div>
            """, unsafe_allow_html=True)

            # --- EKSİK İLÇELER (DÜZELTİLDİ: TÜMÜNÜ GÖSTER) ---
            all_scope_districts = scope_df['İlçe'].unique()
            my_districts = my_df['İlçe'].unique()
            missing_districts = sorted(list(set(all_scope_districts) - set(my_districts)))
            
            if len(missing_districts) > 0:
                st.markdown(f"""
                <div class="insight-box-warning">
                    <b>🚀 Büyüme Fırsatları (Boş Noktalar):</b> <br>
                    Bu bölgede toplam <b>{len(missing_districts)}</b> ilçede hiç bayiniz bulunmuyor.
                </div>
                """, unsafe_allow_html=True)
                
                # Expandable Liste
                with st.expander("📄 Tüm Eksik İlçeleri Listele (Tıklayın)", expanded=False):
                    st.write(", ".join(missing_districts))
                    st.info("💡 **Not:** Nüfus verisi veritabanında olmadığı için '+10.000 nüfus' filtresi uygulanamamıştır. Ancak yukarıdaki liste bölgedeki tüm eksik noktaları içerir.")
            else:
                st.success("Tebrikler! Bu bölgedeki tüm ilçelerde varlık gösteriyorsunuz.")

            if 'Bitis_Yili' in my_df.columns:
                next_year = datetime.date.today().year + 1
                expiring_soon = len(my_df[my_df['Bitis_Yili'] == next_year])
                if expiring_soon > 0:
                    st.markdown(f"""
                    <div class="insight-box-danger">
                        <b>⚠️ Kritik Yenileme Dönemi:</b> <br>
                        Önümüzdeki yıl ({next_year}) toplam <b>{expiring_soon}</b> adet sözleşmeniz sona erecek.
                    </div>
                    """, unsafe_allow_html=True)
            
            total_market = len(scope_df)
            my_share = len(my_df)
            share_pct = (my_share / total_market) * 100
            st.markdown(f"""
            <div class="insight-box-info">
                <b>📊 Pazar Payı:</b> <br>
                Bölgedeki toplam pazar payınız: <b>%{share_pct:.1f}</b>.
            </div>
            """, unsafe_allow_html=True)

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
            
            fig_sim = px.pie(values=[curr, gain], names=['Mevcut', 'Kazanılan'], title="Simülasyon Sonucu", hole=0.6, color_discrete_sequence=['#2980b9', '#2ecc71'])
            fig_sim.add_annotation(text=f"{new}", showarrow=False, font_size=20)
            st.plotly_chart(fig_sim, use_container_width=True)

    # 5. TAKVİM
    with tab_calendar:
        st.subheader("📅 Aylık Sözleşme Takvimi")
        if 'Bitis_Yili' in df_filtered.columns:
            yrs = sorted(df_filtered['Bitis_Yili'].dropna().unique().astype(int).tolist())
            if yrs:
                curr_yr = datetime.date.today().year
                sel_yr = st.selectbox("Yıl", yrs, index=yrs.index(curr_yr) if curr_yr in yrs else 0)
                df_yr = df_filtered[df_filtered['Bitis_Yili'] == sel_yr]
                if not df_yr.empty:
                    m_cnt = df_yr.groupby(['Bitis_Ayi_No']).agg(Adet=('Unvan','count'), Ay=('Bitis_Ayi','first')).reset_index().sort_values('Bitis_Ayi_No')
                    fig_cal = px.bar(m_cnt, x='Ay', y='Adet', text='Adet', title=f"{sel_yr} Dağılımı")
                    sel = st.plotly_chart(fig_cal, use_container_width=True, on_select="rerun", key="cal_sel")
                    if sel and sel['selection']['points']:
                        mn = sel['selection']['points'][0]['x']
                        st.success(f"🗓️ **{mn} {sel_yr}**")
                        show_details_table(df_yr[df_yr['Bitis_Ayi']==mn], target_date_col)
                    else: show_details_table(df_yr, target_date_col)

    # 6. İLÇE PENETRASYONU
    with tab_ilce:
        st.subheader("📍 İlçe Bazlı Derinlik")
        if not selected_cities: st.warning("Lütfen sol menüden Şehir seçin.")
        else:
            if not df_filtered.empty:
                d_cnt = df_filtered.groupby(['İlçe']).size().reset_index(name='Adet').sort_values('Adet', ascending=True)
                fig_ilce = px.bar(d_cnt, x='Adet', y='İlçe', orientation='h', text='Adet', height=600)
                sel_ilce = st.plotly_chart(fig_ilce, use_container_width=True, on_select="rerun", key="ilce_sel")
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

    # 7. CRM LITE
    with tab_crm:
        st.subheader("📝 CRM Lite")
        if not df_filtered.empty:
            bayiler = sorted(df_filtered['Unvan'].unique().tolist())
            cr1, cr2 = st.columns([1,2])
            with cr1:
                sel_b = st.selectbox("Bayi", bayiler)
                note = st.text_area("Not", height=100)
                if st.button("Kaydet", type="primary") and note:
                    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
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

    # 8. HAM VERİ
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
