from typing import List, Tuple
import os
import pandas as pd

from scrapers import (
    Listing,
    EmlakjetScraper,
    TapuScraper,
    HepsiemlakScraper,
)

from config_sites import (
    emlakjet_url,
    tapu_url,
    hepsiemlak_url,
)



def calculate_average_price(listings: List[Listing]) -> float:
    prices = [l.price for l in listings if l.price > 0]
    if not prices:
        return 0.0
    return sum(prices) / len(prices)


def run_for_location(city: str, district: str, limit: int = 10) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Tek bir şehir/ilçe için:
    - Emlakjet + Tapu'dan ilan çeker
    - Site site ortalamayı hesaplar
    - Detay DataFrame + özet DataFrame döner
    """

    sites = [
    #("Hepsiemlak", HepsiemlakScraper(), hepsiemlak_url(city, district)),
    ("Emlakjet", EmlakjetScraper(), emlakjet_url(city, district)),
    ("Tapu", TapuScraper(), tapu_url(city, district)),
]


    print("=== Emlak Ortalama Fiyat Hesaplama ===")
    print(f"{city} / {district} için her siteden {limit} ilana kadar çekilecek.\n")

    print("Oluşturulan URL'ler:")
    for name, _, url in sites:
        print(f"- {name}: {url}")
    print()

    all_listings: List[Listing] = []

    for name, scraper, url in sites:
        try:
            listings = scraper.fetch_listings(url, limit=limit)
        except Exception as e:
            print(f"[{name}] sırasında hata oluştu: {e}")
            continue

        if not listings:
            print(f"{name}: Hiç ilan bulunamadı (selector veya URL'yi kontrol et).")
            continue

        all_listings.extend(listings)

        site_avg = calculate_average_price(listings)
        print(f"{name}: {len(listings)} ilan, ortalama fiyat = {site_avg:,.0f} TL")

    if not all_listings:
        print("\nHiçbir siteden ilan çekilemedi.")
        # Boş DataFrame'ler döndürelim
        return pd.DataFrame(), pd.DataFrame()

    overall_avg = calculate_average_price(all_listings)
    print("\n========================================")
    print(f"{city} / {district} için toplam {len(all_listings)} ilanın")
    print(f"GENEL ortalama fiyatı: {overall_avg:,.0f} TL")
    print("========================================\n")

    # Detay DF (tüm ilanlar)
    detail_df = pd.DataFrame(
        [
            {
                "city": city,
                "district": district,
                "site": l.site,
                "title": l.title,
                "price": l.price,
                "url": l.url,
            }
            for l in all_listings
        ]
    )

    # Site site özet DF (sadece city, district, site, num_listings, avg_price)
    summary_rows = []
    for site, group in detail_df.groupby("site"):
        avg_price_site = group["price"].mean()
        count_site = len(group)

        summary_rows.append(
            {
                "city": city,
                "district": district,
                "site": site,
                "num_listings": int(count_site),
                "avg_price": round(avg_price_site, 2),
            }
        )

    summary_df = pd.DataFrame(summary_rows, columns=["city", "district", "site", "num_listings", "avg_price"])
    return summary_df, detail_df


def main():
    city = input("Şehir adı (örn. Adana): ").strip()
    district = input("İlçe adı (örn. Cukurova): ").strip()

    try:
        limit = int(input("Her siteden kaç ilan çekilsin? [varsayılan 10]: ") or "10")
    except ValueError:
        limit = 10

    summary_df, detail_df = run_for_location(city, district, limit=limit)

    if detail_df.empty:
        return

    # Detay CSV
    filename = f"sonuc_{city}_{district}.csv".replace(" ", "_")
    detail_df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"Detaylı tablo şu dosyaya kaydedildi: {filename}")

    # Özet Excel'e ekleme (tek dosya)
    excel_path = "emlak_ozet.xlsx"
    if os.path.exists(excel_path):
        old_df = pd.read_excel(excel_path)
        combined = pd.concat([old_df, summary_df], ignore_index=True)
    else:
        combined = summary_df

    combined.to_excel(excel_path, index=False)
    print(f"Site site özetler şu Excel dosyasına kaydedildi/eklenildi: {excel_path}")


if __name__ == "__main__":
    main()
