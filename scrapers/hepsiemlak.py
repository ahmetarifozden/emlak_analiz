import re
from typing import List
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from .base import BaseScraper, Listing


class HepsiemlakScraper(BaseScraper):
    site_name = "hepsiemlak"

    def _create_driver(self):
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")

        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def fetch_listings(self, search_url: str, limit: int = 10) -> List[Listing]:
        print(f"[{self.site_name}] Selenium ile çekiliyor: {search_url}")

        driver = self._create_driver()
        listings: List[Listing] = []

        try:
            driver.get(search_url)

            # WebDriverWait yerine basit sleep: sayfanın tamamen yüklenmesi için
            time.sleep(5)

            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            # 1) Önce li.listing-item üzerinden kartları alalım
            cards = soup.select("li.listing-item")
            # 2) Olmazsa article.listingView deneriz
            if not cards:
                cards = soup.select("article.listingView")

            print(f"[hepsiemlak] HTML içinde bulunan kart sayısı: {len(cards)}")

            for card in cards:
                if len(listings) >= limit:
                    break

                try:
                    # Link & başlık
                    link_tag = card.select_one("a.card-link")
                    if not link_tag:
                        continue

                    href = link_tag.get("href", "")
                    if href.startswith("http"):
                        url = href
                    else:
                        url = "https://www.hepsiemlak.com" + href

                    title = link_tag.get_text(strip=True) or "Başlık yok"

                    # Fiyat
                    price_tag = card.select_one("span.list-view-price")
                    if not price_tag:
                        continue

                    price_text = price_tag.get_text(strip=True)
                    price_num_str = re.sub(r"[^\d]", "", price_text)
                    if not price_num_str:
                        continue

                    price_num = float(price_num_str)

                    listings.append(
                        Listing(
                            title=title,
                            price=price_num,
                            url=url,
                            site=self.site_name,
                        )
                    )

                except Exception as e:
                    print(f"[hepsiemlak] kart parse hatası: {e}")
                    continue

            print(f"[hepsiemlak] Toplam alınan ilan: {len(listings)}")
            return listings

        finally:
            driver.quit()
