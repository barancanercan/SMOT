# Görev Listesi (Task List)

Projenin "Ürünleşme" yolculuğundaki adımları.

## Faz 1: Temizlik ve Standartlaşma (Code Quality)

- [x] **Linter & Type Checking** <!-- id: 0 -->
  - [x] `ruff` ve `mypy` kurulumu yap <!-- id: 1 -->
  - [x] `ruff check` ile temizlik yap (bare excepts, unused imports) <!-- id: 2 -->
  - [x] `mypy` ile type checking yap ve düzelt <!-- id: 3 -->
- [x] **Logging Mekanizması** <!-- id: 4 -->
  - [x] Global bir logger konfigürasyonu oluştur (`utils/logger.py`) <!-- id: 5 -->
  - [x] `print()` kullanımlarını `logger.info()` / `logger.error()` ile değiştir (core files) <!-- id: 6 -->
- [x] **Konfigürasyon Yönetimi** <!-- id: 7 -->
  - [x] `config_settings.py` dosyasını `pydantic-settings` ile oluştur <!-- id: 8 -->
  - [x] `.env` ve `environment variables` kullanımını standartlaştır <!-- id: 9 -->

## Faz 2: Veri Toplama Dayanıklılığı (Scraping Resilience)

- [x] **Retry Logic Entegrasyonu** <!-- id: 10 -->
  - [x] `tenacity` kütüphanesini projeye ekle <!-- id: 11 -->
  - [x] Scraping fonksiyonlarına decorator ile retry mekanizması ekle <!-- id: 12 -->
- [x] **Hata Yakalama İyileştirmesi** <!-- id: 13 -->
  - [x] Spesifik exception yakalama (Timeout, NoSuchElement, StaleElement) ekle <!-- id: 15 -->

## Faz 3: Veritabanı Modernizasyonu

- [x] **ORM Hazırlığı** <!-- id: 16 -->
  - [x] `SQLAlchemy` modellerini tanımla (`models.py`) <!-- id: 17 -->
  - [x] Mevcut `database.py` (raw SQL) yapısını ORM'e dönüştür <!-- id: 18 -->

## Faz 4: AI İyileştirmeleri

- [x] **Structured Output** <!-- id: 19 -->
  - [x] LLM yanıtlarını JSON parse edilebilir hale getir <!-- id: 20 -->
  - [x] Regex ile parse edilen yerleri structured yapıya çevir <!-- id: 21 -->

## Faz 5: Temizlik ve Optimizasyon

- [x] **Gereksiz Dosyaların Kaldırılması** <!-- id: 22 -->
  - [x] Legacy Gradio UI (`ui/app.py`) kaldırılması <!-- id: 23 -->
  - [x] Eski veritabanı yedekleri ve örnek veri dosyalarının temizlenmesi <!-- id: 24 -->
- [x] **Bağımlılık Temizliği** <!-- id: 25 -->
  - [x] `requirements.txt`'den kullanılmayan kütüphanelerin (`gradio`, `langchain`, `tabulate`) çıkarılması <!-- id: 26 -->
