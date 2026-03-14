import pandas as pd

# Girdi dosyaları
FILES = [
    r"",
    r"",
]

# Çıktı dosyası yolu
OUTPUT_PATH = r""

def combine_and_save_to_excel(file_list, output_path):
    all_names = []
    
    for file_path in file_list:
        try:
            # Excel'i oku
            df = pd.read_excel(file_path)
            
            # Sütun isimlerini standartlaştır
            df.columns = [str(col).upper().strip() for col in df.columns]
            
            # Firma ismini içeren sütunu bul
            target_col = None
            possible_cols = ['FAAL FİRMA ADI', 'FİRMA ADI', 'FİRMA', 'COMPANY NAME']
            
            for col in possible_cols:
                if col in df.columns:
                    target_col = col
                    break
            
            if target_col:
                # Verileri temizle ve listeye ekle
                names = df[target_col].dropna().astype(str).str.strip().str.upper().tolist()
                all_names.extend(names)
                print(f"Başarıyla okundu: {file_path} ({len(names)} satır)")
            
        except Exception as e:
            print(f"Hata: {file_path} okunurken sorun çıktı: {e}")

    # Mükerrerleri sil ve alfabetik sırala
    unique_companies = sorted(list(set(all_names)))
    
    # Yeni bir DataFrame oluştur
    final_df = pd.DataFrame(unique_companies, columns=['FIRMA_ADI'])
    
    # Excel formatında kaydet
    try:
        final_df.to_excel(output_path, index=False)
        print("-" * 30)
        print(f"İŞLEM TAMAMLANDI!")
        print(f"Toplam benzersiz firma: {len(unique_companies)}")
        print(f"Kaydedilen dosya: {output_path}")
    except Exception as e:
        print(f"Dosya kaydedilirken hata oluştu: {e}")

# Fonksiyonu çalıştır
combine_and_save_to_excel(FILES, OUTPUT_PATH)