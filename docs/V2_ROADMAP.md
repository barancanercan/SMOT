 edilmiş o# Meclis Istihbarat Sistemi - V2 Roadmap

## Proje Ozeti

**Hedef:** Meclis uyelerinin X/Twitter aktivitelerini analiz eden,
kullanici dostu bir raporlama sistemi.

**Mimari:**
```
[Haftalik Guncelleme - Backend]          [Kullanici - Frontend]
         |                                        |
    scraper_worker.py                        Gradio UI
         |                                        |
    SQLite + Profil Bilgileri              Uye Secimi
         |                                        |
    Vector Database (embedding)            Rapor Goster
         |                                        |
         +----------------+-------------------+
                          |
                    LLM (Ollama)
```

---

## Sistem Gereksinimleri

### Donanim (Mevcut)
- CPU: Intel i7-1165G7 (4 core, 8 thread)
- RAM: 16GB
- GPU: YOK (onemli kisit)
- Disk: 206GB bos

### Kisitlar
1. GPU yok = Buyuk LLM'ler cok yavas
2. Tamamen ucretsiz olmali
3. Minimum kaynak kullanimi

### Cozum Stratejisi
- LLM: Ollama + qwen2.5:7b (mevcut, CPU'da ~30-60sn/cevap)
- Alternatif: qwen2.5:3b (daha hizli, ~10-20sn/cevap)
- Vector DB: ChromaDB (lightweight, local)
- UI: Gradio (basit, hizli)

---

## Rapor Sablonu V2

| # | Soru | Veri Kaynagi | LLM Gerekli |
|---|------|--------------|-------------|
| 1 | Ana konular nedir? | Tweet text | EVET |
| 2 | Kac takipcisi var? | Profil scrape | HAYIR |
| 3 | Kac kisi takip ediyor? | Profil scrape | HAYIR |
| 4 | Takipci degisimi (tarih arasi) | Profil history | HAYIR |
| 5 | Etkilesim degisimi (tarih arasi) | Tweet metrics | HAYIR |
| 6 | Parti/lider savunusu | Tweet text | EVET |
| 7 | Muhalefet elestirisi | Tweet text | EVET |
| 8 | En cok etkilesim alan tweetler | Tweet metrics | HAYIR |

**Ozet:** 8 sorudan 3'u LLM gerektiriyor (1, 6, 7)

---

## Modul Yapisi

### Modul 1: Veri Toplama (MEVCUT - v1.0)
```
scraper_worker.py  -> Tweet toplama
database.py        -> SQLite kayit
export_to_csv.py   -> CSV export
```
**Durum:** TAMAMLANDI

### Modul 2: Profil Bilgileri (YENI)
```
profile_scraper.py -> Takipci/takip sayisi
profile_history.py -> Tarihsel kayit
```
**Gerekli Veriler:**
- followers_count
- following_count
- scrape_date (tarihsel takip icin)

### Modul 3: Vector Database (YENI)
```
embeddings.py      -> Tweet embedding olustur
vector_db.py       -> ChromaDB islemleri
```
**Amac:** LLM'e gonderilecek relevant tweet'leri bulmak

### Modul 4: LLM Analiz (YENI)
```
analyzer.py        -> Ollama entegrasyonu
prompts.py         -> Soru sablonlari
```
**Sorular:** 1, 6, 7 (ana konular, parti savunusu, muhalefet elestirisi)

### Modul 5: Raporlama (YENI)
```
report_generator.py -> Rapor olustur
report_cache.py     -> Onbellek (performans)
```
**Cikti:** Markdown formatinda rapor

### Modul 6: Web UI (YENI)
```
app.py             -> Gradio arayuzu
```
**Ozellikler:**
- Uye secimi (checkbox)
- Tarih araliigi
- Rapor gosterimi

---

## Veritabani Semasi V2

### Mevcut Tablolar
```sql
councilors (username, name, party, district)
tweets (username, tweet_text, tweet_date, likes, replies, retweets, views)
```

### Yeni Tablolar
```sql
-- Profil gecmisi (takipci takibi)
profile_history (
    id,
    username,
    followers_count,
    following_count,
    tweet_count,
    scrape_date
)

-- Rapor onbellegi
report_cache (
    id,
    username,
    report_type,
    content,
    created_at,
    expires_at
)
```

---

## Uygulama Plani

### Faz 1: Profil Scraping (1-2 gun)
- [ ] profile_scraper.py olustur
- [ ] Takipci/takip sayisi cek
- [ ] profile_history tablosu ekle
- [ ] Haftalik karsilastirma fonksiyonu

### Faz 2: Metrik Hesaplama (1 gun)
- [ ] Etkilesim hesaplama (likes + replies + retweets)
- [ ] Tarih arasi karsilastirma
- [ ] En iyi tweet'leri bulma

### Faz 3: Vector Database (2-3 gun)
- [ ] ChromaDB kurulumu
- [ ] Embedding modeli sec (all-MiniLM-L6-v2 - ucretsiz)
- [ ] Tweet'leri embed et
- [ ] Similarity search fonksiyonu

### Faz 4: LLM Entegrasyonu (2-3 gun)
- [ ] Ollama baglantisi
- [ ] Prompt sablonlari (Turkce)
- [ ] 3 soru icin analiz fonksiyonlari
- [ ] Response parsing

### Faz 5: Rapor Olusturma (1-2 gun)
- [ ] Rapor sablonu
- [ ] Tum sorulari birlestir
- [ ] Markdown cikti
- [ ] Cache mekanizmasi

### Faz 6: Web UI (2-3 gun)
- [ ] Gradio arayuzu
- [ ] Uye secimi
- [ ] Tarih filtresi
- [ ] Rapor gosterimi

### Faz 7: Test & Optimizasyon (1-2 gun)
- [ ] End-to-end test
- [ ] Performans olcumu
- [ ] Hata duzeltme

**Toplam Tahmini Sure:** 10-16 gun

---

## Dosya Yapisi V2

```
MeclisIstihbaratSistemi/
|
|-- config.py                 # Konfigurason
|-- database.py               # SQLite (guncellendi)
|
|-- scraping/
|   |-- x_scraper.py          # Tweet scraper (mevcut)
|   |-- profile_scraper.py    # Profil scraper (yeni)
|
|-- analysis/
|   |-- embeddings.py         # Embedding olustur
|   |-- vector_db.py          # ChromaDB islemleri
|   |-- analyzer.py           # LLM analiz
|   |-- prompts.py            # Prompt sablonlari
|
|-- reporting/
|   |-- report_generator.py   # Rapor olustur
|   |-- metrics.py            # Metrik hesaplama
|
|-- ui/
|   |-- app.py                # Gradio UI
|
|-- workers/
|   |-- scraper_worker.py     # Tweet toplama (mevcut)
|   |-- update_worker.py      # Haftalik guncelleme
|
|-- data/
|   |-- data.csv
|
|-- docs/
|   |-- V2_ROADMAP.md         # Bu dosya
|
|-- meclis.db
|-- chroma_db/                # Vector database
```

---

## Teknoloji Stack V2

| Katman | Arac | Neden |
|--------|------|-------|
| Scraping | Selenium + undetected-chromedriver | Mevcut, calisiyor |
| Database | SQLite | Basit, yeterli |
| Vector DB | ChromaDB | Local, ucretsiz, lightweight |
| Embedding | sentence-transformers (all-MiniLM-L6-v2) | Ucretsiz, hizli, CPU uyumlu |
| LLM | Ollama + qwen2.5:7b | Mevcut, Turkce destekli |
| UI | Gradio | Basit, hizli gelistirme |

---

## Performans Beklentileri

### LLM (CPU - qwen2.5:7b)
- Tek soru: ~30-60 saniye
- 3 soru (rapor): ~2-3 dakika
- 13 uye tam rapor: ~30-40 dakika

### Alternatif: qwen2.5:3b
- Tek soru: ~10-20 saniye
- 3 soru: ~30-60 saniye
- 13 uye: ~10-15 dakika
- Trade-off: Biraz daha dusuk kalite

### Oneri
Ilk kurulumda qwen2.5:7b ile test et.
Cok yavas gelirse qwen2.5:3b'ye gec.

---

## Haftalik Guncelleme Akisi

```
Her Pazartesi (manuel):
1. python workers/scraper_worker.py    # Yeni tweetler
2. python workers/update_worker.py     # Profil + embedding guncelle

Kullanici istediginde:
1. Gradio UI ac
2. Uyeleri sec
3. Rapor olustur (cache varsa hizli, yoksa LLM calistir)
```

---

## Sonraki Adim

Faz 1 ile baslayalim mi?
- profile_scraper.py olusturma
- Takipci/takip sayisi cekme
- profile_history tablosu

Onay verirsen baslarim.
