import re
import random
from typing import List

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

from .base import BaseScraper, Listing


class HepsiemlakScraper(BaseScraper):
    site_name = "hepsiemlak"

    def _create_driver(self):
        options = Options()

        # Headless DEĞİL (stabil olsun diye) ama pencereyi ekran dışına atıyoruz
        # Böylece sen görmüyorsun ama normal modun tüm stabilitesini kullanıyoruz.
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--window-position=-2000,0")  # ekran dışında

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Bot algısını azalt
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Normal kullanıcı gibi görünsün
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        )

        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        # navigator.webdriver izini sil
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        # ÖNEMLİ: set_page_load_timeout KULLANMIYORUZ
        # (renderer timeout’u tetikliyordu)

        return driver

    def fetch_listings(self, search_url: str, limit: int = 10) -> List[Listing]:
        sample_size = limit
        max_scrape = 100
        max_pages = 100

        print(f"[{self.site_name}] Selenium ile çekiliyor: {search_url}")

        driver = self._create_driver()
        all_listings: List[Listing] = []
        seen_urls = set()

        try:
            page = 1

            while len(all_listings) < max_scrape and page <= max_pages:

                if page == 1:
                    page_url = search_url
                else:
                    sep = "&" if "?" in search_url else "?"
                    page_url = f"{search_url}{sep}page={page}"

                print(f"[hepsiemlak] Sayfa {page} açılıyor: {page_url}")

                # Sayfayı yükle - aşırı hata varsa ilçeyi atla
                try:
                    driver.get(page_url)
                except Exception:
                    print("[hepsiemlak] Sayfa yüklenemedi (zaman aşımı veya bağlantı sorunu). "
                          "Bu ilçe Hepsiemlak için atlanıyor.")
                    return []


                # Kartlar yüklenene kadar max 12 sn bekle
                try:
                    WebDriverWait(driver, 12).until(
                        EC.presence_of_all_elements_located(
                            (By.CSS_SELECTOR, "li.listing-item")
                        )
                    )
                except TimeoutException:
                    print("[hepsiemlak] Bu sayfada ilan kartı yok (timeout).")
                    break

                html = driver.page_source
                soup = BeautifulSoup(html, "html.parser")

                # 0 ilan durumunu ilk sayfada yakala, benzer ilanları atla
                if page == 1:
                    full_text = soup.get_text(" ", strip=True).lower()
                    if ("0 ilan bulundu" in full_text or
                        "aradığınız kriterlere uygun ilan bulunamadık" in full_text):
                        print("[hepsiemlak] Arama kriterlerine uygun ana ilan yok. "
                              "Benzer/yakın ilanlar alınmayacak, bu ilçe için veri yok.")
                        return []

                cards = soup.select("li.listing-item")
                print(f"[hepsiemlak] Sayfa {page} kart sayısı: {len(cards)}")

                if not cards:
                    print("[hepsiemlak] Kart bulunamadı, durduruluyor.")
                    break

                new_in_page = 0

                for card in cards:
                    if len(all_listings) >= max_scrape:
                        break

                    try:
                        link_tag = card.select_one("a.card-link") or card.select_one("a.img-link")
                        if not link_tag:
                            continue

                        href = link_tag.get("href", "")
                        url = href if href.startswith("http") else \
                            "https://www.hepsiemlak.com" + href

                        if url in seen_urls:
                            continue

                        seen_urls.add(url)
                        new_in_page += 1

                        title_tag = card.select_one("header.list-view-header h3")
                        title = title_tag.get_text(strip=True) if title_tag else (
                            link_tag.get("title") or "Başlık yok"
                        )

                        price_tag = card.select_one("span.list-view-price")
                        if not price_tag:
                            continue

                        price_digits = re.sub(
                            r"[^\d]", "", price_tag.get_text(strip=True)
                        )
                        if not price_digits:
                            continue

                        price_num = float(price_digits)

                        all_listings.append(
                            Listing(
                                title=title,
                                price=price_num,
                                url=url,
                                site=self.site_name,
                            )
                        )

                    except Exception as e:
                        print(f"[hepsiemlak] Kart parse hatası: {e}")
                        continue

                print(f"[hepsiemlak] Bu sayfada eklenen yeni ilan: {new_in_page}")
                print(f"[hepsiemlak] Toplam toplanan ilan: {len(all_listings)}")

                if new_in_page == 0:
                    print("[hepsiemlak] Yeni ilan yok → durduruluyor.")
                    break

                page += 1

            # Sonuçlar
            if not all_listings:
                return []

            if len(all_listings) <= sample_size:
                return all_listings

            random.shuffle(all_listings)
            return all_listings[:sample_size]

        finally:
            driver.quit()
