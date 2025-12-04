import re
import requests
from bs4 import BeautifulSoup
from typing import List
from .base import BaseScraper, Listing


class TapuScraper(BaseScraper):
    site_name = "tapu"

    def _page_url(self, base_url: str, page: int) -> str:
        """
        Tapu'da 2. sayfaya geçtiğinde URL'ye bak:
          1. sayfa: https://www.tapu.com/konut/adana-ceyhan
          2. sayfa: https://www.tapu.com/konut/adana-ceyhan?page=2
        gibi ise bu fonksiyon doğru çalışır.
        Farklıysa sadece burada pattern'i değiştir.
        """
        if page == 1:
            return base_url
        return f"{base_url}?sayfa={page}"

    def fetch_listings(self, search_url: str, limit: int = 10) -> List[Listing]:
        print(f"[{self.site_name}] {search_url} adresinden veri çekiliyor...")

        headers = {
            "User-Agent":
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9",
            "Referer": "https://www.google.com/",
        }

        listings: List[Listing] = []
        page = 1

        while len(listings) < limit:
            page_url = self._page_url(search_url, page)
            print(f"[tapu] Sayfa {page} URL: {page_url}")

            resp = requests.get(page_url, headers=headers, timeout=15)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")

            # Burada senin daha önce kullandığın kart selector'ü neyse onu kullan:
            cards = soup.select("a.asset")  # ÖRNEK! Sen kendi selector’unu koy
            print(f"[tapu] Sayfa {page} içindeki aday kart sayısı: {len(cards)}")

            if not cards:
                break

            for card in cards:
                if len(listings) >= limit:
                    break

                try:
                    # Burada senin mevcut logic'in neyse (detay sayfasına gidip fiyat
                    # çekme vs.), onu aynen bırak, sadece limit kontrolünü ekle.
                    ...
                except Exception as e:
                    print(f"[tapu] kart hata: {e}")
                    continue

            page += 1

        print(f"[tapu] Toplam {len(listings)} ilan alındı.")
        return listings
