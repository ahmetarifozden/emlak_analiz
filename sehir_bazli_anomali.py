import pandas as pd

# ===========================
#  AYARLAR
# ===========================
INPUT_FILE = "ilanlar_emlakjet.xlsx"
OUTPUT_FILE = "sehir_bazli_anomaliler.xlsx"

COL_CITY = "city"
COL_SITE = "site"
COL_PRICE = "avg_price"


def islem_bir_sehir(grp: pd.DataFrame) -> pd.DataFrame:
    g = grp.copy()

    prices = g[COL_PRICE]

    # IQR hesap
    Q1 = prices.quantile(0.25)
    Q3 = prices.quantile(0.75)
    IQR = Q3 - Q1

    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    # Z-score
    mean = prices.mean()
    std = prices.std(ddof=0)
    if std == 0:
        std = 1e-9

    g["zscore_city"] = (prices - mean) / std

    g["iqr_outlier"] = (prices < lower) | (prices > upper)
    g["zscore_outlier"] = g["zscore_city"].abs() >= 3

    # Genel flag
    g["outlier_flag"] = "normal"
    g.loc[g["iqr_outlier"] | g["zscore_outlier"], "outlier_flag"] = "iqr_or_z"
    g.loc[g["iqr_outlier"] & g["zscore_outlier"], "outlier_flag"] = "both"

    # Ek bilgi sütunları
    g["city_Q1"] = Q1
    g["city_Q3"] = Q3
    g["city_IQR"] = IQR
    g["city_lower_bound"] = lower
    g["city_upper_bound"] = upper
    g["city_mean"] = mean
    g["city_std"] = std

    return g


def main():
    # 1) Dosyayı oku
    df = pd.read_excel(INPUT_FILE)

    # 2) Sadece emlakjet
    if COL_SITE in df.columns:
        df = df[df[COL_SITE] == "emlakjet"].copy()

    # 3) Fiyatı numerik yap
    df[COL_PRICE] = pd.to_numeric(df[COL_PRICE], errors="coerce")
    df = df.dropna(subset=[COL_PRICE])

    # 4) Şehir bazlı analiz
    df_with_flags = df.groupby(COL_CITY, group_keys=False).apply(islem_bir_sehir)

    # 5) Sadece anormal ilçeler
    anomalies = df_with_flags[df_with_flags["outlier_flag"] != "normal"].copy()

    # 6) ÖZET TABLO
    ozet = df_with_flags["outlier_flag"].value_counts().reset_index()
    ozet.columns = ["flag_tipi", "adet"]

    total = len(df_with_flags)
    ozet.loc[len(ozet)] = ["toplam", total]

    # 7) Excel'e kaydet
    with pd.ExcelWriter(OUTPUT_FILE) as writer:
        df_with_flags.to_excel(writer, index=False, sheet_name="tum_ilceler")
        anomalies.to_excel(writer, index=False, sheet_name="anormal_ilceler")
        ozet.to_excel(writer, index=False, sheet_name="ozet")

    print("✅ İşlem tamamlandı!")
    print(f"➡ {OUTPUT_FILE} oluşturuldu.")
    print("✔ 'ozet' sayfasında normal / iqr_or_z / both adetleri yazıyor.")


if __name__ == "__main__":
    main()
