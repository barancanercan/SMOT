# Meclis Istihbarat Sistemi - ROADMAP (v3.0 - Professional Edition)

**Son Güncelleme:** 2026-01-13
**Hedef:** MVP'den Ürüne (From MVP to Product)

---

## 🎯 VİZYON

Bu proje, sadece bir tweet toplama scripti değil; siyasi analiz, veri madenciliği ve istihbarat raporlaması yapan profesyonel, satılabilir bir **SaaS (Software as a Service)** ürününe dönüşecektir. Bunu yaparken **maliyet etkinliği (yerel LLM + ücretsiz scraping)** korunacaktır.

---

## 📅 GELİŞTİRME PLANI

### FAZ 1: Temizlik ve Standartlaşma (Code Quality)

_Kod tabanını profesyonel standartlara getirme._

- [ ] **Linter & Formatter Entegrasyonu:** `ruff` ve `mypy` kurulumu ve tüm kodun taranması.
- [ ] **Logging Mekanizması:** `print()` ifadelerinin `logging` modülü ile değiştirilmesi ve logların dosyaya yazılması.
- [ ] **Konfigürasyon Yönetimi:** `config.py` ve `.env` yapısının `pydantic-settings` ile modernize edilmesi.
- [ ] **Proje Dokümantasyonu:** Kod içi docstring'lerin tamamlanması.

### FAZ 2: Veri Toplama Dayanıklılığı (Scraping Resilience)

_Selenium yapısını koruyarak "kurşun geçirmez" hale getirme._

- [ ] **Retry Mekanizması:** Scraping hatalarında "Exponential Backoff" ile tekrar deneme yapısının kurulması (`tenacity` kütüphanesi).
- [ ] **Headless & Docker:** Scraping işleminin izole bir Docker container içinde (Browserless veya kendi imajımız) çalıştırılması.
- [ ] **User-Agent & Fingerprint Yönetimi:** Bot tespitini aşmak için daha gelişmiş teknikler.
- [ ] **Hata Yakalama:** X.com arayüz değişikliklerine karşı anlık uyarı sistemi.

### FAZ 3: Veritabanı ve Backend Dönüşümü

_Tek kişilik yapıdan çoklu kullanıcıya geçiş._

- [ ] **PostgreSQL Geçişi:** `SQLite`'tan `PostgreSQL` veri tabanına migrasyon.
- [ ] **ORM Entegrasyonu:** `SQLAlchemy 2.0` ile modern ORM yapısı.
- [ ] **Backend API:** Mantıksal katmanın `FastAPI` arkasına alınması (UI ile Logic'in ayrılması).

### FAZ 4: AI Mühendisliği (AI Engineering)

_Daha güvenilir ve yapısal analizler._

- [ ] **Structured Output:** LLM çıktılarının metin değil, %100 geçerli JSON olması (`Pydantic` veya `Instructor` ile).
- [ ] **Prompt Versiyonlama:** Promptların kod içinde değil, yönetilebilir bir yapıda tutulması.
- [ ] **Task Queue:** Analiz işlemlerinin `Celery` + `Redis` ile arka plana alınması.

### FAZ 5: Modern Arayüz ve Ticarileşme

_Müşteriye sunulabilir arayüz._

- [ ] **Dashboard Yenileme:** Streamlit yerine React/Next.js (Opsiyonel ama önerilen) veya çok gelişmiş bir Streamlit dashboard'u.
- [ ] **Authentication:** Kullanıcı girişi ve yetkilendirme.
- [ ] **Deployment:** Tek komutla (`docker-compose up`) kurulum paketi.

---

## ✅ MEVCUT DURUM (v2.1)

| Özellik           | Durum                            |
| ----------------- | -------------------------------- |
| Temel Scraping    | ✅ Çalışıyor                     |
| Yerel LLM Analizi | ✅ Çalışıyor (Ollama)            |
| Raporlama         | ✅ Çalışıyor (PDF/Excel)         |
| Arayüz            | ✅ Streamlit (Temel)             |
| Kod Kalitesi      | ⚠️ Geliştirilmeli (Script-level) |
| Hata Toleransı    | ⚠️ Düşük (Kırılgan)              |
| Mimari            | ⚠️ Monolitik/Script              |

---

## 🛠 TEKNİK YIĞIN (Hedef)

- **Backend:** Python 3.10+, FastAPI
- **Database:** PostgreSQL + pgvector
- **Queue:** Redis + Celery
- **Scraping:** Selenium (Dockerized)
- **AI:** Ollama (Local), LangChain (Orchestration)
- **DevOps:** Docker, Docker Compose

---
