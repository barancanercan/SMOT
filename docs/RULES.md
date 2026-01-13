# PROJE KURALLARI VE STANDARTLARI (RULES.md)

Bu dosya, Meclis İstihbarat Sistemi projesinin geliştirilme sürecinde uyulması gereken **KIRMIZI ÇİZGİLERİ** ve **TEKNİK STANDARTLARI** içerir. Proje üzerinde çalışan her geliştirici (ve AI asistanı) bu kurallara uymakla yükümlüdür.

---

## 1. KIRMIZI ÇİZGİLER (HARD CONSTRAINTS)

Bu kurallar **ASLA** ihlal edilmemelidir.

### 1.1. Ücretsiz ve Yerel Kalmalı

- **Scraping:** Veri toplama işlemi **Selenium / Undetected Chromedriver** ile yapılmaya devam edecektir. Ücretli API (Twitter API, BrightData, vb.) kullanımı **YASAKTIR**.
- **LLM:** Analizler yerel **Ollama** üzerinden yapılacaktır. OpenAI/Claude gibi ücretli API'lere bağımlılık eklenmemelidir (opsiyonel olarak eklenebilir ama varsayılan yerel olmalıdır).

### 1.2. Ürünleşme Odaklılık

- Her özellik "satılabilir bir ürün" kalitesinde olmalıdır. "Hobi projesi" mantığındaki `print` ile debug etme, hata gizleme (`try-except pass`) gibi pratikler **YASAKTIR**.
- Kullanıcı her zaman ne olduğunu anlamalıdır (UI geri bildirimleri).

---

## 2. KOD STANDARTLARI

### 2.1. Python ve Stil

- **Type Hinting:** Tüm fonksiyonlar argüman ve dönüş değerleri için type hint içermelidir.

  ```python
  # DOĞRU
  def get_user_tweets(username: str, limit: int = 100) -> List[Dict]:

  # YANLIŞ
  def get_user_tweets(username, limit=100):
  ```

- **Docstrings:** Her modül, sınıf ve fonksiyonun ne yaptığını açıklayan bir Docstring'i olmalıdır.
- **Dil:** Kod değişkenleri ve fonksiyon isimleri **İngilizce** (`get_tweets`), yorumlar ve arayüz metinleri **Türkçe** veya İngilizce olabilir (Tercihen Türkçe).

### 2.2. Hata Yönetimi (Error Handling)

- **Sessiz Hata YASAK:** `try: ... except: pass` bloğu kesinlikle kullanılmayacaktır. Hatalar loglanmalı veya anlamlı bir exception fırlatılmalıdır.
- **Logging:** `print()` yerine Python'un `logging` modülü kullanılmalıdır.

---

## 3. MİMARİ KARARLAR

### 3.1. Veritabanı

- Proje **PostgreSQL** geçişine hazırlanacaktır. SQLite sadece geliştirme ortamında kabul edilebilir, ancak hedef Production ortamı PostgreSQL'dir.
- Veritabanı işlemleri `database.py` içinde izole edilmelidir. UI katmanından doğrudan SQL sorgusu atılmamalıdır.

### 3.2. Asenkron Yapı

- Uzun süren işlemler (Scraping, LLM Analizi) asla ana thread'i veya UI thread'ini bloklamamalıdır. Bu işlemler `Celery` veya benzeri bir görev kuyruğu ile arka plana atılmalıdır.

### 3.3. Scraping Dayanıklılığı

- Scraping kodu "kırılgan" olmamalıdır.
  - **Retry Logic:** Bağlantı hatası veya element bulunamaması durumunda hemen pes etmemeli, "Exponential Backoff" ile tekrar denemelidir.
  - **Self-Healing:** X.com arayüzü değişirse kodun patladığı yer loglanmalı ve admin uyarılmalıdır.

---

## 4. GÜVENLİK

- `.env` dosyası **ASLA** git geçmişine atılmamalıdır.
- Veritabanı bağlantı bilgileri kod içine gömülmemelidir.

---

**Bu kurallara uyulmadığı tespit edildiğinde, ilgili Pull Request veya Commit REDDEDİLECEKTİR.**
