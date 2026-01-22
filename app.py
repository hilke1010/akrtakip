import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
import io
import time
# DÜZELTME: Datetime hatasını önleyen import yapısı
from datetime import datetime, timedelta, date

# --- 1. SAYFA VE GENEL AYARLAR ---
st.set_page_config(
    page_title="EPDK Akaryakıt Pazar Analizi",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="collapsed" 
)

# --- DOSYA TARİHİ HESAPLAMA (TÜRKİYE SAATİ GMT+3) ---
def get_file_last_modified(file_path):
    try:
        if not os.path.exists(file_path):
            return "DOSYA BULUNAMADI"
        
        # Dosyanın değiştirilme zamanı
        timestamp = os.path.getmtime(file_path)
        
        # UTC zamanını al
        utc_time = datetime.utcfromtimestamp(timestamp)
        
        # Türkiye Saati (GMT+3)
        turkey_time = utc_time + timedelta(hours=3)
        
        tr_months = {
            1: 'OCAK', 2: 'ŞUBAT', 3: 'MART', 4: 'NİSAN', 5: 'MAYIS', 6: 'HAZİRAN',
            7: 'TEMMUZ', 8: 'AĞUSTOS', 9: 'EYLÜL', 10: 'EKİM', 11: 'KASIM', 12: 'ARALIK'
        }
        
        month_name = tr_months.get(turkey_time.month, "")
        # Format: 23 OCAK 2026 SAAT 14:30
        return f"{turkey_time.day} {month_name} {turkey_time.year} SAAT {turkey_time.strftime('%H:%M')}"
    except:
        return "TARİH ALINAMADI"


# ==========================================
# 🎬 CAFCAFLI YÜKLEME ANİMASYONU
# ==========================================
def show_intro_animation():
    if 'intro_played' not in st.session_state:
        st.session_state['intro_played'] = False

    if st.session_state['intro_played']:
        return

    placeholder = st.empty()
    
    with placeholder.container():
       st.markdown("""
<div class='insight-box-danger'>
    <div style="font-size:1.1em; font-weight:bold; margin-bottom:10px;">
        ⚠️ Kritik Yenileme Dönemleri
    </div>
    <ul style="padding-left:20px; margin:0;">
        <li style="margin-bottom:8px;">
            <span style="color:#c0392b; font-weight:bold;">2027</span>: Toplam <b>435</b> Bayi
        </li>
        <li style="margin-bottom:8px;">
            <span style="color:#c0392b; font-weight:bold;">2028</span>: Toplam <b>461</b> Bayi
        </li>
        <li style="margin-bottom:8px;">
            <span style="color:#c0392b; font-weight:bold;">2029</span>: Toplam <b>455</b> Bayi
        </li>
         <li style="margin-bottom:8px;">
            <span style="color:#c0392b; font-weight:bold;">2030</span>: Toplam <b>762</b> Bayi
        </li>
    </ul>
</div>
""", unsafe_allow_html=True)
       time.sleep(2.0)
    
    placeholder.empty()
    st.session_state['intro_played'] = True


# --- PERFORMANS AYARLARI ---
MAX_ROW_DISPLAY = 1000  
MAX_MAP_POINTS = 50000 
PREVIEW_ROW_LIMIT = 100
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
    .district-chip:hover { background-color: #e2e6ea; border-color: #adb5bd; }
    .filter-container { background-color: #e3f2fd; padding: 15px; border-radius: 10px; border: 1px solid #bbdefb; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# --- 4. KOORDİNAT VERİTABANI ---
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
    if not os.path.exists(file_path): return None, None, None
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
        
        start_col = 'Dağıtıcı ile Yapılan Sözleşme Başlangıç Tarihi'
        if start_col not in df.columns: start_col = 'Lisans Başlangıç Tarihi'

        today = pd.to_datetime(date.today())
        
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

        if start_col in df.columns and target_col in df.columns:
            df['Sozlesme_Suresi_Gun'] = (df[target_col] - df[start_col]).dt.days
        else:
            df['Sozlesme_Suresi_Gun'] = np.nan

        def get_risk(days):
            if pd.isna(days): return "Bilinmiyor"
            if days < 0: return "SÜRESİ DOLDU 🚨"
            if days < 90: return "KRİTİK (<3 Ay) ⚠️"
            if days < 180: return "YAKLAŞIYOR (<6 Ay) ⏳"
            return "GÜVENLİ ✅"
        df['Risk_Durumu'] = df['Kalan_Gun'].apply(get_risk)

        if 'İl' in df.columns: df['İl'] = df['İl'].astype(str).str.upper().str.replace('i', 'İ').str.replace('ı', 'I')
        if 'İlçe' in df.columns: df['İlçe'] = df['İlçe'].astype(str).str.upper().str.replace('i', 'İ').str.replace('ı', 'I')
        return df, target_col, start_col
    except Exception as e: return None, str(e), None

# --- DETAY TABLOSU ---
def show_details_table(dataframe, target_date_col, extra_cols=None):
    if dataframe is None or dataframe.empty:
        st.info("Seçilen kriterlere uygun kayıt bulunamadı.")
        return
    record_count = len(dataframe)
    
    if record_count > MAX_ROW_DISPLAY:
        st.markdown(f"<div class='warning-box'>⚠️ <b>Performans Uyarısı:</b> Listede toplam <b>{record_count:,}</b> kayıt var.<br>Tarayıcınızın donmaması için aşağıda sadece ilk <b>{MAX_ROW_DISPLAY:,}</b> tanesi gösterilmektedir.<br>Tüm listeyi görmek için lütfen aşağıdaki <b>Excel İndir</b> butonunu kullanın.</div>", unsafe_allow_html=True)
        display_df_limit = dataframe.head(MAX_ROW_DISPLAY)
    else:
        display_df_limit = dataframe

    cols = ['Unvan', 'İl', 'İlçe', 'Dağıtım Şirketi', target_date_col, 'Kalan_Gun', 'Sozlesme_Suresi_Gun', 'Risk_Durumu']
    if extra_cols:
        cols.extend(extra_cols)
    
    seen = set()
    final_cols = [c for c in cols if c in display_df_limit.columns and not (c in seen or seen.add(c))]
    
    display_df = display_df_limit[final_cols].copy()
    
    date_columns = [col for col in display_df.columns if "Tarihi" in col or "Tarih" in col]
    for date_col in date_columns:
        try: display_df[date_col] = pd.to_datetime(display_df[date_col]).dt.strftime('%d.%m.%Y')
        except: pass

    if 'Kalan_Gun' in display_df.columns: display_df = display_df.sort_values('Kalan_Gun')
    
    def highlight_risk(val):
        if not isinstance(val, (int, float)): return ''
        if val < 0: return 'background-color: #ffcccc'
        elif val < 90: return 'background-color: #ffe5cc'
        elif val < 180: return 'background-color: #ffffcc'
        return ''
    
    st.markdown(f"**📋 Listelenen Bayi Sayısı:** {len(display_df)}")
    
    if record_count > 0:
        buffer = io.BytesIO()
        try:
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                dataframe.to_excel(writer, index=False, sheet_name='Bayi Listesi')
            st.download_button(label=f"📥 Tüm Listeyi Excel İndir ({record_count} Kayıt)", data=buffer.getvalue(), file_name="Bayi_Listesi.xlsx", mime="application/vnd.ms-excel")
        except: pass

    if 'Kalan_Gun' in display_df.columns:
        st.dataframe(display_df.style.map(highlight_risk, subset=['Kalan_Gun']), use_container_width=True, hide_index=True)
    else:
        st.dataframe(display_df, use_container_width=True, hide_index=True)

# ==========================================
# 🛠️ HER TAB İÇİN BAĞIMSIZ FİLTRE FONKSİYONU
# ==========================================
def create_tab_filters(df, key_prefix):
    """
    Bu fonksiyon her sekme için bağımsız filtreler oluşturur ve filtrelenmiş veriyi döndürür.
    """
    with st.expander("🔍 **Filtre Paneli (Bu Sekme İçin)**", expanded=True):
        st.markdown(f"<div class='filter-container'>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        
        # 1. BÖLGE
        with c1:
            region_opts = ["Tümü"] + list(BOLGE_TANIMLARI.keys())
            sel_reg = st.selectbox("🌍 Bölge", region_opts, key=f"{key_prefix}_reg")
        
        filtered_by_reg = df.copy()
        if sel_reg != "Tümü":
            filtered_by_reg = df[df['İl'].isin(BOLGE_TANIMLARI[sel_reg])]
            
        # 2. İL
        with c2:
            city_opts = sorted(filtered_by_reg['İl'].unique().tolist())
            sel_city = st.multiselect("🏢 İl", city_opts, key=f"{key_prefix}_city")

        filtered_by_city = filtered_by_reg.copy()
        if sel_city:
            filtered_by_city = filtered_by_reg[filtered_by_reg['İl'].isin(sel_city)]
            
        # 3. İLÇE
        with c3:
            dist_opts = sorted(filtered_by_city['İlçe'].unique().tolist()) if 'İlçe' in filtered_by_city.columns else []
            sel_dist = st.multiselect("📍 İlçe", dist_opts, key=f"{key_prefix}_dist")

        filtered_by_dist = filtered_by_city.copy()
        if sel_dist:
            filtered_by_dist = filtered_by_dist[filtered_by_dist['İlçe'].isin(sel_dist)]
            
        # 4. ŞİRKET
        with c4:
            comp_opts = sorted(filtered_by_dist['Dağıtım Şirketi'].dropna().astype(str).unique().tolist())
            sel_comp = st.multiselect("⛽ Şirket", comp_opts, key=f"{key_prefix}_comp")
            
        filtered_final = filtered_by_dist.copy()
        if sel_comp:
            filtered_final = filtered_final[filtered_final['Dağıtım Şirketi'].isin(sel_comp)]
            
        st.markdown("</div>", unsafe_allow_html=True)
            
    return filtered_final

# --- ANA UYGULAMA ---
def main():
    # 1. Animasyonu Oynat
    show_intro_animation()

    # 2. Verileri Yükle
    data_result = load_data(SABIT_DOSYA_ADI)
    if data_result is None or data_result[0] is None:
        st.error(f"⚠️ Hata: {data_result[1] if data_result else 'Veri Yüklenemedi'}")
        st.stop()
    df, target_date_col, start_date_col = data_result
    
    # 3. Dosyanın Son Değiştirilme Tarihini Al
    file_date_str = get_file_last_modified(SABIT_DOSYA_ADI)

    # --- SIDEBAR (SADECE BİLGİ, FİLTRE YOK) ---
    with st.sidebar:
        st.success(f"🔄 **VERİ GÜNCELLEME:**\n\n{file_date_str}")
        st.info(f"📧 **İletişim:**\n\nkerim.aksu@milangaz.com.tr")
        st.markdown("---")
        st.header("🔗 Diğer Uygulamalar")
        st.markdown("[📊 EPDK LPG Sektör Raporu](https://pazarpayi.streamlit.app/)")
        st.markdown("[📰 Haber Aracı](https://newslpg.streamlit.app/)")
        st.markdown("[📱 Mobil Hesaplayıcı](https://lpg2026.streamlit.app/)")

    # --- GLOBAL KPI (TÜM VERİTABANI ÖZETİ) ---
    st.title("🚀 Akaryakıt Pazar & Risk Analizi")
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Veri Tabanı", f"{len(df):,}")
    c2.metric("Aktif Şirket", df['Dağıtım Şirketi'].nunique() if 'Dağıtım Şirketi' in df.columns else 0)
    acil_durum = len(df[df['Kalan_Gun'] < 90]) if 'Kalan_Gun' in df.columns else 0
    c3.metric("Kritik Durum (Toplam)", acil_durum, delta="Acil Yenileme", delta_color="inverse")

    st.divider()

    # --- SEKMELER ---
    tab_overview, tab_machine, tab_compare, tab_sim, tab_calendar, tab_radar, tab_ilce, tab_report, tab_crm, tab_data = st.tabs([
        "📊 Bölgesel & Durum",
        "🤖 Makine Analizi",     
        "⚔️ Karşılaştırma (Vs.)", 
        "🔮 Simülasyon",         
        "📅 Takvim",
        "📡 Sözleşme Radar", 
        "📍 İlçe Penetrasyonu",
        "📄 İl Karnesi", 
        "📝 CRM Lite",            
        "📋 Ham Veri"
    ])

    # 1. BÖLGESEL & DURUM
    with tab_overview:
        st.subheader("🗺️ Bölgesel Yoğunluk Haritası")
        
        # TAB İÇİ FİLTRELEME
        df_tab1 = create_tab_filters(df, "tab1")
        
        if len(df_tab1) > MAX_MAP_POINTS:
            st.warning(f"⚠️ Haritada {len(df_tab1):,} nokta var. Performans için filtreleyin.")
        elif not df_tab1.empty:
            map_data = df_tab1['İl'].value_counts().reset_index()
            map_data.columns = ['İl', 'Adet']
            map_data['lat'] = map_data['İl'].map(lambda x: CITY_COORDINATES.get(x, [None, None])[0])
            map_data['lon'] = map_data['İl'].map(lambda x: CITY_COORDINATES.get(x, [None, None])[1])
            map_data = map_data.dropna(subset=['lat', 'lon'])

            if not map_data.empty:
                fig_map = px.scatter_mapbox(
                    map_data, lat="lat", lon="lon", size="Adet", color="Adet",
                    hover_name="İl", size_max=35, zoom=5, 
                    mapbox_style="open-street-map", color_continuous_scale=px.colors.sequential.Bluered,
                    title="İl Bazlı Bayi Yoğunluğu"
                )
                fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
                st.plotly_chart(fig_map, use_container_width=True)
                st.info("ℹ️ **Lejand:** 🔴 Koyu = Yüksek Yoğunluk, 🔵 Açık = Düşük Yoğunluk, ⚪ Büyüklük = İstasyon Sayısı")

        st.divider()
        st.subheader("📊 İstatistikler")
        
        city_stats = df_tab1['İl'].value_counts().reset_index()
        city_stats.columns = ['İl', 'Total']
        
        # Şirket seçildiyse ona göre, seçilmediyse en büyüğe göre etiketleme
        top_comp_name = df_tab1['Dağıtım Şirketi'].value_counts().idxmax() if not df_tab1.empty else "Bilinmiyor"
        top_comp_df = df_tab1[df_tab1['Dağıtım Şirketi'] == top_comp_name]
        top_counts = top_comp_df['İl'].value_counts().reset_index()
        top_counts.columns = ['İl', 'Top_Count']
        
        merged_stats = pd.merge(city_stats, top_counts, on='İl', how='left').fillna(0)
        
        def get_bar_label(row):
            total = int(row['Total'])
            return f"<b>{total}</b>"
        
        merged_stats['Label'] = merged_stats.apply(get_bar_label, axis=1)
        fig_city = px.bar(merged_stats, x='İl', y='Total', text='Label', title="Şehir Sıralaması (Toplam)", color='Total', color_continuous_scale='Blues')
        fig_city.update_traces(textposition='outside', cliponaxis=False)
        fig_city.update_layout(yaxis=dict(title='Toplam Bayi Sayısı'), margin=dict(t=50, b=100))
        st.plotly_chart(fig_city, use_container_width=True, on_select="rerun", key="overview_bar_chart")

        st.markdown("---")
        
        col_pie1, col_pie2 = st.columns(2)
        with col_pie1:
            # DÜZELTME: SADECE TOP 15 İLİ GÖSTER, "DİĞER" OLUŞTURMA
            city_pie_data = df_tab1['İl'].value_counts().reset_index()
            city_pie_data.columns = ['İl', 'Adet']
            # İlk 15'i alıyoruz, geri kalanı ("Diğer") eklemiyoruz
            city_pie_data = city_pie_data.head(15) 
            
            fig_city_pie = px.pie(city_pie_data, values='Adet', names='İl', hole=0.4, title="Şehir Dağılımı (Top 15)")
            st.plotly_chart(fig_city_pie, use_container_width=True)

        with col_pie2:
            if 'Dağıtım Şirketi' in df_tab1.columns:
                dist_pie_data = df_tab1['Dağıtım Şirketi'].value_counts().reset_index()
                dist_pie_data.columns = ['Dağıtım Şirketi', 'Adet']
                # Burada da karmaşayı önlemek için ilk 15'i gösterebiliriz
                dist_pie_data = dist_pie_data.head(15)
                fig_dist_pie = px.pie(dist_pie_data, values='Adet', names='Dağıtım Şirketi', hole=0.4, title="Pazar Payı (Top 15)")
                st.plotly_chart(fig_dist_pie, use_container_width=True)

        show_details_table(df_tab1, target_date_col)

    # 2. MAKİNE ANALİZİ
    with tab_machine:
        st.subheader("🤖 Makine Analizi (Akıllı Asistan)")
        
        # TAB İÇİ FİLTRELEME
        df_tab2 = create_tab_filters(df, "tab2")
        
        if df_tab2.empty:
            st.warning("⚠️ Seçilen kriterlere uygun veri bulunamadı. Lütfen filtreyi değiştirin.")
        else:
            # ARTIK "GÜZEL ENERJİ" ŞARTI YOK. Filtrede ne varsa o analiz edilir.
            
            # 1. En Güçlü Şehir
            top_city = df_tab2['İl'].value_counts().idxmax()
            top_city_count = df_tab2['İl'].value_counts().max()
            st.markdown(f"<div class='insight-box-success'><b>🏆 Filtre Lider Bölgesi:</b><br>Mevcut seçimdeki en yoğun il <b>{top_city}</b> ({top_city_count} Bayi).</div>", unsafe_allow_html=True)

            # 2. Eksik İlçe Analizi (Filtrelenen iller içinde, filtrelenen şirketlerin olmadığı yerler)
            selected_cities_in_filter = df_tab2['İl'].unique()
            all_possible_districts = df[df['İl'].isin(selected_cities_in_filter)]['İlçe'].unique()
            current_districts = df_tab2['İlçe'].unique()
            
            missing_districts = sorted(list(set(all_possible_districts) - set(current_districts)))
            district_market_size = df[df['İl'].isin(selected_cities_in_filter)]['İlçe'].value_counts()

            if len(missing_districts) > 0:
                st.markdown(f"<div class='insight-box-warning'><b>🚀 Büyüme Fırsatları (Boş Noktalar):</b><br>Seçtiğiniz kapsama alanında (İller) toplam <b>{len(missing_districts)}</b> ilçede şu anki filtrenize ait bayi bulunmuyor.</div>", unsafe_allow_html=True)
                with st.expander("📄 Tüm Eksik İlçeleri Listele (Üzerine Gelip Pazar Büyüklüğünü Görün)", expanded=False):
                    html_chips = ""
                    for dist in missing_districts:
                        total_stations = district_market_size.get(dist, 0)
                        tooltip_text = f"{dist}: Mevcut 0, Toplam Pazar: {total_stations} Bayi"
                        html_chips += f'<span class="district-chip" title="{tooltip_text}">{dist}</span>'
                    st.markdown(html_chips, unsafe_allow_html=True)
            
            # 3. Sözleşme Bitiş Analizi
            if 'Bitis_Yili' in df_tab2.columns:
                current_year = datetime.now().year
                future_expirations = df_tab2[df_tab2['Bitis_Yili'] >= current_year]['Bitis_Yili'].value_counts().sort_index()
                if not future_expirations.empty:
                    msg_list = "<ul>"
                    total_future = 0
                    for year, count in future_expirations.items():
                        yr_text = f"{int(year)} (Bu Yıl)" if year == current_year else f"{int(year)}"
                        msg_list += f"<li><b>{yr_text}:</b> {count} adet sözleşme</li>"
                        total_future += count
                    msg_list += "</ul>"
                    st.markdown(f"<div class='insight-box-danger'><b>⚠️ Kritik Yenileme Dönemleri (Seçili Kapsam):</b><br>Toplamda <b>{total_future}</b> sözleşme sona erecek.<br>{msg_list}</div>", unsafe_allow_html=True)
            
            # 4. Pasta Grafiği (Filtre içindeki dağılım)
            col_share_text, col_share_chart = st.columns([1, 1])
            with col_share_text:
                total_in_filter = len(df_tab2)
                unique_companies = df_tab2['Dağıtım Şirketi'].nunique()
                st.markdown(f"<div class='insight-box-info'><b>📊 Filtre Özeti:</b><br>Toplam İstasyon: <b>{total_in_filter}</b><br>Bulunan Şirket Sayısı: <b>{unique_companies}</b></div>", unsafe_allow_html=True)
            with col_share_chart:
                comp_dist = df_tab2['Dağıtım Şirketi'].value_counts().reset_index()
                comp_dist.columns = ['Şirket', 'Adet']
                fig_my_share = px.pie(comp_dist, names='Şirket', values='Adet', hole=0.5, title=f"Seçim İçi Dağılım")
                fig_my_share.update_layout(margin=dict(t=30, b=0, l=0, r=0))
                st.plotly_chart(fig_my_share, use_container_width=True)

    # 3. KARŞILAŞTIRMA (VS.)
    with tab_compare:
        st.subheader("⚔️ Head-to-Head Rakip Analizi")
        st.info("Aşağıdaki filtreden **Bölge/İl/İlçe** seçerek arenayı daraltabilirsiniz. Şirket karşılaştırması filtrenin altındadır.")
        
        # TAB İÇİ FİLTRELEME (Şirket hariç, şirketler aşağıda seçilecek)
        df_tab3 = create_tab_filters(df, "tab3")

        if 'Dağıtım Şirketi' in df.columns:
            comp_list = sorted(df['Dağıtım Şirketi'].dropna().astype(str).unique().tolist())
            if len(comp_list) >= 2:
                c_sel1, c_sel2 = st.columns(2)
                comp_a = c_sel1.selectbox("1. Şirket (Taraf A)", comp_list, index=0, key="comp_a_sel")
                comp_b = c_sel2.selectbox("2. Şirket (Taraf B)", comp_list, index=1 if len(comp_list)>1 else 0, key="comp_b_sel")
                
                df_a = df_tab3[df_tab3['Dağıtım Şirketi'] == comp_a]
                df_b = df_tab3[df_tab3['Dağıtım Şirketi'] == comp_b]

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
                df_vs = df_tab3[df_tab3['Dağıtım Şirketi'].isin([comp_a, comp_b])]
                if not df_vs.empty:
                    city_vs = df_vs.groupby(['İl', 'Dağıtım Şirketi']).size().reset_index(name='Adet')
                    fig_vs = px.bar(city_vs, x='İl', y='Adet', color='Dağıtım Şirketi', barmode='group', title="Tüm Şehirlerde Karşılaştırma")
                    st.plotly_chart(fig_vs, use_container_width=True)
            else: st.warning("Yeterli veri yok.")

    # 4. SİMÜLASYON
    with tab_sim:
        st.subheader("🔮 'What-If' Senaryo Analizi")
        
        # TAB İÇİ FİLTRELEME
        sim_df = create_tab_filters(df, "tab4")
        
        st.markdown("---")
        
        all_comp = sorted(df['Dağıtım Şirketi'].dropna().astype(str).unique().tolist())
        
        col_s1, col_s2 = st.columns(2)
        my_comp = col_s1.selectbox("Sizin Şirketiniz", all_comp, index=0, key="sim_my_comp")
        target_comps = [c for c in all_comp if c != my_comp]
        target = col_s2.selectbox("Hedef Rakip", target_comps, key="sim_target_comp")
        
        rate = st.slider("Dönüşüm Oranı (%)", 0, 100, 10, key="sim_rate_slider")
        
        if target:
            curr = len(sim_df[sim_df['Dağıtım Şirketi'] == my_comp])
            targ = len(sim_df[sim_df['Dağıtım Şirketi'] == target])
            gain = int(targ * rate / 100)
            new = curr + gain
            
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("Mevcut", curr)
            sc2.metric("Kazanılacak", f"+{gain}")
            sc3.metric("Yeni Toplam", new, delta=f"%{((new-curr)/curr*100) if curr else 100:.1f}")
            
            st.markdown(f"""
            <div class="insight-box-info">
                🧮 <b>Hesaplama Detayı:</b><br>
                Seçilen filtrede, <b>{target}</b> firmasının toplam <b>{targ}</b> bayisi bulunmaktadır.<br>
                Siz <b>%{rate}</b> oranında dönüşüm hedeflediğiniz için:<br>
                <code>{targ} x {rate/100} = {gain}</code> adet yeni bayi kazanımı öngörülmektedir.
            </div>
            """, unsafe_allow_html=True)

    # 5. TAKVİM
    with tab_calendar:
        st.subheader("📅 Aylık Sözleşme Takvimi")
        
        # TAB İÇİ FİLTRELEME
        df_tab5 = create_tab_filters(df, "tab5")

        if 'Bitis_Yili' in df_tab5.columns:
            yrs = sorted(df_tab5['Bitis_Yili'].dropna().unique().astype(int).tolist())
            if yrs:
                curr_yr = datetime.now().year
                sel_yr = st.selectbox("Yıl", yrs, index=yrs.index(curr_yr) if curr_yr in yrs else 0, key="cal_year")
                df_yr = df_tab5[df_tab5['Bitis_Yili'] == sel_yr]
                if not df_yr.empty:
                    m_cnt = df_yr.groupby(['Bitis_Ayi_No']).agg(Adet=('Unvan','count'), Ay=('Bitis_Ayi','first')).reset_index().sort_values('Bitis_Ayi_No')
                    fig_cal = px.bar(m_cnt, x='Ay', y='Adet', text='Adet', title=f"{sel_yr} Dağılımı")
                    sel = st.plotly_chart(fig_cal, use_container_width=True, on_select="rerun", key="cal_sel")
                    st.caption("ℹ️ *👇 Grafiğin çubuklarına tıklayarak aşağıdaki listeyi filtreleyebilirsiniz.*")
                    if sel and sel['selection']['points']:
                        mn = sel['selection']['points'][0]['x']
                        st.success(f"🗓️ **{mn} {sel_yr}**")
                        show_details_table(df_yr[df_yr['Bitis_Ayi']==mn], target_date_col)
                    else: show_details_table(df_yr, target_date_col)

    # 6. SÖZLEŞME RADAR
    with tab_radar:
        st.subheader("📡 Sözleşme Radar (Kısa Süreli Anlaşmalar)")
        st.markdown("Sözleşme Başlangıç ve Bitiş tarihi arasında **3 Aydan (90 gün) az** süre olan kayıtları listeler.")
        
        # TAB İÇİ FİLTRELEME
        radar_base_df = create_tab_filters(df, "tab6")
        
        if 'Sozlesme_Suresi_Gun' in radar_base_df.columns and start_date_col:
            radar_df = radar_base_df[(radar_base_df['Sozlesme_Suresi_Gun'] < 90) & (radar_base_df['Sozlesme_Suresi_Gun'] >= 0)]
            if not radar_df.empty:
                st.error(f"⚠️ Toplam **{len(radar_df)}** adet 3 aydan kısa süreli sözleşme tespit edildi.")
                extra_cols = ['Dağıtıcı ile Yapılan Sözleşme Başlangıç Tarihi', 'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi', 'Sozlesme_Suresi_Gun']
                if start_date_col not in extra_cols: extra_cols[0] = start_date_col
                show_details_table(radar_df, target_date_col, extra_cols=extra_cols)
            else:
                st.success("✅ Seçilen kriterlerde 3 aydan kısa süreli (şüpheli) sözleşme bulunmamaktadır.")
        else:
            st.warning("Veri setinde Başlangıç Tarihi sütunu bulunamadı.")

    # 7. İLÇE PENETRASYONU
    with tab_ilce:
        st.subheader("📍 İlçe Bazlı Derinlik")
        
        # TAB İÇİ FİLTRELEME
        df_tab7 = create_tab_filters(df, "tab7")

        if not df_tab7.empty:
            d_cnt = df_tab7.groupby(['İlçe']).size().reset_index(name='Adet').sort_values('Adet', ascending=True)
            fig_ilce = px.bar(d_cnt, x='Adet', y='İlçe', orientation='h', text='Adet', height=600)
            sel_ilce = st.plotly_chart(fig_ilce, use_container_width=True, on_select="rerun", key="ilce_sel")
            st.caption("ℹ️ *👇 Grafiğin çubuklarına tıklayarak aşağıdaki listeyi filtreleyebilirsiniz.*")
            if sel_ilce and sel_ilce['selection']['points']:
                dst = sel_ilce['selection']['points'][0]['y']
                st.success(f"📍 **{dst}**")
                show_details_table(df_tab7[df_tab7['İlçe']==dst], target_date_col)
            else: show_details_table(df_tab7, target_date_col)
            
            st.divider()
            
            # Seçili illerde hiç olmayan ilçeleri bulma mantığı
            all_d = df[df['İl'].isin(df_tab7['İl'].unique())]['İlçe'].unique()
            curr_d = df_tab7['İlçe'].unique()
            miss = sorted(list(set(all_d) - set(curr_d)))
            if miss:
                st.markdown("#### ⚠️ Hiç Bayi Olmayan İlçeler (Seçili İller İçinde)")
                cols = st.columns(4)
                for i, d in enumerate(miss): cols[i%4].warning(f"📍 {d}")

    # 8. İL KARNESİ
    with tab_report:
        st.subheader("📄 Tek Tuşla İl Karnesi")
        st.markdown("Seçilen ilin tüm kritik verilerini tek sayfada özetler.")
        
        # Burası özel bir sayfa olduğu için standart filtre yerine sadece İl seçimi koyuyoruz
        all_provinces = sorted(df['İl'].unique().tolist())
        report_city = st.selectbox("Karne Çıkarılacak İli Seçin:", all_provinces, key="report_city_sel")
        
        if report_city:
            city_df = df[df['İl'] == report_city]
            total_stations_city = len(city_df)
            
            competitors_city = city_df['Dağıtım Şirketi'].value_counts()
            market_leader = competitors_city.idxmax() if not competitors_city.empty else "Veri Yok"
            leader_count = competitors_city.max() if not competitors_city.empty else 0
            
            st.markdown("---")
            target_company_report = st.selectbox("Analiz Edilecek Şirket:", sorted(city_df['Dağıtım Şirketi'].unique()), index=0, key="report_comp_sel")
            
            my_city_df = city_df[city_df['Dağıtım Şirketi'] == target_company_report]
            my_city_count = len(my_city_df)
            
            st.markdown(f"<h1 style='text-align: center; color: #2980b9;'>{report_city} İLİ PAZAR KARNESİ</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center;'>Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y')}</p>", unsafe_allow_html=True)
            
            rk1, rk2, rk3 = st.columns(3)
            rk1.metric("Toplam İstasyon", total_stations_city)
            rk2.metric("Pazar Lideri", f"{leader_count} Bayi", help=market_leader)
            rk3.metric(f"{target_company_report}", my_city_count)
            
            st.divider()
            
            st.subheader(f"📅 {target_company_report} Sözleşme Bitiş Projeksiyonu")
            
            if not my_city_df.empty and 'Bitis_Yili' in my_city_df.columns:
                current_year = datetime.now().year
                future_expirations = my_city_df[my_city_df['Bitis_Yili'] >= current_year]['Bitis_Yili'].value_counts().sort_index()
                
                if not future_expirations.empty:
                    cols = st.columns(len(future_expirations))
                    for idx, (year, count) in enumerate(future_expirations.items()):
                        with cols[idx]:
                            st.markdown(f"""
                            <div class="year-box">
                                <div class="year-title">{int(year)}</div>
                                <div class="year-count">{count}</div>
                                <div style="font-size:0.8em; color:#666;">Sözleşme</div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    st.divider()
                    st.markdown("### 📋 Detaylı Bitiş Listesi")
                    st.dataframe(my_city_df[['Unvan', 'İlçe', 'Bitis_Ayi', 'Bitis_Yili', 'Kalan_Gun']].sort_values('Kalan_Gun'), use_container_width=True, hide_index=True)
                else:
                    st.success("Bu ilde yakın zamanda bitecek sözleşmeniz bulunmamaktadır.")
            else:
                st.warning("Bu ilde seçilen şirketin bayisi bulunmamaktadır.")

            st.divider()
            
            rc1, rc2 = st.columns(2)
            with rc1:
                st.subheader("Dağıtıcı Pazar Payı")
                if not competitors_city.empty:
                    top_comp = competitors_city.head(7).reset_index()
                    top_comp.columns = ['Şirket', 'Adet']
                    fig_rep_pie = px.pie(top_comp, values='Adet', names='Şirket', hole=0.4)
                    st.plotly_chart(fig_rep_pie, use_container_width=True)
            
            with rc2:
                st.subheader("İlçe Dağılımı")
                dist_dist = city_df['İlçe'].value_counts().reset_index()
                dist_dist.columns = ['İlçe', 'Adet']
                fig_rep_bar = px.bar(dist_dist.head(10), x='Adet', y='İlçe', orientation='h', text='Adet')
                st.plotly_chart(fig_rep_bar, use_container_width=True)

    # 9. CRM LITE
    with tab_crm:
        st.subheader("📝 CRM Lite")
        
        # TAB İÇİ FİLTRELEME
        df_tab9 = create_tab_filters(df, "tab9")
        
        if not df_tab9.empty:
            bayiler = sorted(df_tab9['Unvan'].unique().tolist())
            cr1, cr2 = st.columns([1,2])
            with cr1:
                sel_b = st.selectbox("Bayi", bayiler, key="crm_bayi_sel")
                note = st.text_area("Not", height=100, key="crm_note")
                if st.button("Kaydet", type="primary", key="crm_save"):
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
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

    # 10. HAM VERİ
    with tab_data:
        st.subheader("📋 Ham Veri")
        
        # TAB İÇİ FİLTRELEME
        df_tab10 = create_tab_filters(df, "tab10")

        buf = io.BytesIO()
        try:
            with pd.ExcelWriter(buf, engine='xlsxwriter') as w: df_tab10.to_excel(w, index=False)
            st.download_button("📥 Tümünü İndir", buf.getvalue(), "Data.xlsx", "application/vnd.ms-excel", key="raw_dl")
        except: pass
        st.markdown(f"_Önizleme ({PREVIEW_ROW_LIMIT} satır)_")
        st.dataframe(df_tab10.head(PREVIEW_ROW_LIMIT), use_container_width=True)

if __name__ == "__main__":
    main()
