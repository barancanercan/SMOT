# Meclis Istihbarat Sistemi - ROADMAP

**Son Guncelleme:** 2026-01-11
**Versiyon:** 2.0

---

## CLAUDE CODE ICIN REHBER

Bu dosya, projenin diger bilgisayardan calistirildiginda Claude Code'un takip edecegi adimlari icerir.

---

## MEVCUT DURUM

### Tamamlanan Ozellikler

| Ozellik | Durum | Notlar |
|---------|-------|--------|
| Tweet Scraping | ✅ TAMAM | 12,480 tweet, 85/86 kullanici |
| Database Schema | ✅ TAMAM | SQLite v4.1 |
| Rapor Olusturma | ✅ TAMAM | Tek/toplu rapor, Markdown export |
| LLM Entegrasyonu | ✅ TAMAM | Ollama + qwen2.5:7b |
| Vector Database | ✅ TAMAM | ChromaDB + embeddings |
| Streamlit UI | ✅ TAMAM | Yeni eklendi |
| Resume Scraping | ✅ TAMAM | `--resume` parametresi |

### Veritabani Istatistikleri

```
Toplam Tweet: 12,480
Orijinal Tweet: 3,764
Retweet: 8,716
Aktif Kullanici: 85/86
Profile History: 0 (henuz toplanmadi)
```

---

## BILINEN PROBLEMLER

### 1. Profil Bilgileri Eksik
**Problem:** `profile_history` tablosu bos, takipci/takip sayilari toplanmamis.
**Cozum:** Profile scraper calistirilmali.
```bash
python scraping/profile_scraper.py --all
```

### 2. Bazi Raporlarda "Profil verisi bulunamadi"
**Problem:** Rapor olusturulurken profil bilgileri gosterilemiyor.
**Cozum:** Yukaridaki profil scraper calistirilmali.

### 3. Gradio UI Uyumsuzluk Uyarisi
**Problem:** Gradio 6.0 ile theme/css parametreleri launch()'a tasinmis.
**Cozum:** Streamlit UI kullanilmali (onerilen).

### 4. Cok Fazla Retweet
**Problem:** 8,716 retweet vs 3,764 orijinal tweet. Raporlar sadece orijinal tweetleri gosteriyor.
**Cozum:** Bu kasitli bir tasarim karari - retweet'ler analiz icin anlamli degil.

---

## DIGER BILGISAYAR ICIN ADIMLAR

### Adim 1: Kodu Cek
```bash
cd ~/Desktop
git clone https://github.com/barancanercan/MeclisIstihbaratSistemi.git
# veya mevcut repo varsa:
git pull origin main
```

### Adim 2: Ortami Kur
```bash
cd MeclisIstihbaratSistemi
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Adim 3: Streamlit'i Yukle (eger requirements.txt guncellenmemisse)
```bash
pip install streamlit>=1.30.0
```

### Adim 4: Veritabani Kontrol
```bash
# Eger meclis.db yoksa veya bozuksa:
python database.py

# Mevcut verileri gormek icin:
python -c "from database import get_stats; print(get_stats())"
```

### Adim 5: UI Baslat
```bash
# Streamlit (onerilen)
streamlit run ui/streamlit_app.py

# veya Gradio
python ui/app.py
```

### Adim 6: Profil Bilgilerini Topla (opsiyonel)
```bash
python scraping/profile_scraper.py --all
```

---

## GELECEK GELISTIRMELER (V3)

### Oncelik 1: Profil Scraping
- [ ] Takipci/takip sayilarini topla
- [ ] Haftalik karsilastirma icin gecmis kaydet
- [ ] Raporlara profil bilgilerini ekle

### Oncelik 2: Dashboard Grafikleri
- [ ] Engagement trend grafigi
- [ ] Kullanici karsilastirma grafigi
- [ ] Parti bazli analiz
- [ ] Streamlit'e Plotly entegrasyonu

### Oncelik 3: Otomatik Haftalik Scraping
- [ ] Cron job veya systemd timer
- [ ] Email/Telegram bildirimi
- [ ] Hata raporlama

### Oncelik 4: Karsilastirmali Rapor
- [ ] Birden fazla kullanici karsilastirmasi
- [ ] Parti bazli karsilastirma
- [ ] Zaman bazli trend analizi

### Oncelik 5: Export Ozellikleri
- [ ] PDF export
- [ ] Excel export
- [ ] Otomatik rapor arsivleme

---

## DOSYA DEGISIKLIKLERI (Bu Oturum)

### Yeni Dosyalar
- `ui/streamlit_app.py` - Yeni Streamlit UI
- `docs/ROADMAP.md` - Bu dosya

### Guncellenen Dosyalar
- `README.md` - v2.0 icin guncellendi
- `requirements.txt` - streamlit eklendi
- `run_full_scrape.py` - `--resume` ve `--start` parametreleri eklendi

---

## NOTLAR

1. **LLM Performansi:** CPU'da qwen2.5:7b yavas (~30-60sn/soru). Hizli mod (`--no-llm`) onerilen.

2. **Session Crash:** Tweet scraping sirasinda browser crash olursa `--resume` ile devam edilebilir.

3. **Veri Boyutu:** 12,480 tweet ~5MB SQLite dosyasi. ChromaDB ayrica ~50MB.

4. **UI Tercihi:** Streamlit daha hizli ve sade. Gradio daha fazla ozellik sunuyor ama yavas.

---

## HIZLI REFERANS

```bash
# Tweet toplama
python run_full_scrape.py --resume

# Hizli rapor
python reporting/report_generator.py --user USERNAME --no-llm

# UI baslat
streamlit run ui/streamlit_app.py

# Cache temizle
python reporting/report_generator.py --clear-cache

# Metrik sirala
python reporting/metrics.py --users user1 user2 --ranking
```

---

*Bu dosya Claude Code tarafindan otomatik olusturulmustur.*
