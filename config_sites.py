# config_sites.py

from urllib.parse import quote_plus


def slugify(text: str) -> str:
    """
    Basit slug fonksiyonu:
    - Küçük harfe çevir
    - Türkçe karakterleri düzelt
    - Boşluk -> '-'
    """
    text = text.strip().lower()
    text = text.replace("ç", "c").replace("ğ", "g").replace("ş", "s")
    text = text.replace("ı", "i").replace("ö", "o").replace("ü", "u")
    text = text.replace(" ", "-")
    return quote_plus(text)


def hepsiemlak_url(city: str, district: str) -> str:
    """
    Örnek: https://www.hepsiemlak.com/cukurova-satilik
    (Hepsiemlak'ta şu an il değil, direk ilçe slug'ı kullanılıyor)
    """
    d = slugify(district)
    return f"https://www.hepsiemlak.com/{d}-satilik"



def emlakjet_url(city: str, district: str) -> str:
    """
    Gerçek pattern:
    https://www.emlakjet.com/satilik-konut/istanbul-kadikoy
    """
    c = slugify(city)
    d = slugify(district)
    return f"https://www.emlakjet.com/satilik-konut/{c}-{d}"

def tapu_url(city: str, district: str) -> str:
    """
    Örnek: https://www.tapu.com/konut/adana-saricam
    """
    c = slugify(city)
    d = slugify(district)
    return f"https://www.tapu.com/konut/{c}-{d}"
