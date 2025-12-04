import re
import requests
from bs4 import BeautifulSoup
from typing import List
from .base import BaseScraper, Listing


class EmlakjetScraper(BaseScraper):
    site_name = "emlakjet"

    def _page_url(self, base_url: str, page: int) -> str:
        """
        Emlakjet'te 2. sayfanın URL'sine bak:
        Örneğin:
          1. sayfa: https://www.emlakjet.com/satilik-konut/adana-ceyhan
          2. sayfa: https://www.emlakjet.com/satilik-konut/adana-ceyhan?page=2
        ise bu fonksiyon doğrudur.
        Farklıysa sadece burayı değiştirmen yeter.
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
            print(f"[emlakjet] Sayfa {page} URL: {page_url}")

            resp = requests.get(page_url, headers=headers, timeout=15)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select("div.listing-item")

            print(f"[emlakjet] Sayfa {page} içindeki kart sayısı: {len(cards)}")

            if not cards:
                # Bu sayfada hiç kart yoksa -> daha ileri sayfaya gitmenin anlamı yok
                break

            for card in cards:
                if len(listings) >= limit:
                    break

                try:
                    title_tag = card.select_one("h3.listing-title")
                    title = title_tag.get_text(strip=True) if title_tag else "Başlık yok"

                    price_tag = card.select_one("div.listing-price")
                    if not price_tag:
                        continue

                    price_text = price_tag.get_text(strip=True)
                    price_num = float(re.sub(r"[^\d]", "", price_text))

                    link_tag = card.select_one("a")
                    if link_tag and link_tag.get("href"):
                        href = link_tag["href"]
                        if href.startswith("http"):
                            url = href
                        else:
                            url = "https://www.emlakjet.com" + href
                    else:
                        url = search_url

                    listings.append(
                        Listing(
                            title=title,
                            price=price_num,
                            url=url,
                            site=self.site_name,
                        )
                    )
                except Exception as e:
                    print(f"[emlakjet] kart hata: {e}")
                    continue

            page += 1  # bir sonraki sayfaya geç

        print(f"[emlakjet] Toplam {len(listings)} ilan alındı.")
        return listings
