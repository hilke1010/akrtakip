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


# --- 4. BÖLGE TANIMLARI ---
BOLGE_TANIMLARI = {
    "Orta Anadolu": [
        "DÜZCE", "KARABÜK", "KONYA", "BOLU", "AFYONKARAHİSAR",
        "AKSARAY", "ESKİŞEHİR", "ANKARA", "KIRIKKALE", "KASTAMONU",
        "ÇANKIRI", "YOZGAT", "KIRŞEHİR", "KAYSERİ", "NEVŞEHİR",
        "NİĞDE", "ZONGULDAK", "BARTIN"
    ]
}


# --- 5. EXCEL VERİ YÜKLEME ---
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
            # Yıl ve Ay bilgisini çıkar (Takvim analizi için)
            df['Bitis_Yili'] = df[target_col].dt.year
            df['Bitis_Ayi'] = df[target_col].dt.month_name(locale='Turkish' if 'Turkish' in datetime.date.today().strftime('%B') else None)
            # Türkçe Ay sıralaması için sayısal değer
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
    """Seçilen filtrelere göre detaylı bayi listesini gösterir."""
    if dataframe.empty:
        st.info("Seçilen kriterlere uygun kayıt bulunamadı.")
        return

    # Gösterilecek Sütunlar
    cols = ['Unvan', 'İl', 'İlçe', 'Dağıtım Şirketi', target_date_col, 'Kalan_Gun', 'Risk_Durumu']
    # Sadece mevcut olanları seç
    final_cols = [c for c in cols if c in dataframe.columns]
    
    # Tarih formatı düzeltme
    display_df = dataframe[final_cols].copy()
    if target_date_col in display_df.columns:
        display_df[target_date_col] = display_df[target_date_col].dt.strftime('%d.%m.%Y')

    # Sıralama: Kalan güne göre (en kritik en üstte)
    display_df = display_df.sort_values('Kalan_Gun')

    # Renklendirme (Pandas Styler)
    def highlight_risk(val):
        if val < 0: color = '#ffcccc' # Kırmızımsı
        elif val < 90: color = '#ffe5cc' # Turuncumsu
        elif val < 180: color = '#ffffcc' # Sarımsı
        else: color = '' 
        return f'background-color: {color}'

    st.markdown(f"**📋 Listelenen Bayi Sayısı:** {len(display_df)}")
    
    # Kalan gün sütununu renklendirerek göster
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

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam İstasyon", f"{len(df_filtered):,}")

    acil_durum = len(df_filtered[df_filtered['Kalan_Gun'] < 90])
    c2.metric("Acil Sözleşme", acil_durum, delta="Acil Yenileme", delta_color="inverse")

    if 'Dağıtım Şirketi' in df_filtered.columns:
        aktif_dagitici = df_filtered['Dağıtım Şirketi'].nunique()
    else:
        aktif_dagitici = 0
    c3.metric("Aktif Dağıtıcı", aktif_dagitici)

    if not df_filtered.empty:
        ort_gun = df_filtered['Kalan_Gun'].mean()
        c4.metric("Ort. Kalan Gün", f"{ort_gun:.0f}")
    else:
        c4.metric("Ort. Kalan Gün", "0")

    st.divider()

    # --- SEKMELER ---
    tab_risk, tab_calendar, tab_ilce, tab_market, tab_data = st.tabs([
        "⚡ Sözleşme & Risk",
        "📅 Sözleşme Takvimi", # YENİ (ZAMAN ANALİZİ YERİNE)
        "📍 İlçe Penetrasyonu",
        "🏢 Pazar & Rekabet",
        "📋 Ham Veri"
    ])

    # 1. RİSK TABLOSU
    with tab_risk:
        st.subheader("🚨 Kritik Sözleşmeler (İlk 6 Ay)")
        critical_df = df_filtered[df_filtered['Kalan_Gun'] < 180].sort_values('Kalan_Gun')
        show_details_table(critical_df, target_date_col)

    # 2. SÖZLEŞME TAKVİMİ (İNTERAKTİF)
    with tab_calendar:
        st.subheader("📅 Aylık Sözleşme Bitiş Takvimi")
        st.info("👇 Grafikteki ayların üzerine tıklayarak o aydaki bayilerin listesini aşağıda görebilirsiniz.")

        # Yıl Seçimi
        all_years = sorted(df_filtered['Bitis_Yili'].dropna().unique().astype(int).tolist())
        # Mevcut yıl varsayılan olsun
        current_year = datetime.date.today().year
        default_ix = all_years.index(current_year) if current_year in all_years else 0
        
        selected_year = st.selectbox("Yıl Seçiniz:", all_years, index=default_ix)

        # Seçilen yıla göre filtrele
        df_year = df_filtered[df_filtered['Bitis_Yili'] == selected_year]
        
        if not df_year.empty:
            # Aylık gruplama
            # Ayları sayısal sıraya göre dizmek için
            monthly_counts = df_year.groupby(['Bitis_Ayi_No']).agg(
                Adet=('Unvan', 'count'),
                Ay_Ismi=('Bitis_Ayi', 'first') # Grubun ilk ay ismini al
            ).reset_index().sort_values('Bitis_Ayi_No')
            
            # Grafik
            fig_cal = px.bar(monthly_counts, x='Ay_Ismi', y='Adet', text='Adet',
                             title=f"{selected_year} Yılı Aylık Dağılım",
                             hover_data=['Ay_Ismi'])
            fig_cal.update_traces(marker_color='#2980b9')
            fig_cal.update_layout(xaxis_title="Ay", yaxis_title="Bitecek Sözleşme Sayısı")
            
            # --- INTERAKTİF SEÇİM ---
            selection = st.plotly_chart(fig_cal, use_container_width=True, on_select="rerun")
            
            # Seçim Mantığı
            selected_month_name = None
            if selection and selection['selection']['points']:
                # Seçilen barın x değerini (Ay İsmi) al
                selected_month_name = selection['selection']['points'][0]['x']
                st.success(f"🗓️ **{selected_month_name} {selected_year}** için detaylar listeleniyor:")
                
                # Tabloyu filtrele
                df_table = df_year[df_year['Bitis_Ayi'] == selected_month_name]
            else:
                st.markdown("**Tüm Yıl Listesi:** (Filtrelemek için grafiğe tıklayın)")
                df_table = df_year

            # Tabloyu Göster
            show_details_table(df_table, target_date_col)
            
        else:
            st.warning("Bu yıl için veri bulunamadı.")

    # 3. İLÇE PENETRASYONU (İNTERAKTİF)
    with tab_ilce:
        st.subheader("📍 İlçe Bazlı Derinlik Analizi")
        st.info("👇 Grafikteki ilçelerin üzerine tıklayarak o ilçedeki bayilerin listesini aşağıda görebilirsiniz.")
        
        if not selected_cities:
            st.warning("Lütfen sol menüden bir **Şehir** seçiniz.")
        else:
            # --- Grafik ---
            district_breakdown = df_filtered.groupby(['İlçe']).size().reset_index(name='Adet').sort_values('Adet', ascending=True)
            
            if not district_breakdown.empty:
                fig_ilce = px.bar(district_breakdown, x='Adet', y='İlçe', 
                                  orientation='h', title="İlçelere Göre Dağılım",
                                  text='Adet', height=600)
                fig_ilce.update_traces(marker_color='#0066cc')
                fig_ilce.update_layout(yaxis={'categoryorder': 'total ascending'})
                
                # --- INTERAKTİF SEÇİM ---
                selection_ilce = st.plotly_chart(fig_ilce, use_container_width=True, on_select="rerun")
                
                # Seçim Mantığı
                selected_district = None
                if selection_ilce and selection_ilce['selection']['points']:
                    # Seçilen barın y değerini (İlçe) al (Yatay bar olduğu için y ekseni kategori)
                    selected_district = selection_ilce['selection']['points'][0]['y']
                    st.success(f"📍 **{selected_district}** ilçesi detayları listeleniyor:")
                    
                    df_ilce_table = df_filtered[df_filtered['İlçe'] == selected_district]
                else:
                    st.markdown("**Seçilen Şehirlerin Tümü:** (Özel bir ilçe görmek için grafiğe tıklayın)")
                    df_ilce_table = df_filtered

                # Tabloyu Göster
                show_details_table(df_ilce_table, target_date_col)

            else:
                st.warning("Veri bulunamadı.")

            st.divider()
            # GAP ANALİZİ
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
