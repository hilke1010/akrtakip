                    count = row['Toplam İstasyon']
                    
                    with st.expander(f"🔻 {vkn} - {unvan} ({count} İstasyon)"):
                        # O gruba ait veriyi süz
                        sub_df = matrix_data[matrix_data[tax_col_name] == vkn]
                        # Gösterilecek kolonlar
                        disp_cols = ['Unvan', 'Dağıtım Şirketi', 'İl', 'İlçe', target_date_col]
                        final_cols = [c for c in disp_cols if c in sub_df.columns]
                        
                        # Tarih düzeltme
                        if target_date_col in sub_df.columns:
                             try: sub_df[target_date_col] = pd.to_datetime(sub_df[target_date_col]).dt.strftime('%d.%m.%Y')
                             except: pass
                        
                        st.dataframe(sub_df[final_cols], use_container_width=True, hide_index=True)
                    
        else:
            if not tax_col_name:
                st.error("Excel dosyasında 'Vergi No', 'VKN' veya benzeri bir sütun bulunamadı.")
            else:
                st.warning("Veri yok.")

    # 13. DETAYLI ARAMA [NEW]
    if active_tab == TAB_LABELS[12]:
        st.subheader("🔍 Detaylı Arama & Bayi Kimlik Kartı")
        st.info("💡 Aşağıdaki kutudan bayi seçimi yapın, sistem tüm bilgileri sizin için derlesin.")
        
        # 1. AKILLI ARAMA LİSTESİ OLUŞTURMA
        if 'Dağıtım Şirketi' in df.columns:
            dist_col = 'Dağıtım Şirketi'
        else:
            dist_col = df.columns[0] # Fallback
            
        df['Arama_Etiketi'] = df['Unvan'].astype(str) + " | " + df['İl'].astype(str) + " - " + df.get('İlçe', '').astype(str) + " (" + df[dist_col].astype(str) + ")"
        
        search_options = sorted(df['Arama_Etiketi'].unique().tolist())
        
        # Arama kutusu
        selected_label = st.selectbox(
            "🔎 Bayi Seçin (Yazmaya başlayın...):",
            options=[""] + search_options,
            index=0,
            placeholder="Örn: YILDIZ PETROL"
        )
        
        # 2. BAYİ KİMLİK KARTI (GÜVENLİ NATIVE KART)
        if selected_label:
            row = df[df['Arama_Etiketi'] == selected_label].iloc[0]
            
            # Verileri Çek
            unvan = row['Unvan']
            dagitici = row.get('Dağıtım Şirketi', '-')
            il = row.get('İl', '-')
            ilce = row.get('İlçe', '-')
            
            # Akıllı Adres Bulucu
            adres_col = None
            for c in df.columns:
                if "ADRES" in c.upper():
                    adres_col = c
                    break
            
            if adres_col:
                adres = row.get(adres_col)
                if pd.isna(adres) or str(adres).lower() == 'nan':
                    adres = f"{ilce} / {il} (Detay Yok)"
            else:
                adres = f"{ilce} / {il}"

            # Vergi No Bulucu
            vergi_no = '-'
            for c in df.columns:
                clean_c = c.upper().replace('İ','I')
                if "VERGI" in clean_c or "VKN" in clean_c:
                    vergi_no = row[c]
                    break
            
            # Tarihler (Hata veren yer burasıydı, düzeltildi)
            baslangic = row[start_date_col].strftime('%d.%m.%Y') if pd.notnull(row.get(start_date_col)) else "-"
            bitis = row[target_date_col].strftime('%d.%m.%Y') if pd.notnull(row.get(target_date_col)) else "-"
            kalan = int(row['Kalan_Gun']) if pd.notnull(row.get('Kalan_Gun')) else 0
            
            # --- NATIVE STREAMLIT KART TASARIMI ---
            # HTML yerine native kullanarak hatayı önlüyoruz
            with st.container(border=True):
                c_header1, c_header2 = st.columns([3, 1])
                with c_header1:
                    st.subheader(f"⛽ {unvan}")
                    st.caption(f"📍 {il} / {ilce}")
                with c_header2:
                    st.info(f"{dagitici}")

                st.divider()
                
                c_info1, c_info2 = st.columns(2)
                
                with c_info1:
                    st.markdown(f"**📍 Adres:** \n{adres}")
                    st.write("") # Boşluk
                    st.markdown(f"**🆔 Vergi / TC No:** \n`{vergi_no}`")
                
                with c_info2:
                    st.markdown(f"**📅 Sözleşme Başlangıç:** \n{baslangic}")
                    st.write("") # Boşluk
                    
                    # Renkli ve vurgulu bitiş tarihi
                    kalan_renk = "red" if kalan < 90 else "green"
                    st.markdown(f"**⏳ Sözleşme Bitiş:** \n{bitis} (:{kalan_renk}[**{kalan} Gün Kaldı**])")
                
                st.divider()
                st.success("📜 **Lisans Durumu:** AKTİF")

if __name__ == "__main__":
    main()
