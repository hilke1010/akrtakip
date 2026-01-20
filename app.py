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
        else:
            df['Kalan_Gun'] = np.nan

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

        # Risk Filtresi
        all_risks = sorted(df['Risk_Durumu'].unique().tolist())
        selected_risks = st.multiselect("⚠️ Risk Durumu", all_risks)

        st.info(f"Excel Kayıt: {len(df)}")

        st.markdown("---")
        st.header("🔗 Diğer Raporlar")
        st.markdown("🔥 [LPG Lisans Raporu](https://lpgtakip.streamlit.app/)")
        st.markdown("📊 [EPDK Sektör Raporu](https://pazarpayi.streamlit.app/)")
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
    if selected_risks: df_filtered = df_filtered[df_filtered['Risk_Durumu'].isin(selected_risks)]

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

    # --- SEKMELER (ZAMAN KALDIRILDI, İLÇE EKLENDİ) ---
    tab_risk, tab_detay, tab_market, tab_ilce, tab_data = st.tabs([
        "⚡ Sözleşme & Risk",
        "🔢 Detaylı Bayi",
        "🏢 Pazar & Rekabet",
        "📍 İlçe Penetrasyonu",  # YENİ
        "📋 Ham Veri"
    ])

    # 1. RİSK TABLOSU
    with tab_risk:
        st.subheader("🚨 Kritik Sözleşmeler (İlk 6 Ay)")
        critical_df = df_filtered[df_filtered['Kalan_Gun'] < 180].sort_values('Kalan_Gun')
        critical_df.index = np.arange(1, len(critical_df) + 1)

        display_cols = ['İl', 'İlçe', 'Dağıtım Şirketi', 'Kalan_Gun', 'Risk_Durumu']
        if 'Unvan' in df.columns: display_cols.insert(0, 'Unvan')
        if target_date_col in df.columns:
            critical_df['Bitis_Tarihi'] = critical_df[target_date_col].dt.strftime('%Y-%m-%d')
            display_cols.insert(3, 'Bitis_Tarihi')

        cols_to_show = [c for c in display_cols if c in critical_df.columns]

        if not critical_df.empty:
            st.dataframe(critical_df[cols_to_show], use_container_width=True)
        else:
            st.success("Seçilen kriterlerde riskli (süresi dolan veya 6 aydan az kalan) sözleşme yok.")

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            if target_date_col in df_filtered.columns and not df_filtered.empty:
                df_filtered['Yil'] = df_filtered[target_date_col].dt.year
                y_cnt = df_filtered['Yil'].value_counts().sort_index().reset_index()
                y_cnt.columns = ['Yıl', 'Adet']
                curr_year = datetime.date.today().year
                y_cnt = y_cnt[(y_cnt['Yıl'] >= curr_year) & (y_cnt['Yıl'] <= curr_year + 10)]
                st.plotly_chart(px.bar(y_cnt, x='Yıl', y='Adet', text='Adet', title="Yıllara Göre Bitecek Sözleşmeler",
                                       color='Adet', color_continuous_scale='Blues'), use_container_width=True)

        with col_r2:
            if not df_filtered.empty:
                risk_counts = df_filtered['Risk_Durumu'].value_counts().reset_index()
                risk_counts.columns = ['Durum', 'Adet']
                st.plotly_chart(
                    px.pie(risk_counts, values='Adet', names='Durum', hole=0.4, title="Risk Dağılımı",
                           color_discrete_map={"SÜRESİ DOLDU 🚨": "red", "KRİTİK (<3 Ay) ⚠️": "orange",
                                               "YAKLAŞIYOR (<6 Ay) ⏳": "#FFD700", "GÜVENLİ ✅": "green"}),
                    use_container_width=True
                )

    # 2. DETAYLI BAYİ
    with tab_detay:
        if 'Dağıtım Şirketi' in df_filtered.columns and not df_filtered.empty:
            if not selected_companies:
                comp_stats = df_filtered['Dağıtım Şirketi'].value_counts().reset_index()
                comp_stats.columns = ['Şirket', 'Toplam Bayi']
                comp_stats.index = np.arange(1, len(comp_stats) + 1)

                c_d1, c_d2 = st.columns(2)
                with c_d1:
                    st.dataframe(comp_stats, use_container_width=True, height=600)
                with c_d2:
                    fig_comp = px.bar(comp_stats.head(30), x='Toplam Bayi', y='Şirket', orientation='h', height=600,
                                      text='Toplam Bayi', title="En Büyük Dağıtım Şirketleri (İlk 30)")
                    fig_comp.update_layout(yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig_comp, use_container_width=True)
            else:
                city_stats = df_filtered['İl'].value_counts().reset_index()
                city_stats.columns = ['Şehir', 'Bayi Sayısı']
                city_stats.index = np.arange(1, len(city_stats) + 1)

                c_d1, c_d2 = st.columns(2)
                with c_d1:
                    st.dataframe(city_stats, use_container_width=True, height=600)
                with c_d2:
                    fig_city = px.bar(city_stats, x='Bayi Sayısı', y='Şehir', orientation='h', height=600,
                                      text='Bayi Sayısı', title="Seçilen Şirketlerin İllere Göre Dağılımı")
                    fig_city.update_layout(yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig_city, use_container_width=True)

    # 3. PAZAR ANALİZİ
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

    # 4. İLÇE PENETRASYONU (YENİ EKLENEN KISIM)
    with tab_ilce:
        st.subheader("📍 İlçe Bazlı Derinlik Analizi")
        
        if not selected_cities:
            st.info("💡 İlçe bazlı detaylı penetrasyon analizi için sol menüden en az bir **Şehir** seçmelisiniz.")
            # Şehir seçili değilse genel olarak en yoğun ilçeleri gösterelim
            if not df_filtered.empty:
                st.markdown("##### Türkiye Geneli En Yoğun İlçeler")
                top_districts = df_filtered.groupby(['İl','İlçe']).size().reset_index(name='Bayi Sayısı')
                top_districts['Etiket'] = top_districts['İl'] + " - " + top_districts['İlçe']
                top_districts = top_districts.sort_values('Bayi Sayısı', ascending=False).head(20)
                
                fig_top = px.bar(top_districts, x='Bayi Sayısı', y='Etiket', orientation='h', text='Bayi Sayısı',
                                 title="Türkiye Geneli Top 20 İlçe (Filtrelere Göre)")
                fig_top.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_top, use_container_width=True)
        else:
            # Şehir Seçildiyse Analizi Başlat
            st.markdown(f"**Seçilen Şehirler:** {', '.join(selected_cities)}")
            
            # --- Grafik 1: Seçilen Kriterlere Göre İlçe Dağılımı ---
            district_breakdown = df_filtered.groupby(['İlçe', 'Dağıtım Şirketi']).size().reset_index(name='Adet')
            
            # Daha güzel görünüm için pivot yapalım (sütun: şirket, satır: ilçe)
            if not district_breakdown.empty:
                fig_ilce = px.bar(district_breakdown, x='Adet', y='İlçe', color='Dağıtım Şirketi', 
                                  orientation='h', title="İlçelere Göre Dağılım (Seçili Kriterler)",
                                  text='Adet', height=700)
                fig_ilce.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_ilce, use_container_width=True)
            else:
                st.warning("Seçilen kriterlere uygun veri bulunamadı.")

            st.divider()
            
            # --- GAP ANALİZİ (BOŞ OLAN İLÇELER) ---
            st.subheader("⚠️ Varlık Gösterilmeyen İlçeler (Fırsatlar)")
            st.markdown("Seçtiğiniz şehirlerde bulunan ancak **seçili şirketlerin hiç bayisinin olmadığı** ilçeler aşağıdadır.")
            
            # 1. Seçilen şehirlerin TÜM ilçelerini bul (Ana Dataframe'den)
            tum_ilceler_ref = df[df['İl'].isin(selected_cities)]['İlçe'].unique()
            
            # 2. Şu an filtrelenen (gösterilen) ilçeleri bul
            mevcut_ilceler = df_filtered['İlçe'].unique()
            
            # 3. Farkı al (Set işlemi)
            bos_ilceler = set(tum_ilceler_ref) - set(mevcut_ilceler)
            
            if bos_ilceler:
                bos_ilceler_list = sorted(list(bos_ilceler))
                st.error(f"Toplam **{len(bos_ilceler_list)}** ilçede hiç bayi yok!")
                
                # Güzel bir kutu içinde gösterelim
                cols = st.columns(4)
                for i, ilce in enumerate(bos_ilceler_list):
                    cols[i % 4].warning(f"📍 {ilce}")
            else:
                st.success("Tebrikler! Seçilen şehirlerin **TÜM** ilçelerinde varlık gösteriliyor.")

    # 5. HAM VERİ
    with tab_data:
        st.dataframe(df_filtered, use_container_width=True)


if __name__ == "__main__":
    main()
