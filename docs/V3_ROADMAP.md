# Meclis Istihbarat Sistemi - V3 Roadmap

## Mevcut Durum (V2 Tamamlandi)

**Calisan Ozellikler:**
- Tweet scraping (manuel login ile)
- Profil bilgileri toplama
- Vector database (ChromaDB + embeddings)
- LLM analizi (Ollama)
- Rapor olusturma (8 soru)
- Gradio web arayuzu
- Haftalik guncelleme worker

**Istatistikler:**
- 13 meclis uyesi
- 46 tweet (ilk toplama)
- 11M+ toplam goruntulenme

---

## V3 Yapilacaklar

### 1. [BUG] Tweet Scraper 3 Aylik Veri Cekmiyor

**Sorun:** 90 gunluk pencere ayarli ama sadece son ~3-10 tweet geliyor.

**Olasi Nedenler:**
- X/Twitter scroll limiti
- Rate limiting
- Sayfa yapisinda degisiklik
- Lazy loading sorunu

**Arastirilacak:**
- [ ] x_scraper.py scroll mekanizmasi
- [ ] max_scrolls parametresi (su an 200)
- [ ] consecutive_no_new threshold
- [ ] Alternatif: Twitter API (academic access?)

---

### 2. Coklu Kullanici Raporu (Tek Ekran)

**Hedef:** Birden fazla kullanici secilsin, her biri icin ayri rapor tek sayfada gosterilsin

**Ozellikler:**
- [ ] Checkbox ile coklu kullanici secimi
- [ ] Her kullanici icin ayri rapor blogu
- [ ] Yan yana veya alt alta gorunum
- [ ] Toplu PDF/Markdown export
- [ ] Paralel rapor olusturma (hiz icin)

**UI Tasarimi:**
```
┌─────────────────────────────────────────────────────┐
│ Kullanici Sec: ☑ user1  ☑ user2  ☐ user3  ☑ user4 │
│ [Toplu Rapor Olustur]                               │
├─────────────────────────────────────────────────────┤
│ ┌─────────────────┐  ┌─────────────────┐           │
│ │ @user1 Raporu   │  │ @user2 Raporu   │           │
│ │ ...             │  │ ...             │           │
│ └─────────────────┘  └─────────────────┘           │
│ ┌─────────────────┐                                │
│ │ @user4 Raporu   │                                │
│ │ ...             │                                │
│ └─────────────────┘                                │
└─────────────────────────────────────────────────────┘
```

---

### 3. Otomatik Haftalik Scraping

**Hedef:** Her hafta otomatik tweet toplama

**Secenekler:**
- Linux cron job
- Python scheduler (APScheduler)
- Systemd timer

**Ornek Cron:**
```bash
# Her Pazartesi 09:00
0 9 * * 1 cd /home/baran/Desktop/MeclisIstihbaratSistemi && .venv/bin/python workers/update_worker.py
```

---

### 4. Daha Fazla Meclis Uyesi

**Mevcut:** 13 uye (Kecioren)

**Hedef:** Tum Ankara BBB meclis uyeleri

**Gerekli:**
- [ ] Tam liste edinme
- [ ] Twitter hesaplarini bulma
- [ ] data.csv guncelleme

---

### 5. Karsilastirmali Rapor

**Hedef:** Uyeler arasi karsilastirma

**Ozellikler:**
- En aktif 5 uye
- En cok etkilesim alan uyeler
- Parti bazli karsilastirma
- Konu bazli dagilim

---

### 6. Bildirim Sistemi

**Hedef:** Onemli degisikliklerde bildirim

**Tetikleyiciler:**
- Yeni viral tweet (>1000 engagement)
- Takipci kaybi/artisi (>%5)
- Onemli anahtar kelime tespiti

**Kanallar:**
- Email (SMTP)
- Telegram Bot
- Discord Webhook

---

### 7. Dashboard Grafikleri

**Hedef:** Trend analizi gorselleri

**Grafikler:**
- Takipci trendi (cizgi grafik)
- Engagement dagilimi (bar chart)
- Konu dagilimi (pie chart)
- Aktivite haritasi (heatmap)

**Araclar:**
- Plotly
- Gradio Plot komponenti

---

## Oncelik Sirasi

| # | Gorev | Oncelik | Zorluk |
|---|-------|---------|--------|
| 1 | Tweet scraper fix | YUKSEK | ORTA |
| 2 | Coklu kullanici raporu | YUKSEK | ORTA |
| 3 | Otomatik scraping | ORTA | DUSUK |
| 4 | Daha fazla uye | ORTA | DUSUK |
| 5 | Karsilastirmali rapor | ORTA | ORTA |
| 6 | Bildirim sistemi | DUSUK | YUKSEK |
| 7 | Dashboard grafikleri | DUSUK | ORTA |

---

## Notlar

- Tweet scraper sorunu oncelikli cozulmeli
- Gradio UI'da grafikler icin Plotly entegrasyonu gerekli
- Bildirim sistemi icin harici servis (Telegram/SMTP) kurulumu gerekli