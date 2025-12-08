import re
import random
import time
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from .base import BaseScraper, Listing

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
        if page == 1:
            return base_url
        return f"{base_url}?sayfa={page}"

    def _extract_total_count(self, soup: BeautifulSoup) -> Optional[int]:
        """
        Sayfa içindeki metinden toplam ilan sayısını çekmeye çalışır.
        Farklı yazım ihtimalleri için birkaç pattern denenir.
        """
        text = soup.get_text(" ", strip=True)

        patterns = [
            r"([\d\.]+)\s+adet\s+ilan",     # 12 adet ilan
            r"([\d\.]+)\s+ilan\b",          # 12 ilan
            r"Toplam\s*([\d\.]+)\s+ilan",   # Toplam 12 ilan
            r"([\d\.]+)\s+sonuç\b",         # 12 sonuç
        ]

        for pat in patterns:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                raw_num = m.group(1)
                digits = re.sub(r"[^\d]", "", raw_num)
                if digits:
                    return int(digits)

        return None

    def _has_no_results(self, soup: BeautifulSoup) -> bool:
        text = soup.get_text(" ", strip=True).lower()
        no_result_phrases = [
            "aradığınız kriterlere uygun ilan bulunamadı",
            "aradığınız kriterlere uygun bir ilan bulunamadı",
            "aranıza uygun ilan bulunamadı",
            "ilan bulunamadı",
        ]
        return any(phrase in text for phrase in no_result_phrases)

    def fetch_listings(
        self,
        base_url: str,
        limit: int = 50,
        max_pages: int = 50,
    ) -> List[Listing]:

        listings_all: List[Listing] = []
        seen_urls = set()
        page = 1
        total_from_site_printed = False

        prev_total = 0
        unchanged_pages = 0
        max_legit: Optional[int] = None  # sitede yazan gerçek ilan sayısı

        while page <= max_pages:
            url = self._page_url(base_url, page)

            # ---- güvenli istek + retry ----
            resp = None
            for attempt in range(3):
                try:
                    resp = requests.get(url, headers=HEADERS, timeout=20)
                    break
                except requests.exceptions.RequestException as e:
                    print(f"[emlakjet] {url} isteğinde hata (deneme {attempt+1}/3): {e}")
                    time.sleep(2)

            if resp is None:
                print(f"[emlakjet] {url} isteği 3 denemede de başarısız oldu, bu ilçe atlanıyor.")
                break

            if resp.status_code != 200:
                print(f"[emlakjet] {url} için status code: {resp.status_code}")
                break

            soup = BeautifulSoup(resp.text, "html.parser")

            # 0 sonuç varsa, benzer ilanları da tamamen ignore et
            if page == 1 and self._has_no_results(soup):
                print("[emlakjet] Bu ilçe için 'uygun ilan bulunamadı' mesajı var. "
                      "Benzer ilanlar alınmayacak.")
                return []

            # İlk sayfada toplam ilan sayısını okumaya çalış
            if page == 1 and not total_from_site_printed:
                total = self._extract_total_count(soup)
                if total is not None:
                    print(f"[emlakjet] Bu arama için sitede görünen TOPLAM ilan sayısı: {total}")
                    if total == 0:
                        print("[emlakjet] Bu ilçe için gerçek ilan yok, benzer ilanlar alınmayacak.")
                        return []
                    # 🔴 ÖNEMLİ SATIR: gerçek maksimum ilan sayısı
                    max_legit = total
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
                if max_legit is not None and len(listings_all) >= max_legit:
                    break  # zaten yeterli gerçek ilanı aldık

                href = a.get("href")
                if not href:
                    continue

                # Tam URL
                full_url = href if href.startswith("http") else "https://www.emlakjet.com" + href
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                text = " ".join(a.stripped_strings)
                if not text:
                    continue

                price_matches = re.findall(r"([\d\.]+)\s*TL", text)
                if not price_matches:
                    continue

                price_str = price_matches[-1]
                digits = re.sub(r"[^\d]", "", price_str)
                if not digits:
                    continue
                price = int(digits)

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

            current_total = len(listings_all)
            print(
                f"[emlakjet] {url} sayfasından {page_new_count} yeni ilan eklendi. "
                f"Şu ana kadar TOPLAM {current_total} ilan toplandı."
            )

            # Sitede yazan gerçek toplam sayıya ulaştıysak dur
            if max_legit is not None and current_total >= max_legit:
                print("[emlakjet] Sitede yazan toplam ilan sayısına ulaşıldı, benzer ilanlar alınmayacak.")
                break

            # 3 sayfa üst üste yeni ilan gelmezse dur
            if current_total == prev_total:
                unchanged_pages += 1
                print(f"[emlakjet] Bu sayfada yeni ilan yok. "
                      f"Üst üste değişmeyen sayfa sayısı: {unchanged_pages}")
                if unchanged_pages >= 3:
                    print("[emlakjet] 3 sayfa üst üste yeni ilan gelmedi, tarama sonlandırılıyor.")
                    break
            else:
                unchanged_pages = 0
                prev_total = current_total

            page += 1

        if not listings_all:
            print("[emlakjet] Hiç ilan toplanamadı.")
            return []

        # Rastgele seçim
        sample_count = min(limit, len(listings_all))
        sampled_listings = random.sample(listings_all, sample_count)
        print(f"[emlakjet] Toplam {len(listings_all)} ilandan rastgele {sample_count} tanesi seçildi.")
        return sampled_listings
