"""
Query Reasoner - Political Context Understanding Layer

Bu modül, kullanıcı sorgularını politik bağlamda analiz eder ve zenginleştirir.
GPT modelini "düşünme" adımı olarak kullanır.

Temel yetenekler:
1. Politik eşleştirmeler (AKP = hükümet = iktidar)
2. Muhalefet/iktidar ilişkileri
3. Sorgu genişletme ve bağlam çıkarma
4. Türkçe dil ve politik terminoloji
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger("QueryReasoner")


# =============================================================================
# POLITICAL KNOWLEDGE BASE
# =============================================================================

POLITICAL_CONTEXT = """
## Türkiye Politik Yapısı (2024)

### İktidar Bloğu (Cumhur İttifakı)
- **AK Parti (AKP)**: İktidar partisi, hükümet, Cumhurbaşkanlığı
  - Eşanlamlılar: AKP, AK Parti, Adalet ve Kalkınma Partisi, iktidar, hükümet, Saray, Ankara
  - Lider: Cumhurbaşkanı Erdoğan
  - "Hükümet eleştirisi" = "AK Parti eleştirisi" = "iktidar eleştirisi"

- **MHP**: İktidar ortağı, Cumhur İttifakı
  - Lider: Devlet Bahçeli

- **BBP**: İktidar destekçisi

### Muhalefet Bloğu
- **CHP**: Ana muhalefet partisi
  - Eşanlamlılar: muhalefet, ana muhalefet
  - Belediyeler: İstanbul (İmamoğlu), Ankara (Yavaş)
  - "Muhalefet eleştirisi" = "CHP eleştirisi"

- **İYİ Parti**: Muhalefet
  - Lider: Meral Akşener

- **DEM Parti (eski HDP)**: Muhalefet

### Kritik Eşleştirmeler
- hükümet → AK Parti, AKP
- iktidar → AK Parti, AKP
- muhalefet → CHP (birincil), İYİ Parti, DEM Parti
- belediye başkanı eleştirisi (CHP bölgesinde) → muhtemelen AKP'li eleştiriyor
- ekonomi eleştirisi → genelde hükümet eleştirisi
- zam, enflasyon, hayat pahalılığı → hükümet eleştirisi
"""


@dataclass
class ReasonedQuery:
    """Zenginleştirilmiş sorgu sonucu"""
    original_query: str
    reasoning: str  # Model'in düşünce süreci
    enhanced_query: str  # Genişletilmiş sorgu
    search_terms: list[str]  # Aranacak terimler
    target_party: str | None  # Eleştirilen parti
    source_party: str | None  # Eleştiren parti (UI'dan)
    intent: str  # criticism, support, neutral, information
    political_context: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0


class QueryReasoner:
    """
    Sorgu anlamlandırma ve zenginleştirme katmanı.

    Kullanıcı sorgusunu alır, politik bağlamda analiz eder,
    ve arama için optimize edilmiş parametreler döndürür.
    """

    def __init__(self):
        """Initialize with OpenAI client."""
        self.client = None
        self.model = "gpt-4o"  # En iyi reasoning için

        if settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key)
            logger.info(f"QueryReasoner initialized with {self.model}")
        else:
            logger.warning("QueryReasoner: OpenAI API key not found, using fallback")

    def reason(
        self,
        query: str,
        party_filter: str | None = None,
        platform: str = "twitter"
    ) -> ReasonedQuery:
        """
        Sorguyu analiz et ve zenginleştir.

        Args:
            query: Kullanıcının ham sorgusu
            party_filter: UI'dan seçilen parti filtresi
            platform: Arama platformu

        Returns:
            ReasonedQuery: Zenginleştirilmiş sorgu bilgileri
        """
        if not self.client:
            return self._fallback_reasoning(query, party_filter)

        try:
            return self._llm_reasoning(query, party_filter, platform)
        except Exception as e:
            logger.error(f"LLM reasoning failed: {e}")
            return self._fallback_reasoning(query, party_filter)

    def _llm_reasoning(
        self,
        query: str,
        party_filter: str | None,
        platform: str
    ) -> ReasonedQuery:
        """GPT ile sorgu analizi."""

        system_prompt = f"""Sen bir Türk politik analisti ve arama uzmanısın.
Görevin: Kullanıcının sorgusunu analiz edip, sosyal medya araması için optimize etmek.

{POLITICAL_CONTEXT}

## Görevin
1. Sorguyu politik bağlamda analiz et
2. Gizli anlamları ve eşleştirmeleri bul
3. Arama terimlerini genişlet
4. Hedef partiyi belirle

## Önemli Kurallar
- "hükümet eleştirisi" = AK Parti/AKP eleştirisi
- "iktidar eleştirisi" = AK Parti/AKP eleştirisi
- "muhalefet eleştirisi" = CHP eleştirisi (birincil)

## KRİTİK: KONU ≠ ELEŞTİRİ
- "ekonomi hakkında tweetler" → intent: "information" (ELEŞTİRİ DEĞİL!)
- "belediye hizmetleri" → intent: "information" (ELEŞTİRİ DEĞİL!)
- Sadece AÇIK eleştiri kelimeleri varsa intent: "criticism" olmalı
- Eleştiri kelimeleri: eleştiri, başarısız, berbat, rezalet, kötü, felaket, skandal
- "ekonomi eleştirisi" → intent: "criticism" (eleştiri kelimesi VAR)
- "ekonomi hakkında" → intent: "information" (eleştiri kelimesi YOK)

## Platform
Arama yapılacak platform: {platform}
{"Tweet" if platform == "twitter" else "Instagram postu" if platform == "instagram" else "İçerik"} aranacak.

## Parti Filtresi
{"Seçili parti: " + party_filter + " (bu partinin üyelerinin paylaşımları aranacak)" if party_filter else "Parti filtresi yok (tüm partiler)"}
"""

        user_prompt = f"""Kullanıcı sorgusu: "{query}"

Lütfen JSON formatında yanıt ver:
{{
    "reasoning": "Adım adım düşünce sürecin (Türkçe). Sorguyu nasıl yorumladın, hangi politik bağlamları tespit ettin?",
    "enhanced_query": "Genişletilmiş ve netleştirilmiş sorgu metni",
    "search_terms": ["aranacak", "kelimeler", "ve", "ifadeler"],
    "target_party": "Eleştirilen/hedef alınan parti (AK Parti, CHP, MHP, vb.) veya null",
    "intent": "criticism | support | neutral | information",
    "confidence": 0.0-1.0 arası güven skoru,
    "synonyms": {{
        "original_term": ["eşanlamlı1", "eşanlamlı2"]
    }}
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        logger.info(f"QueryReasoner thinking: {result.get('reasoning', '')[:200]}...")

        return ReasonedQuery(
            original_query=query,
            reasoning=result.get("reasoning", ""),
            enhanced_query=result.get("enhanced_query", query),
            search_terms=result.get("search_terms", []),
            target_party=result.get("target_party"),
            source_party=party_filter,
            intent=result.get("intent", "information"),
            political_context={
                "synonyms": result.get("synonyms", {}),
            },
            confidence=result.get("confidence", 0.7)
        )

    def _fallback_reasoning(
        self,
        query: str,
        party_filter: str | None
    ) -> ReasonedQuery:
        """LLM olmadan basit kural tabanlı analiz."""

        query_lower = query.lower()

        # Basit eşleştirmeler
        target_party = None
        intent = "information"
        search_terms = []

        # Explicit criticism keywords - MUST be present to set intent=criticism
        criticism_terms = [
            "eleştir", "elestir", "eleştiri", "elestiri",
            "kötü", "kotu", "başarısız", "basarisiz", "berbat",
            "rezalet", "skandal", "yolsuzluk", "felaket",
            "karşı", "karsi", "tepki", "protesto"
        ]
        has_criticism = any(term in query_lower for term in criticism_terms)

        # Set intent based on explicit criticism keywords
        if has_criticism:
            intent = "criticism"

        # Hükümet/iktidar → AK Parti (only as target if criticism is explicit)
        if any(term in query_lower for term in ["hükümet", "hukumet", "iktidar", "saray", "ankara"]):
            if has_criticism:
                target_party = "AK Parti"
            search_terms.extend(["hükümet", "iktidar", "AKP", "AK Parti", "Erdoğan"])

        # Muhalefet → CHP (only as target if criticism is explicit)
        if any(term in query_lower for term in ["muhalefet", "ana muhalefet"]):
            if has_criticism:
                target_party = "CHP"
            search_terms.extend(["muhalefet", "CHP", "İmamoğlu", "Mansur Yavaş"])

        # Ekonomi - DOES NOT automatically mean criticism or hükümet
        # Just add search terms, let semantic search find relevant content
        econ_terms = ["ekonomi", "zam", "enflasyon", "pahalılık", "pahalilik", "maaş", "maas", "dolar"]
        if any(term in query_lower for term in econ_terms):
            search_terms.extend(["ekonomi", "ekonomik", "mali", "finansal"])
            # Only set target_party if EXPLICIT criticism keywords present
            if has_criticism and not target_party:
                target_party = "AK Parti"
                intent = "criticism"
            # If no criticism keywords, this is just an information search
            # about economy - don't assume it's criticism

        return ReasonedQuery(
            original_query=query,
            reasoning="Fallback kural tabanlı analiz kullanıldı.",
            enhanced_query=query,
            search_terms=list(set(search_terms)) if search_terms else query.split(),
            target_party=target_party,
            source_party=party_filter,
            intent=intent,
            confidence=0.5
        )


# Singleton instance
_reasoner_instance = None

def get_reasoner() -> QueryReasoner:
    """Get or create QueryReasoner singleton."""
    global _reasoner_instance
    if _reasoner_instance is None:
        _reasoner_instance = QueryReasoner()
    return _reasoner_instance
