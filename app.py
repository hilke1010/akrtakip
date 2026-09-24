

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import io
import time
import math
import networkx as nx
import pydeck as pdk
import random
from datetime import datetime, timedelta, date
from plotly.subplots import make_subplots

# Hamburger menüyü ve footer'ı gizleyen CSS kodu
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """
st.markdown(hide_menu_style, unsafe_allow_html=True)
# --- 1. SAYFA VE GENEL AYARLAR ---
st.set_page_config(
    page_title="EPDK Akaryakıt Pazar Analizi",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 🎬 YENİ: SİNEMATİK AÇILIŞ ANİMASYONU (PRO)
# ==========================================
def show_cinematic_intro(df):
    """
    Kullanıcının isteği üzerine:
    1. 'Veri Analiz Ediliyor' (2 sn sabit)
    2. Kritik verilerin seri geçişi (3 sn flaş efektli)
    """
    # Session state kontrolü (Sadece ilk açılışta çalışsın)
    if 'intro_shown' not in st.session_state:
        st.session_state['intro_shown'] = False
    
    if st.session_state['intro_shown']:
        return

    # Gerçek verileri hesapla (Animasyonda kullanacağız)
    total_stations = len(df)
    total_companies = df['Dağıtım Şirketi'].nunique()
    total_cities = df['İl'].nunique()
    
    placeholder = st.empty()
    
    # --- CSS TASARIMI (MATRIX / TERMINAL TARZI) ---
    st.markdown("""
    <style>
    .intro-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100vh;
        background-color: #000000; z-index: 999999;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        font-family: 'Courier New', monospace; letter-spacing: 2px;
    }
    .main-text {
        font-size: 2.5em; font-weight: 900; color: #00ff41;
        text-shadow: 0 0 10px #00ff41;
        text-transform: uppercase;
        margin-bottom: 20px;
    }
    .sub-text {
        font-size: 1.2em; color: #ffffff; opacity: 0.8;
    }
    .blink { animation: blinker 1s linear infinite; }
    @keyframes blinker { 50% { opacity: 0; } }
    
    /* Hızlı veri akış efekti için */
    .data-flash {
        font-size: 3em; font-weight: bold; color: #00ff41;
        text-shadow: 0 0 20px #00ff41;
        animation: popIn 0.2s ease-out;
    }
    @keyframes popIn {
        0% { transform: scale(0.5); opacity: 0; }
        100% { transform: scale(1); opacity: 1; }
    }
    </style>
    """, unsafe_allow_html=True)

    # --- AŞAMA 1: SİSTEME BAĞLANILIYOR (2 SANİYE) ---
    with placeholder.container():
        st.markdown("""
        <div class="intro-overlay">
            <div class="main-text blink">🔌 VERİ ANALİZ EDİLİYOR...</div>
            <div class="sub-text">GÜVENLİ HAT OLUŞTURULUYOR</div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(2.0) # Tam 2 saniye bekle

    # --- AŞAMA 2: VERİLERİN SERİ GEÇİŞİ (3 SANİYE TOPLAM) ---
    # Sırayla gösterilecek veriler
    sequence = [
        ("📂 VERİ TABANI OKUNDU", f"{total_stations:,} İSTASYON"),
        ("🏢 REKABET ANALİZİ", f"{total_companies} DAĞITIM ŞİRKETİ"),
        ("🌍 COĞRAFİ KAPSAM", f"{total_cities} İL TARANDI"),
        ("✅ YETKİ KONTROLÜ", "ERİŞİM ONAYLANDI")
    ]
    
    step_time = 3.0 / len(sequence) # 3 saniyeyi adım sayısına böl

    for title, value in sequence:
        with placeholder.container():
            st.markdown(f"""
            <div class="intro-overlay">
                <div class="sub-text">{title}</div>
                <div class="data-flash">{value}</div>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(step_time)

    # Temizle ve bayrağı kaldır
    placeholder.empty()
    st.session_state['intro_shown'] = True


# --- HAVERSINE (MESAFE HESAPLAMA) FONKSİYONU ---
