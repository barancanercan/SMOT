# 🏛️ Meclis İstihbarat Sistemi v2.0 (Professional Edition)

**Meclis İstihbarat Sistemi**, siyasi aktörlerin dijital ayak izlerini takip eden, analiz eden ve stratejik istihbarat raporları üreten kapsamlı bir yapay zeka ürünüdür. Ankara Büyükşehir Belediyesi Meclis üyeleri odağında, X/Twitter verilerini profesyonel bir "Siyaset Bilimi" disipliniyle işler.

---

## 🚀 Yenilikler: v2.0 "Professional AI Layout"

Bu sürümde proje, klasik kod yığınından profesyonel bir **AI Mühendisi Ürün Düzeni**ne (`src/` layout) geçirilmiş ve istihbarat kapasitesi maksimize edilmiştir.

### 🧠 Üst Düzey İstihbarat Analizi

- **Yeşil/Kırmızı/Gri Takım Framework**: Aktörleri kendi partisine sadakat (Yeşil), rakiplerine saldırı (Kırmızı) ve bağımsız gündemleri (Gri) üzerinden 3 aşamalı analiz eder.
- **Llama 3.2-1B Entegrasyonu**: CPU-only sistemlerde bile saniyeler içinde analiz yapabilen, kişiliği bozulmayan ve hallucination (halüsinasyon) oranı minimize edilmiş optimize model.
- **Etkileşim Kanıtlı Analiz**: Her analiz, tweet metinleri ve gerçek etkileşim verileri (Beğeni, Görüntülenme) ile desteklenir.

### 🏗️ Profesyonel Mimari (src Layout)

- **Modüler Yapı**: Kod tabanı `core`, `scrapers`, `analysis`, `reporting` ve `ui` olarak katmanlara ayrıldı.
- **Modern Import Standartları**: Mutlak paket importları (`meclis_istihbarat.*`) ile kurumsal kod kalitesi.
- **Konteyner Desteği**: Docker ve Docker-Compose ile tek komutla kurulum.

---

## 🔥 Temel Özellikler

### 📊 Akıllı Dashboard

- **Sistem İstatistikleri**: 13.000'den fazla tweet ve 86 meclis üyesinin canlı verisi.
- **Etkileşim Analizi**: Parti ve üye bazlı like/view/retweet karşılaştırmaları.
- **Görselleştirme**: Plotly destekli interaktif grafikler ve ilçe bazlı temsil haritaları.

### 🕵️ İstihbarat Raporlama

- **Profesyonel PDF/Excel Cıktısı**: Tek tıkla siyasi iletişim raporları üretimi.
- **Vector Search (ChromaDB)**: 13.000 tweet içinde anlamsal (semantic) arama ve konu odaklı analiz.
- **Takipçi Gelişimi**: Üyelerin dijital popülaritesindeki değişimlerin takibi.

---

## 🛠️ Kurulum ve Çalıştırma

### 1. Hazırlık

Proje klasörüne gidin ve ortamı hazırlayın:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Modelleri Çekme (Ollama)

Profesyonel analiz için optimize edilmiş modelleri indirin:

```bash
ollama pull llama3.2:1b
```

### 3. Uygulamayı Başlatma

Sistemi tek bir entry-point üzerinden yönetebilirsiniz:

```bash
# Web Arayüzünü Başlat
python3 run.py ui

# Veri Toplamayı Başlat
python3 run.py scrape
```

---

## 📁 Proje Yapısı

```
MeclisIstihbaratSistemi/
├── src/meclis_istihbarat/   # Ana Paket
│   ├── core/                # DB, Modeller, Ayarlar
│   ├── analysis/            # LLM Analizi, Prompts, VectorDB
│   ├── scrapers/            # Selenium Tweet/Profil Scrapers
│   ├── reporting/           # PDF/Excel Üretimi
│   ├── ui/                  # Streamlit Dashboard
│   └── utils/               # Logging ve Helperlar
├── main.py                  # UI Giriş Noktası
├── run.py                   # Unified CLI
├── Dockerfile               # Deployment
└── docker-compose.yml       # Stack Deployment
```

---

## 📊 Teknik Stack

| Katman        | Araç                               |
| ------------- | ---------------------------------- |
| **Frontend**  | Streamlit + Plotly                 |
| **Backend**   | Python 3.10+                       |
| **Database**  | SQLite + SQLAlchemy ORM            |
| **AI/LLM**    | Ollama (Llama 3.2-1B / Qwen 2.5)   |
| **Vector DB** | ChromaDB (All-MiniLM-L6-v2)        |
| **Scraping**  | Selenium (Undetected-Chromedriver) |

---

## 👩‍💻 Geliştirici

**Baran Can Ercan**
[GitHub](https://github.com/barancanercan) | [LinkedIn](https://linkedin.com/in/barancanercan)

---

_Bu sistem v2.0 sürümü ile birlikte profesyonel bir siyasi analiz platformuna dönüştürülmüştür._
