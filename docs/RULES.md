# Proje Kurallari ve Standartlari

Bu dosya, Meclis Istihbarat Sistemi projesinin gelistirilme surecinde uyulmasi gereken kurallari icerir.

## 1. Kirmizi Cizgiler

### 1.1. Ucretsiz ve Yerel Kalmali

- **Scraping:** Selenium / Undetected Chromedriver kullanilacak. Ucretli API yasak.
- **LLM:** Yerel Ollama kullanilacak. OpenAI/Claude API opsiyonel ama varsayilan yerel olmali.

### 1.2. Urunlesme Odaklilik

- Her ozellik "satilabilir urun" kalitesinde olmali
- `print` ile debug, `try-except pass` yasak
- Kullanici her zaman ne oldugunu anlamali (UI geri bildirimleri)

## 2. Kod Standartlari

### 2.1. Python Stil

- **Type Hints:** Tum fonksiyonlar type hint icermeli
- **Docstrings:** Her modul, sinif ve fonksiyon dokumante edilmeli
- **Dil:** Kod degiskenleri Ingilizce, yorumlar Turkce

### 2.2. Hata Yonetimi

- Sessiz hata yasak: `try-except pass` kesinlikle kullanilmayacak
- Hatalar loglanmali veya re-raise edilmeli
- `print()` yerine `logging` modulu kullanilmali

## 3. Mimari Kararlar

### 3.1. Veritabani

- Hedef: PostgreSQL (SQLite sadece gelistirme icin)
- Veritabani islemleri `database.py` icinde izole edilmeli
- UI katmanindan dogrudan SQL sorgusu yasak

### 3.2. Asenkron Yapi

- Uzun suren islemler ana thread'i bloklamamali
- Celery/Redis ile arka plan gorevleri planlanmali

### 3.3. Scraping Dayanikliligi

- Retry logic: Exponential backoff ile tekrar deneme
- Self-healing: Arayuz degisikliklerinde admin uyarisi

## 4. Guvenlik

- `.env` dosyasi git gecmisine atilmamali
- Veritabani baglanti bilgileri kod icine gomulmemeli
