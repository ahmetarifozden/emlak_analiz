from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import List


@dataclass
class Listing:
    """Tek bir ilan kaydını temsil eder."""
    title: str
    price: float  # TL cinsinden
    url: str
    site: str


class BaseScraper(ABC):
    site_name: str

    @abstractmethod
    def fetch_listings(self, search_url: str, limit: int = 10) -> List[Listing]:
        """
        Verilen arama URL'sinden ilanları çekip List[Listing] döndürür.
        search_url: İlçe filtresi yapılmış arama sayfası URL'si
        limit: Kaç ilan çekeceği (örn. 10)
        """
        raise NotImplementedError
