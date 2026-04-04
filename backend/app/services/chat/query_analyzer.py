"""
Query Analyzer v7 - Unified Query Understanding

Merges QueryReasoner + IntentParser into a single module.
Rule-based first, optional single LLM call for complex queries.

Pipeline:
1. Rule-based: topic detection, party extraction, criticism detection, keyword extraction
2. Optional LLM: only for ambiguous queries or when rule-based confidence is low
"""

import json
import re
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field

from app.services.chat.turkish_nlp import (
    extract_keywords,
    expand_keywords,
    normalize_turkish,
    TURKISH_STOPWORDS,
)
from app.services.chat.hybrid_retriever import (
    TOPIC_KEYWORDS,
    CRITICISM_KEYWORDS,
)
from app.core.constants import normalize_party_name
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger("QueryAnalyzer")


# =============================================================================
# POLITICAL KNOWLEDGE
# =============================================================================

PARTY_PATTERNS = {
    "AK Parti": [
        r'\b(akp|ak\s*parti|akpartili|akp\'li|akpliler)\b',
        r'\b(iktidar|hükümet|hukumet)\b',
        r'\b(erdoğan|erdogan)\b',
    ],
    "CHP": [
        r'\b(chp|chp\'li|chpli|chpliler)\b',
        r'\b(kılıçdaroğlu|kilicdaroglu|özgür\s*özel|ozgur\s*ozel)\b',
        r'\b(imamoğlu|imamoglu|mansur\s*yavaş|mansur\s*yavas)\b',
    ],
    "MHP": [
        r'\b(mhp|mhp\'li|mhpli)\b',
        r'\b(bahçeli|bahceli)\b',
    ],
    "İYİ Parti": [
        r'\b(iyi\s*parti|iyip|iyi\'li)\b',
        r'\b(akşener|aksener)\b',
    ],
    "DEM Parti": [
        r'\b(dem\s*parti|hdp|dem\'li)\b',
    ],
    "BBP": [r'\b(bbp|bbp\'li)\b'],
    "YRP": [r'\b(yrp|yeniden\s*refah)\b'],
}

# When party X is selected and user asks for "criticism", who is being criticized?
OPPOSITE_PARTIES = {
    "CHP": "AK Parti",
    "AK Parti": "CHP",
    "MHP": "CHP",
    "BBP": "CHP",
    "İYİ Parti": "AK Parti",
    "YRP": "CHP",
}

GOVERNMENT_TERMS = {
    "hükümet", "hukumet", "iktidar", "saray", "ankara",
    "akp", "ak parti", "erdoğan", "erdogan", "beştepe",
}

OPPOSITION_TERMS = {
    "muhalefet", "ana muhalefet", "chp",
    "imamoğlu", "imamoglu", "mansur", "yavaş",
}


@dataclass
class AnalyzedQuery:
    """Result of query analysis."""
    original_query: str
    # Intent
    intent: str  # search_topic, search_criticism, search_user, search_date, analyze_topics
    is_criticism: bool
    confidence: float
    # Parties
    source_party: Optional[str]  # Party whose content we're searching (from UI)
    target_party: Optional[str]  # Party being criticized/discussed
    # Topic
    detected_topic: Optional[str]
    # Search parameters
    keywords: List[str]
    expanded_keywords: List[str]
    search_query: str  # Enhanced query for semantic search
    # Filters
    username: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class QueryAnalyzer:
    """
    Unified query analysis: intent + topic + party + keywords in one pass.

    Rule-based primary, optional LLM for complex queries.
    """

    def __init__(self):
        self.llm_client = None
        try:
            if settings.openai_api_key:
                from openai import OpenAI
                self.llm_client = OpenAI(api_key=settings.openai_api_key)
                logger.info("QueryAnalyzer initialized with LLM support")
            else:
                logger.info("QueryAnalyzer initialized (rule-based only)")
        except Exception as e:
            logger.warning(f"LLM not available: {e}")

    def analyze(
        self,
        query: str,
        party_filter: Optional[str] = None,
        platform: str = "twitter",
    ) -> AnalyzedQuery:
        """
        Analyze query in one pass: intent + topic + party + keywords.

        Args:
            query: User's Turkish query
            party_filter: Party filter from UI
            platform: Platform (twitter, instagram, both)

        Returns:
            AnalyzedQuery with all analysis results
        """
        query_lower = query.lower()

        # --- Topic Detection ---
        detected_topic = self._detect_topic(query_lower)

        # --- Criticism Detection ---
        is_criticism = self._detect_criticism(query_lower)

        # --- Party Detection ---
        source_party = party_filter
        target_party = self._detect_target_party(query_lower, is_criticism, party_filter)

        # If source party selected and criticism query, infer target from opposites
        if is_criticism and source_party and not target_party:
            target_party = OPPOSITE_PARTIES.get(source_party)

        # --- Username Detection ---
        username = None
        username_match = re.search(r"@(\w+)", query)
        if username_match:
            username = username_match.group(1)

        # --- Date Detection ---
        start_date, end_date = self._detect_dates(query)

        # --- Intent Classification ---
        intent = self._classify_intent(
            query_lower, is_criticism, username, start_date, detected_topic
        )

        # --- Keyword Extraction ---
        keywords = self._extract_search_keywords(query, detected_topic)

        # Expand for BM25 matching
        expanded = expand_keywords(keywords[:8]) if keywords else []
        # Limit expansion
        expanded = list(set(expanded))[:25]

        # --- Build Enhanced Search Query ---
        search_query = self._build_search_query(
            query, keywords, detected_topic, target_party
        )

        confidence = 0.75
        if detected_topic:
            confidence += 0.1
        if is_criticism and target_party:
            confidence += 0.1

        result = AnalyzedQuery(
            original_query=query,
            intent=intent,
            is_criticism=is_criticism,
            confidence=confidence,
            source_party=source_party,
            target_party=target_party,
            detected_topic=detected_topic,
            keywords=keywords,
            expanded_keywords=expanded,
            search_query=search_query,
            username=username,
            start_date=start_date,
            end_date=end_date,
        )

        logger.info(
            f"Query analyzed: intent={intent}, topic={detected_topic}, "
            f"criticism={is_criticism}, target={target_party}, "
            f"keywords={keywords[:5]}"
        )

        return result

    def _detect_topic(self, query_lower: str) -> Optional[str]:
        """Detect topic from keywords."""
        best_topic = None
        best_count = 0
        for topic, keywords in TOPIC_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in query_lower)
            if count > best_count:
                best_count = count
                best_topic = topic
        return best_topic if best_count > 0 else None

    def _detect_criticism(self, query_lower: str) -> bool:
        """Check if query explicitly asks for criticism."""
        return any(kw in query_lower for kw in CRITICISM_KEYWORDS[:15])

    def _detect_target_party(
        self,
        query_lower: str,
        is_criticism: bool,
        party_filter: Optional[str],
    ) -> Optional[str]:
        """Detect which party is being criticized/discussed."""
        if not is_criticism:
            return None

        # Government-related terms → AK Parti
        if any(t in query_lower for t in GOVERNMENT_TERMS):
            return "AK Parti"

        # Opposition terms → CHP
        if any(t in query_lower for t in OPPOSITION_TERMS):
            return "CHP"

        # Check specific party mentions
        for party, patterns in PARTY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    # If this is the source party, skip (they're the ones tweeting)
                    if party == party_filter:
                        continue
                    return party

        return None

    def _detect_dates(self, query: str) -> tuple:
        """Extract date range from query."""
        date_matches = re.findall(r'(\d{2})[-/](\d{2})[-/](\d{4})', query)
        dates = []
        for d, m, y in date_matches:
            dates.append(f"{y}-{m}-{d}")
        dates.sort()

        start_date = dates[0] if len(dates) >= 1 else None
        end_date = dates[1] if len(dates) >= 2 else None
        return start_date, end_date

    def _classify_intent(
        self,
        query_lower: str,
        is_criticism: bool,
        username: Optional[str],
        start_date: Optional[str],
        detected_topic: Optional[str],
    ) -> str:
        """Classify query intent."""
        if username:
            if "konu" in query_lower or "analiz" in query_lower:
                return "analyze_topics"
            return "search_user"

        if start_date:
            return "search_date"

        if is_criticism:
            return "search_criticism"

        if any(kw in query_lower for kw in ["konu", "analiz", "trend", "eğilim"]):
            return "analyze_topics"

        if "rt" in query_lower or "retweet" in query_lower:
            return "search_retweets"

        return "search_topic"

    def _extract_search_keywords(
        self,
        query: str,
        detected_topic: Optional[str],
    ) -> List[str]:
        """Extract meaningful search keywords from query."""
        # Start with NLP-extracted keywords
        keywords = extract_keywords(query, max_keywords=10)

        # Remove meta-words that don't help search
        meta_words = {
            "tweetler", "tweet", "tweetleri", "paylaşım", "paylaşımlar",
            "içerik", "içerikler", "hakkında", "ilgili", "bilgi",
            "nasıl", "neden", "nedir", "kim", "göster", "listele",
            "bul", "ara", "getir", "var", "yok", "olan",
            "postlar", "post", "postları",
        }
        keywords = [kw for kw in keywords if kw.lower() not in meta_words and len(kw) > 2]

        # Add topic keywords if detected
        if detected_topic:
            topic_kws = TOPIC_KEYWORDS.get(detected_topic, [])[:5]
            for kw in topic_kws:
                if kw not in keywords:
                    keywords.append(kw)

        return keywords[:12]

    def _build_search_query(
        self,
        original_query: str,
        keywords: List[str],
        detected_topic: Optional[str],
        target_party: Optional[str],
    ) -> str:
        """Build an enhanced search query for semantic retrieval."""
        parts = [original_query]

        # Add topic context
        if detected_topic:
            topic_kws = TOPIC_KEYWORDS.get(detected_topic, [])[:3]
            parts.extend(topic_kws)

        # Add target party context for criticism
        if target_party:
            parts.append(target_party)
            if target_party in ["AK Parti", "AKP"]:
                parts.extend(["hükümet", "iktidar"])
            elif target_party == "CHP":
                parts.extend(["muhalefet", "belediye"])

        return " ".join(parts)


# Singleton
_analyzer_instance = None


def get_query_analyzer() -> QueryAnalyzer:
    """Get or create QueryAnalyzer singleton."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = QueryAnalyzer()
    return _analyzer_instance
