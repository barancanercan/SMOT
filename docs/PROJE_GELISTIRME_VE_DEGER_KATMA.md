# Proje Gelistirme ve Deger Katma Onerileri

> **Meclis Istihbarat Sistemi - Stratejik Urun Yol Haritasi**
>
> Tarih: Mart 2026 | Versiyon: 3.0

---

## Executive Summary

Meclis Istihbarat Sistemi, Turkiye'deki buyuksehir belediye meclis uyelerinin sosyal medya aktivitelerini analiz eden bir AI-powered SaaS platformudur. Mevcut haliyle **MVP asamasindadir** ve ciddi guvenlik, olcekleme ve urunlestirme eksiklikleri vardir. Bu rapor, projeyi **ticari bir SaaS urunune** donusturmek icin stratejik yol haritasi sunmaktadir.

**Mevcut Durum:** MVP (Minimum Viable Product)
**Hedef:** Production-Ready SaaS (6 ay)
**Potansiyel Pazar:** Siyasi danismanlik, medya kuruluslari, akademik arastirmacilar

---

## Product-Market Fit Analizi

### Hedef Kullanici Segmentleri

| Segment | Ihtiyac | Odeme Potansiyeli |
|---------|--------|-------------------|
| **Siyasi Danismanlar** | Rakip analizi, trend izleme | Yuksek |
| **Medya Kuruluslari** | Gundem takibi, haber kaynagi | Orta-Yuksek |
| **PR Ajanslari** | Kriz yonetimi, mesaj analizi | Yuksek |
| **Akademisyenler** | Arastirma verisi | Dusuk |
| **Parti Teskilatlari** | Ic analiz, performans olcumu | Orta |

### Rekabet Analizi

| Rakip | Guc | Zayiflik | Farklilasma Firsati |
|-------|-----|----------|---------------------|
| Genel sosyal medya izleme (Brandwatch vb.) | Kapsamli, global | Turkiye odakli degil, pahali | Yerel uzmanlik |
| Manuel analiz | Ucuz | Yavas, olceklenemiyor | Otomasyon |
| Haber takip servisleri | Yerlesik | Derinlemesine analiz yok | AI istihbarat |

### Unique Value Proposition

> "Turkiye siyaseti icin ozel tasarlanmis, AI-destekli sosyal medya istihbarat platformu"

**Temel Farkliliklar:**
1. Turkce dil ve siyasi baglamda uzmanlasmis LLM analizi
2. Yesil/Kirmizi/Gri takim metodolojisi
3. Meclis uyesi odakli veri yapilandirmasi
4. Yerel market bilgisi

---

## SaaS Product Roadmap

### Faz 1: Foundation (0-2 Ay)

**Hedef:** Production-ready altyapi

| Gorev | Oncelik | Hafta |
|-------|---------|-------|
| JWT Authentication | P0 | 1 |
| CORS & Rate Limiting | P0 | 1 |
| PostgreSQL Migration | P1 | 2-3 |
| Celery Async Tasks | P1 | 3-4 |
| Error Boundaries (FE) | P0 | 1 |
| React Query Standardization | P0 | 2 |
| Temel UI Components | P1 | 3-4 |

**Cikti:** Guvenli, olceklenebilir temel sistem

---

### Faz 2: Product Enhancement (2-4 Ay)

**Hedef:** Ticari degeri artir

| Ozellik | Aciklama | Oncelik |
|---------|----------|---------|
| Dashboard v2 | Interaktif grafikler, trendler | P1 |
| Karsilastirmali Analiz | Birden fazla kullaniciyi karsilastir | P1 |
| Alarm/Alert Sistemi | Anomali tespiti, bildirim | P1 |
| Export Genisletme | PDF rapor, Excel veri | P2 |
| Arama ve Filtreleme | Gelismis sorgulama | P1 |
| Kullanici Yonetimi | Coklu kullanici, roller | P0 |

**Yeni Ozellik Detaylari:**

#### Karsilastirmali Analiz
```
Kullanici A vs Kullanici B
├── Engagement metrikleri
├── Konu dagilimi
├── Sadakat skorlari
└── Zaman serisi karsilastirmasi
```

#### Alert Sistemi
```python
# Ornek alert kurallari
AlertRule(
    name="Follower Spike",
    condition="followers_change > 1000 in 24h",
    action="email_notification"
)

AlertRule(
    name="Viral Tweet",
    condition="tweet_likes > 10000",
    action="dashboard_alert + email"
)

AlertRule(
    name="Muhalefet Tonu Degisimi",
    condition="criticism_level changed from 'Dusuk' to 'Yuksek'",
    action="report_generation"
)
```

---

### Faz 3: Scale & Monetize (4-6 Ay)

**Hedef:** Gelir uretmeye basla

| Gorev | Aciklama |
|-------|----------|
| Multi-tenant Architecture | Her musteriye izole ortam |
| Subscription Billing | Stripe entegrasyonu |
| API Rate Tiers | Kullanim bazli fiyatlandirma |
| White-label Option | Musteri markasi ile sunma |
| SLA & Support | Destek katmanlari |

---

## Monetizasyon Stratejileri

### Tier Yapisi

| Tier | Fiyat/Ay | Ozellikler |
|------|----------|------------|
| **Free** | 0 TL | 5 kullanici izleme, temel dashboard, 7 gunluk veri |
| **Pro** | 1.499 TL | 50 kullanici, LLM analiz, 90 gunluk veri, export |
| **Enterprise** | 4.999 TL | Sinirsiz kullanici, ozel model, 1 yil veri, API erişimi |
| **API** | Kullanim bazli | Dakikada 100 istek, webhook, bulk data |

### Gelir Projeksiyonu (12 Ay)

| Ay | Free | Pro | Enterprise | MRR |
|----|------|-----|------------|-----|
| 1 | 50 | 0 | 0 | 0 TL |
| 3 | 100 | 5 | 0 | 7.495 TL |
| 6 | 200 | 20 | 2 | 39.978 TL |
| 12 | 500 | 50 | 10 | 124.870 TL |

**Varsayimlar:**
- Free-to-Pro conversion: 5%
- Pro-to-Enterprise upgrade: 10%
- Churn rate: 5%/ay

---

## Feature Prioritization Matrix

| Ozellik | Impact | Effort | Skor | Oncelik |
|---------|--------|--------|------|---------|
| Authentication | 10 | 3 | 3.33 | P0 |
| Alert System | 9 | 5 | 1.80 | P1 |
| Comparative Analysis | 8 | 4 | 2.00 | P1 |
| PDF Reports | 6 | 2 | 3.00 | P2 |
| Multi-tenant | 10 | 8 | 1.25 | P1 |
| White-label | 7 | 6 | 1.17 | P2 |
| Mobile App | 5 | 9 | 0.56 | P3 |
| RAG Search | 8 | 7 | 1.14 | P2 |

**Skor = Impact / Effort** (yuksek skor = once yap)

---

## Technical Debt Yonetimi

### Mevcut Technical Debt Envanteri

| Debt | Dosya | Risk | Odeme Maliyeti |
|------|-------|------|----------------|
| CORS wildcard | `main.py:37` | Kritik | Low |
| Senkron LLM | `analyzer.py:87` | Yuksek | Medium |
| SQLite | `config.py:40` | Yuksek | High |
| No tests | - | Orta | High |
| Hardcoded model | `analyzer.py:26` | Orta | Low |
| No pagination | `users.py:17` | Orta | Low |
| Mixed state mgmt | `reports/page.tsx` | Dusuk | Medium |

### Debt Odeme Stratejisi

```
Sprint 1-2: Kritik guvenlik (CORS, Auth)
Sprint 3-4: Altyapi (PostgreSQL, Celery)
Sprint 5-6: Kalite (Tests, Observability)
Sprint 7+: Refactoring (as needed)
```

**Kural:** Her sprint'te %20 kapasite debt odemeye ayrilmali

---

## Takim Olceklendirme Onerileri

### Mevcut Durum (Varsayim)
- 1 Full-stack Developer

### Faz 1 Takim (MVP → Alpha)
| Rol | Kisi | Sorumluluk |
|-----|------|------------|
| Full-stack Dev | 1 | Backend + Frontend |
| DevOps (Part-time) | 0.5 | CI/CD, Infra |

### Faz 2 Takim (Alpha → Beta)
| Rol | Kisi | Sorumluluk |
|-----|------|------------|
| Backend Dev | 1 | API, LLM, DB |
| Frontend Dev | 1 | UI/UX, Components |
| DevOps | 0.5 | Infra, Monitoring |
| Product Manager | 0.5 | Roadmap, User Research |

### Faz 3 Takim (Beta → Production)
| Rol | Kisi | Sorumluluk |
|-----|------|------------|
| Backend Dev | 2 | API, Scraping, LLM |
| Frontend Dev | 1 | UI/UX |
| ML Engineer | 1 | Model optimization |
| DevOps | 1 | Infra, SRE |
| Product Manager | 1 | Product strategy |
| Customer Success | 1 | Support, Onboarding |

---

## Basari Metrikleri

### Teknik KPI'lar

| Metrik | Mevcut | 3 Ay | 6 Ay | 12 Ay |
|--------|--------|------|------|-------|
| API Uptime | N/A | 99% | 99.5% | 99.9% |
| P95 Latency | 500ms | 300ms | 150ms | 100ms |
| Error Rate | N/A | <5% | <2% | <1% |
| Test Coverage | 0% | 50% | 70% | 80% |
| Security Score | 2/10 | 6/10 | 8/10 | 9/10 |

### Is KPI'lari

| Metrik | 3 Ay | 6 Ay | 12 Ay |
|--------|------|------|-------|
| Registered Users | 100 | 250 | 700 |
| Paying Customers | 5 | 25 | 75 |
| MRR | 7.5K TL | 40K TL | 125K TL |
| Churn Rate | 10% | 7% | 5% |
| NPS | N/A | 30 | 50 |

### Urun KPI'lari

| Metrik | 3 Ay | 6 Ay | 12 Ay |
|--------|------|------|-------|
| Weekly Active Users | 30 | 100 | 300 |
| Reports Generated/Week | 50 | 200 | 1000 |
| Avg Session Duration | 5 min | 10 min | 15 min |
| Feature Adoption (Alerts) | N/A | 30% | 60% |

---

## Risk Analizi

| Risk | Olasilik | Etki | Azaltma |
|------|----------|------|---------|
| Twitter/X API degisikligi | Yuksek | Kritik | Alternatif scraping, official API lisansi |
| LLM maliyet artisi | Orta | Yuksek | Self-hosted modeller, caching |
| Yasal sorunlar (veri gizliligi) | Orta | Kritik | KVKK uyumlulugu, yasal danismanlik |
| Rekabet girisi | Yuksek | Orta | Hizli iterasyon, niche odaklanma |
| Takim kaybi | Dusuk | Yuksek | Dokumantasyon, knowledge sharing |

---

## Sonraki Adimlar

### Bu Hafta (Immediate Actions)

1. **CORS Duzelt** - `main.py:37` → 2 saat
2. **Rate Limiting Ekle** - slowapi → 4 saat
3. **JWT Auth Baslat** - Temel yapi → 1 gun

### Bu Ay (Short-term)

1. PostgreSQL migration plani
2. Celery POC
3. UI component library baslangiç
4. Test framework kurulumu

### Bu Ceyrek (Medium-term)

1. Alpha release
2. Ilk 10 beta kullanici
3. Pricing validation
4. Alert sistemi MVP

---

## Ek: Mimari Hedef Durumu

```
                    ┌─────────────────┐
                    │   CloudFlare    │
                    │   (CDN + WAF)   │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
    ┌─────────┴─────────┐         ┌────────┴────────┐
    │   Next.js (FE)    │         │  FastAPI (BE)   │
    │   Vercel/Docker   │         │     Docker      │
    └───────────────────┘         └────────┬────────┘
                                           │
              ┌────────────────────────────┼────────────────────────────┐
              │                            │                            │
    ┌─────────┴─────────┐        ┌────────┴────────┐        ┌─────────┴─────────┐
    │    PostgreSQL     │        │      Redis      │        │      Ollama       │
    │   (Managed/RDS)   │        │  (Cache/Queue)  │        │   (GPU Server)    │
    └───────────────────┘        └────────┬────────┘        └───────────────────┘
                                          │
                                 ┌────────┴────────┐
                                 │  Celery Workers │
                                 │    (Scraping)   │
                                 └─────────────────┘
```

---

## Referans Dokumanlar

- [LLM Gelistirme Onerileri](./LLM_GELISTIRME_ONERILERI.md)
- [Backend Gelistirme Onerileri](./BACKEND_GELISTIRME_ONERILERI.md)
- [Frontend Gelistirme Onerileri](./FRONTEND_GELISTIRME_ONERILERI.md)

---

*Bu rapor Meclis Istihbarat Sistemi v3.0 kod tabanina dayanmaktadir.*
