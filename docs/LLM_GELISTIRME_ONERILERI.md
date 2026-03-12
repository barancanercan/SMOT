# LLM Gelistirme Onerileri

> **Meclis Istihbarat Sistemi - Yapay Zeka Analiz Modulu Uzman Raporu**
>
> Tarih: Mart 2026 | Versiyon: 3.0

---

## Executive Summary

Mevcut LLM entegrasyonu Ollama uzerinden calisan, Pydantic ile validasyon yapan temel bir yapidir. **Senkron istek modeli, gozlemlenebilirlik eksikligi ve tek few-shot ornek** ana zayifliklardir. Asagidaki oneriler, sistemi production-grade bir AI platformuna donusturmek icin onceliklendirilmistir.

**Mevcut Skor:** 5/10
**Hedef Skor:** 8.5/10 (6 ay sonra)

---

## Mevcut Durum Analizi

### Guclu Yanlar
| Alan | Detay | Dosya |
|------|-------|-------|
| Structured Output | JSON mode + Pydantic validasyon | `analyzer.py:74` |
| Fallback Mekanizmasi | Manuel alan cikarma | `analyzer.py:186-204` |
| JSON-LD Temizleme | `_clean_json_response()` fonksiyonu | `analyzer.py:103-143` |
| Retry Logic | max_retries parametresi | `analyzer.py:85-100` |

### Zayif Yanlar
| Alan | Sorun | Etki |
|------|-------|------|
| Senkron Cagrilar | 300s timeout API'yi bloke eder | `analyzer.py:87` |
| Tek Few-Shot | Sadece 1 ornek analiz | `prompts.py:40-51` |
| Monitoring Yok | LLM performansi izlenemiyor | - |
| Model Hardcoded | Degisiklik kod degisikligi gerektirir | `analyzer.py:26-28` |

---

## P0: Kritik Oncelik (Hemen Yapilmali)

### 1. Async LLM Isleme

**Problem:** `_call_llm()` senkron olarak 300s bekleyebilir, API thread'ini bloke eder.

**Cozum:**
```python
# analyzer.py - Async versiyon
import httpx

async def _call_llm_async(self, prompt: str) -> str:
    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post(
            f"{self.base_url}/api/chat",
            json=payload
        )
        return resp.json()["message"]["content"]
```

**Dosya:** `backend/app/services/analysis/analyzer.py:56-101`

| Metrik | Mevcut | Hedef |
|--------|--------|-------|
| API Timeout | 300s blocking | Non-blocking async |
| Concurrent Requests | 1 | 10+ |

**Effort:** Medium | **Impact:** Critical

---

### 2. Confidence Scoring

**Problem:** LLM ciktisinin guvenilirligini olcecek bir metrik yok.

**Cozum:**
```python
# schemas.py - Confidence ekle
class IntelligenceAnalysis(BaseModel):
    executive_summary: str
    confidence_score: float = Field(ge=0, le=1, description="0-1 arasi guven skoru")
    evidence_count: int = Field(ge=0, description="Destekleyen tweet sayisi")

    # Mevcut alanlar...
```

**Prompt Guncellemesi (`prompts.py`):**
```
Analizin sonunda 0-1 arasi bir confidence_score ver:
- 0.9+: Cok net kaliplar, 10+ destekleyen tweet
- 0.7-0.9: Orta net kaliplar, 5-10 destekleyen tweet
- 0.5-0.7: Zayif kaliplar, 2-5 destekleyen tweet
- 0.5 alti: Belirsiz, yetersiz veri
```

**Dosya:** `backend/app/services/analysis/schemas.py:40-55`

**Effort:** Low | **Impact:** High

---

## P1: Yuksek Oncelik (30 Gun Icinde)

### 3. Observability Layer

**Problem:** LLM cagrilarinin performansi, hatalari ve maliyet izlenemiyor.

**Cozum:**
```python
# utils/llm_metrics.py (yeni dosya)
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class LLMMetrics:
    request_id: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    success: bool
    error_type: str = None

    def log(self):
        logger.info(json.dumps(asdict(self)))

# Kullanim (analyzer.py)
metrics = LLMMetrics(
    request_id=uuid4().hex,
    model=self.model,
    latency_ms=(time.time() - start) * 1000,
    ...
)
metrics.log()
```

**Metriklerin Toplanmasi:**
| Metrik | Aciklama |
|--------|----------|
| `llm_request_duration_seconds` | Istek suresi histogram |
| `llm_token_usage_total` | Token kullanimi counter |
| `llm_validation_errors_total` | Pydantic hata sayisi |
| `llm_cache_hit_rate` | Cache isabet orani |

**Effort:** Medium | **Impact:** High

---

### 4. Multi-Shot Ornekler

**Problem:** Tek few-shot ornek model performansini sinirliyor (`prompts.py:40-51`).

**Cozum:**
```python
# prompts.py - Coklu ornek
FEW_SHOT_EXAMPLES = [
    {
        "input": "CHP uyesi, belediye baskani",
        "output": {
            "executive_summary": "...",
            "green_summary": "Parti liderligine acik destek...",
            "loyalty_level": "Yuksek",
            # ...
        }
    },
    {
        "input": "AKP uyesi, muhalefeti elestiren",
        "output": {
            "executive_summary": "...",
            "red_summary": "CHP ve HDP'yi sert sekilde elestiriyor...",
            "criticism_level": "Yuksek",
            # ...
        }
    },
    {
        "input": "MHP uyesi, milliyetci soylemleri agir basan",
        "output": {
            "executive_summary": "...",
            # ...
        }
    }
]
```

**Dosya:** `backend/app/services/analysis/prompts.py:27-60`

**Beklenen Iyilesme:**
| Metrik | Mevcut | Hedef |
|--------|--------|-------|
| Validation Success Rate | ~70% | 90%+ |
| Output Consistency | Degisken | Tutarli |

**Effort:** Low | **Impact:** High

---

### 5. Model Registry

**Problem:** Model secimi hardcoded, A/B test mumkun degil.

**Cozum:**
```python
# core/model_registry.py (yeni dosya)
from enum import Enum
from typing import Dict

class ModelCapability(Enum):
    TURKISH_ANALYSIS = "turkish_analysis"
    FAST_INFERENCE = "fast_inference"
    LONG_CONTEXT = "long_context"

MODEL_REGISTRY: Dict[str, dict] = {
    "qwen3:14b": {
        "capabilities": [ModelCapability.TURKISH_ANALYSIS, ModelCapability.LONG_CONTEXT],
        "context_window": 8192,
        "avg_latency_ms": 15000,
        "quality_score": 0.85,
    },
    "qwen2.5:3b": {
        "capabilities": [ModelCapability.FAST_INFERENCE],
        "context_window": 4096,
        "avg_latency_ms": 3000,
        "quality_score": 0.65,
    },
    "llama3.2:8b": {
        "capabilities": [ModelCapability.TURKISH_ANALYSIS],
        "context_window": 8192,
        "avg_latency_ms": 8000,
        "quality_score": 0.75,
    }
}

def get_best_model(capability: ModelCapability) -> str:
    candidates = [
        (name, cfg) for name, cfg in MODEL_REGISTRY.items()
        if capability in cfg["capabilities"]
    ]
    return max(candidates, key=lambda x: x[1]["quality_score"])[0]
```

**Dosya:** `backend/app/core/model_registry.py` (yeni)

**Effort:** Medium | **Impact:** Medium

---

## P2: Orta Oncelik (60 Gun Icinde)

### 6. A/B Testing Framework

**Problem:** Farkli prompt/model kombinasyonlarini test etmek manuel.

**Cozum:**
```python
# services/analysis/ab_testing.py
import random
from typing import Literal

ExperimentGroup = Literal["control", "variant_a", "variant_b"]

class ABExperiment:
    def __init__(self, experiment_name: str, weights: dict):
        self.name = experiment_name
        self.weights = weights  # {"control": 0.8, "variant_a": 0.2}

    def get_group(self, user_id: str) -> ExperimentGroup:
        # Deterministic assignment based on user_id hash
        hash_val = hash(f"{self.name}:{user_id}") % 100
        cumulative = 0
        for group, weight in self.weights.items():
            cumulative += weight * 100
            if hash_val < cumulative:
                return group
        return "control"

# Kullanim
experiment = ABExperiment(
    "prompt_v2_test",
    {"control": 0.5, "variant_a": 0.5}
)
group = experiment.get_group(username)
prompt = PROMPT_V1 if group == "control" else PROMPT_V2
```

**Effort:** High | **Impact:** Medium

---

### 7. Output Validation Pipeline

**Problem:** Pydantic validation basarisiz oldugunda fallback cok basit.

**Cozum:**
```python
# services/analysis/validators.py
from typing import List, Tuple

class ValidationPipeline:
    def __init__(self):
        self.validators = [
            self._check_required_fields,
            self._check_loyalty_level_values,
            self._check_summary_length,
            self._check_turkish_content,
        ]

    def validate(self, data: dict) -> Tuple[bool, List[str]]:
        errors = []
        for validator in self.validators:
            is_valid, error = validator(data)
            if not is_valid:
                errors.append(error)
        return len(errors) == 0, errors

    def _check_loyalty_level_values(self, data: dict) -> Tuple[bool, str]:
        valid_levels = ["Dusuk", "Orta", "Yuksek"]
        level = data.get("loyalty_level", "")
        if level not in valid_levels:
            return False, f"loyalty_level '{level}' gecersiz"
        return True, ""

    def _check_summary_length(self, data: dict) -> Tuple[bool, str]:
        summary = data.get("executive_summary", "")
        if len(summary) < 50:
            return False, "executive_summary cok kisa (min 50 karakter)"
        return True, ""
```

**Dosya:** `backend/app/services/analysis/validators.py` (yeni)

**Effort:** Medium | **Impact:** Medium

---

## P3: Gelecek Planlamasi (90+ Gun)

### 8. RAG Entegrasyonu

**Mevcut Durum:** ChromaDB entegrasyonu mevcut ama kullanilmiyor (`vector_db.py`).

**Hedef Mimari:**
```
[Tweet DB] -> [Embedding] -> [ChromaDB]
                                  |
[User Query] -> [Semantic Search] -> [Top-K Tweets]
                                          |
                              [LLM Context Injection]
                                          |
                              [Enhanced Analysis]
```

**Implementasyon Adimlari:**
1. Tum tweetleri embedding'e cevir (batch job)
2. Kullanici bazli index olustur
3. Analiz oncesi relevant tweet retrieval
4. Context window'a inject et

**Dosya:** `backend/app/services/analysis/vector_db.py`

**Effort:** High | **Impact:** High

---

### 9. Multi-Model Ensemble

**Konsept:** Birden fazla model kullanarak consensus-based sonuc.

```python
class EnsembleAnalyzer:
    def __init__(self):
        self.models = ["qwen3:14b", "llama3.2:8b"]

    async def analyze(self, tweets: List[Dict]) -> IntelligenceAnalysis:
        results = await asyncio.gather(*[
            self._analyze_with_model(tweets, model)
            for model in self.models
        ])
        return self._merge_results(results)

    def _merge_results(self, results: List[IntelligenceAnalysis]):
        # Voting/averaging logic
        loyalty_levels = [r.loyalty_level for r in results]
        consensus_loyalty = max(set(loyalty_levels), key=loyalty_levels.count)
        # ...
```

**Effort:** Very High | **Impact:** High

---

## Implementasyon Yol Haritasi

```
Hafta 1-2:
├── P0.1: Async LLM (_call_llm_async)
└── P0.2: Confidence scoring

Hafta 3-4:
├── P1.3: Observability layer
├── P1.4: Multi-shot ornekler
└── P1.5: Model registry

Hafta 5-8:
├── P2.6: A/B testing framework
└── P2.7: Validation pipeline

Hafta 9-12:
├── P3.8: RAG entegrasyonu
└── P3.9: Multi-model ensemble (POC)
```

---

## Basari Metrikleri

| KPI | Mevcut | 30 Gun | 60 Gun | 90 Gun |
|-----|--------|--------|--------|--------|
| Validation Success Rate | 70% | 85% | 90% | 95% |
| Avg Response Latency | 15s | 12s | 10s | 8s |
| Confidence Score Avg | N/A | 0.7 | 0.75 | 0.8 |
| Cache Hit Rate | N/A | 30% | 50% | 60% |
| P99 Latency | 45s | 35s | 25s | 20s |

---

## Referans Dosyalar

| Dosya | Satir | Aciklama |
|-------|-------|----------|
| `backend/app/services/analysis/analyzer.py` | 56-101 | `_call_llm()` senkron implementasyon |
| `backend/app/services/analysis/analyzer.py` | 103-143 | JSON-LD temizleme |
| `backend/app/services/analysis/analyzer.py` | 186-204 | Fallback mekanizmasi |
| `backend/app/services/analysis/prompts.py` | 31-60 | Ana prompt sablonu |
| `backend/app/services/analysis/prompts.py` | 40-51 | Tek few-shot ornek |
| `backend/app/services/analysis/schemas.py` | 40-55 | IntelligenceAnalysis modeli |
| `backend/app/api/v1/reports.py` | 28-68 | Report generation endpoint |

---

*Bu rapor Meclis Istihbarat Sistemi v3.0 kod tabanina dayanmaktadir.*
