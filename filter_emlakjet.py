import pandas as pd

# ---- AYAR KISMI ----
# Girdi ve çıktı dosya adlarını buradan ayarla
INPUT_FILE  = "emlak_ozet_turkiye.xlsx"          # elindeki asıl dosya
OUTPUT_FILE = "ilanlar_emlakjet.xlsx" # filtrelenmiş yeni dosya

# ---- İŞLEM KISMI ----

def main():
    # 1) Excel dosyasını oku
    # Eğer sayfa adı farklıysa sheet_name parametresini değiştirebilirsin
    df = pd.read_excel(INPUT_FILE)  # varsayılan: ilk sheet

    # 2) Sadece 'site' sütunu "emlakjet" olan satırları al
    # site sütun adı tam olarak resimdeki gibi 'site' ise bu çalışır
    emlakjet_df = df[df["site"] == "emlakjet"]

    # 3) Yeni Excel dosyasına yaz
    emlakjet_df.to_excel(OUTPUT_FILE, index=False)

    print(f"Toplam {len(emlakjet_df)} satır '{OUTPUT_FILE}' dosyasına kaydedildi.")

if __name__ == "__main__":
    main()
