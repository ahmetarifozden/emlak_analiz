# 🏠 Emlak Analiz Projesi

Bu proje, Türkiye’deki emlak sitelerinden toplanan ilan verilerini kullanarak;

- İl / ilçe bazında **ortalama emlak fiyatlarını** çıkaran,
- Bu ortalamalar arasındaki **anormal (uç) ilçeleri istatistiksel olarak tespit eden**
- Sonuçları **Excel çıktıları** ile raporlayan

bir veri analiz çalışmasıdır.

---

## 🎯 Projenin Amacı

1. Farklı sitelerden alınan il/ilçe fiyat ortalamalarını işlemek.
2. Her **ilçe için**:
   - Toplam ilan sayısını (`num_listings`)
   - Ortalama fiyatı (`avg_price`)
   hesaplamak.
3. İlçeleri **şehir bazlı** analiz etmek (her il kendi içinde değerlendirilir).
4. **IQR** ve **Z-Score** yöntemlerini kullanarak **fiyat anomalilerini tespit etmek**.
5. Sonuçları yeni Excel dosyalarına kaydetmek ve özet tablo oluşturmak.

---

## 📂 Veri Yapısı

Analiz edilen Excel dosyası şu kolonlara sahiptir:

| Sütun        | Açıklama                                      |
|-------------|-----------------------------------------------|
| `city`      | İl adı                                        |
| `district`  | İlçe adı                                      |
| `site`      | Verinin alındığı kaynak sitesi                |
| `num_listings` | O ilçe için alınan ilan sayısı             |
| `avg_price` | İlanların ortalama fiyatı (TL)                |

Analizler sadece `emlakjet` verileri üzerinden gerçekleştirilmiştir.

---

## 🧮 Yapılan Analizler

### 1️⃣ **Şehir Bazlı Anomali Analizi (IQR + Z-Score)**

Fiyatların şehirden şehire değişen seviyelerini (ör. İstanbul Kadıköy vs. Mersin Tarsus) doğru şekilde ele almak için:

- **Her il ayrı ayrı değerlendirilir.**
- İlçeler kendi şehirlerinin fiyat dağılımına göre karşılaştırılır.

### 🟦 IQR (Interquartile Range) Yöntemi

- Q1 = 1. çeyrek  
- Q3 = 3. çeyrek  
- IQR = Q3 - Q1  

Normal fiyat aralığı:

\[
Q1 - 1.5 \times IQR \quad \text{ile} \quad Q3 + 1.5 \times IQR
\]

Bu aralığın dışına çıkan ilçeler **IQR outlier** olarak işaretlenir.

---

### 🟥 Z-Score Yöntemi

Bir ilçenin şehir ortalamasından ne kadar uzak olduğunu ölçmek için:

\[
z = \frac{x - \mu}{\sigma}
\]

- \( x \) = ilçe ortalama fiyatı  
- \( \mu \) = o şehrin ortalama fiyatı  
- \( \sigma \) = standart sapma  

|Z| ≥ 3 olan ilçeler **Z-score outlier** kabul edilir.

---

### 🟩 Outlier Flag Mantığı

Her ilçe için üç seviyeli bir etiket oluşturulur:

| Flag | Açıklama |
|------|----------|
| `normal` | Hem IQR hem Z-Score açısından normal |
| `iqr_or_z` | İki yöntemden en az birine göre anormal |
| `both` | Hem IQR hem Z-Score’a göre anormal (**güçlü anomali**) |

---

## 🧾 Üretilen Çıktılar

`sehir_bazli_anomali.py` çalıştırıldığında **tek bir Excel dosyası** oluşturulur:

### 📌 **sehir_bazli_anomaliler.xlsx**

Bu Excel dosyasında üç sayfa bulunur:

### 1️⃣ `tum_ilceler`
- Tüm emlakjet ilçeleri  
- Ek sütunlar:
  - `zscore_city`
  - `iqr_outlier`
  - `zscore_outlier`
  - `outlier_flag`
  - `city_Q1`, `city_Q3`, `city_IQR`
  - `city_lower_bound`, `city_upper_bound`
  - `city_mean`, `city_std`

---

### 2️⃣ `anormal_ilceler`
- Sadece anormal çıkan ilçeler.
- `outlier_flag != normal` olan tüm satırlar.

---

### 3️⃣ `ozet`
İstatistiksel özet tablosu:

| flag_tipi | adet |
|-----------|------|
| normal    | toplam normal ilçeler |
| iqr_or_z  | IQR veya Z-score’a göre anormal ilçeler |
| both      | Çok güçlü anomali ilçeler |
| toplam    | toplam ilçe sayısı |

---

## 🛠 Kullanılan Teknolojiler

- **Python 3.x**
- **Pandas**
- **NumPy**
- **SciPy**
- **openpyxl**

---


