import re
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from .base import BaseScraper, Listing
import sys 
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}


class TapuScraper(BaseScraper):
    site_name = "tapu"

    def _extract_total_count(self, soup: BeautifulSoup) -> Optional[int]:
        """
        Sayfa içindeki '9 sonuç' gibi yazıdan toplam ilan sayısını çekmeye çalışır.
        Hiç bulamazsak None döner.
        """
        text = soup.get_text(" ", strip=True)
        m = re.search(r"([\d\.]+)\s+sonuç\b", text, flags=re.IGNORECASE)
        if not m:
            return None
        raw = m.group(1)
        digits = re.sub(r"[^\d]", "", raw)
        if not digits:
            return None
        return int(digits)

    def fetch_listings(self, search_url: str, limit: int = 10) -> List[Listing]:
        """
        TAPU: Sadece İLK SAYFADAKİ ilanlara bakar.

        - search_url sayfasını çeker
        - href'i '/detay/' ile başlayan <a> linklerinden ilanları çıkarır
        - Sayfada yazan 'N sonuç' bilgisini kullanır:
            * N = 0 ise -> hiç ilan döndürmez (önerilen ilanları yok sayar)
            * N > 0 ise -> en fazla min(limit, N) kadar ilan alır
        """

        print(f"[{self.site_name}] {search_url} adresinden veri çekiliyor...")

        resp = requests.get(search_url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"[tapu] {search_url} için status code: {resp.status_code}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        # Toplam sonuç sayısını okumayı dene
        total = self._extract_total_count(soup)
        if total is not None:
            print(f"[tapu] Bu arama için sitede görünen TOPLAM ilan sayısı: {total}")
            if total == 0:
                print("[tapu] Bu arama için gerçek sonuç yok, sadece önerilen ilanlar var. Veri alınmıyor.")
                return []
        else:
            print("[tapu] Toplam ilan sayısı metinden okunamadı.")
            sys.exit(0)
        # Gerçek alacağımız maksimum ilan sayısı
        effective_limit = limit
        if total is not None and total > 0:
            effective_limit = min(limit, total)

        # İLAN LİNKLERİ: href'i /detay/ ile başlayan <a> tag'leri
        card_links = soup.find_all("a", href=re.compile(r"^/detay/"))
        print(f"[tapu] İlk sayfadaki aday kart sayısı (benzerler dahil): {len(card_links)}")

        listings: List[Listing] = []
        seen_urls = set()

        for a in card_links:
            if len(listings) >= effective_limit:
                break

            href = a.get("href")
            if not href:
                continue

            # Tam URL
            if href.startswith("http"):
                full_url = href
            else:
                full_url = "https://www.tapu.com" + href

            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            # Link içindeki tüm yazıyı al (başlık + fiyat vs aynı string'de)
            text = " ".join(a.stripped_strings)
            if not text:
                continue

            # Metinden fiyatı çek (örn: 4.300.000 TL)
            price_matches = re.findall(r"([\d\.]+)\s*TL", text)
            if not price_matches:
                continue

            price_str = price_matches[-1]
            digits = re.sub(r"[^\d]", "", price_str)
            if not digits:
                continue
            price = int(digits)

            # Başlık: fiyat string'inden önceki kısım
            price_pos = text.rfind(price_str)
            title = text[:price_pos].strip()

            listings.append(
                Listing(
                    site=self.site_name,
                    title=title,
                    price=price,
                    url=full_url,
                )
            )

        print(f"[tapu] İlk sayfadan alınan GERÇEK ilan sayısı: {len(listings)}")
        return listings
