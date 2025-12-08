import time
import pandas as pd

from main import run_for_location

CSV_PATH = "il_ilce.csv"     # senin dosyan
EXCEL_PATH = "emlak_ozet_turkiye_hepsiemlak.xlsx"
LIMIT_PER_SITE = 10


def main():
    # CSV şu formatta:
    # il,ilce
    # Adana,Aladağ
    # Adana,Ceyhan
    # ...
    df_locs = pd.read_csv(CSV_PATH)

    all_summaries = []

    for idx, row in df_locs.iterrows():
        city = str(row["il"])
        district = str(row["ilce"])

        print(f"\n=== {idx+1}/{len(df_locs)}: {city} / {district} ===")

        try:
            summary_df, _ = run_for_location(city, district, limit=LIMIT_PER_SITE)
        except Exception as e:
            print(f"{city}/{district} sırasında hata: {e}")
            continue

        if summary_df.empty:
            print(f"{city}/{district} için özet veri yok, atlanıyor.")
            continue

        all_summaries.append(summary_df)

        # Siteleri yormamak için bekleme koy
        time.sleep(3)

    # Tüm özetleri birleştir
    if not all_summaries:
        print("\nHiç veri alınamadı.")
        return

    combined = pd.concat(all_summaries, ignore_index=True)
    combined.to_excel(EXCEL_PATH, index=False)

    print(f"\nTÜM İL/İLÇE SONUÇLARI {EXCEL_PATH} dosyasına kaydedildi.")


if __name__ == "__main__":
    main()
