import re
import random
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from .base import BaseScraper, Listing

# Gerçek tarayıcı gibi görünmek için header
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}


class EmlakjetScraper(BaseScraper):
    site_name = "emlakjet"

    def _page_url(self, base_url: str, page: int) -> str:
        """
        1. sayfa: https://www.emlakjet.com/satilik-konut/adana-seyhan
        2. sayfa: https://www.emlakjet.com/satilik-konut/adana-seyhan?sayfa=2
        """
        if page == 1:
            return base_url
        return f"{base_url}?sayfa={page}"

    def _extract_total_count(self, soup: BeautifulSoup) -> Optional[int]:
        """
        Sayfa içindeki metinden toplam ilan sayısını çekmeye çalışır.
        Örn: '1.234 adet ilan bulundu' gibi bir yazı varsa onu yakalar.
        """
        text = soup.get_text(" ", strip=True)

        m = re.search(r"([\d\.]+)\s+adet\s+ilan\b", text, flags=re.IGNORECASE)
        if not m:
            return None

        raw_num = m.group(1)
        digits = re.sub(r"[^\d]", "", raw_num)
        if not digits:
            return None
        return int(digits)

    def fetch_listings(self, base_url: str, limit: int = 50, max_pages: int = 50) -> List[Listing]:
        """
        - Verilen arama URL’si için TÜM sayfalardaki ilanları gezer
        - /ilan/ içeren linklerden ilanları toplar
        - EN SON, tüm bu ilanlar arasından rastgele `limit` kadarını seçip döner.

        Yani:
        1) Tüm sayfalardan full ilan listesi (listings_all)
        2) random.sample(listings_all, limit) ile rastgele seçim
        """

        listings_all: List[Listing] = []
        seen_urls = set()
        page = 1
        total_from_site_printed = False  # toplam ilan sayısını sadece 1 kez basalım

        while page <= max_pages:
            url = self._page_url(base_url, page)
            resp = requests.get(url, headers=HEADERS, timeout=20)

            if resp.status_code != 200:
                print(f"[emlakjet] {url} için status code: {resp.status_code}")
                break

            soup = BeautifulSoup(resp.text, "html.parser")

            # İlk sayfada toplam ilan sayısını okumayı dene
            if page == 1 and not total_from_site_printed:
                total = self._extract_total_count(soup)
                if total is not None:
                    print(f"[emlakjet] Bu arama için sitede görünen TOPLAM ilan sayısı: {total}")
                else:
                    print("[emlakjet] Toplam ilan sayısı metinden okunamadı.")
                total_from_site_printed = True

            # href içinde /ilan/ geçen tüm linkler
            card_links = soup.find_all("a", href=re.compile(r"/ilan/"))
            if not card_links:
                print(f"[emlakjet] {url} sayfasında ilan linki bulunamadı. Muhtemelen son sayfa.")
                break

            page_new_count = 0

            for a in card_links:
                href = a.get("href")
                if not href:
                    continue

                # Tam URL yap
                if href.startswith("http"):
                    full_url = href
                else:
                    full_url = "https://www.emlakjet.com" + href

                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                # Link içindeki tüm yazıyı al
                text = " ".join(a.stripped_strings)
                if not text:
                    continue

                # Metinden fiyatı çek (örn: 8.750.000 TL)
                price_matches = re.findall(r"([\d\.]+)\s*TL", text)
                if not price_matches:
                    continue

                # Genelde son TL ifadesi gerçek fiyat
                price_str = price_matches[-1]
                digits = re.sub(r"[^\d]", "", price_str)
                if not digits:
                    continue

                price = int(digits)

                # Başlığı, fiyat kısmından önceki kısım olarak al
                price_pos = text.rfind(price_str)
                title = text[:price_pos].strip()

                listings_all.append(
                    Listing(
                        site=self.site_name,
                        title=title,
                        price=price,
                        url=full_url,
                    )
                )
                page_new_count += 1

            print(f"[emlakjet] {url} sayfasından {page_new_count} yeni ilan eklendi. "
                  f"Şu ana kadar TOPLAM {len(listings_all)} ilan toplandı.")

            page += 1  # sıradaki sayfaya geç

        if not listings_all:
            print("[emlakjet] Hiç ilan toplanamadı.")
            return []

        # Rastgele seçim
        sample_count = min(limit, len(listings_all))
        sampled_listings = random.sample(listings_all, sample_count)

        print(f"[emlakjet] Toplam {len(listings_all)} ilandan rastgele {sample_count} tanesi seçildi.")
        return sampled_listings
