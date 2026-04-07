#!/usr/bin/env python3
"""
Intent Parser v2 - Parse Turkish natural language queries into structured filters

Uses:
1. LLM for complex intent detection
2. Turkish NLP for keyword expansion
3. Rule-based fallback with improved patterns
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.core.constants import normalize_party_name
from app.services.analysis.analyzer import TweetAnalyzer
from app.services.analysis.chat_prompts import get_chat_prompt
from app.services.chat.turkish_nlp import (
    expand_keywords,
    extract_keywords,
    text_contains_any,
)
from app.utils.logger import get_logger

logger = get_logger("IntentParser")


@dataclass
class ParsedIntent:
    """Parsed intent from user query"""
    intent_type: str  # search_topic, search_user, search_date, analyze_topics, search_retweets, search_criticism
    filters: dict[str, Any] = field(default_factory=dict)
    semantic_query: str = ""
    confidence: float = 0.0
    raw_response: str = ""


class IntentParser:
    """
    Parse Turkish natural language queries into structured filters.
    Uses LLM for intent detection and filter extraction.
    """

    def __init__(self):
        """Initialize the intent parser with LLM analyzer"""
        try:
            self.analyzer = TweetAnalyzer()
            self.llm_available = True
            logger.info("IntentParser initialized with LLM support")
        except Exception as e:
            logger.warning(f"LLM not available, falling back to rule-based parsing: {e}")
            self.analyzer = None
            self.llm_available = False

    def parse(self, query: str) -> ParsedIntent:
        """
        Parse a Turkish natural language query into structured intent.

        Args:
            query: Turkish language query string

        Returns:
            ParsedIntent object with intent type, filters, and semantic query
        """
        if not query or len(query.strip()) < 3:
            return ParsedIntent(
                intent_type="search_topic",
                filters={"keywords": []},
                semantic_query="",
                confidence=0.0
            )

        # Try LLM parsing first
        if self.llm_available and self.analyzer:
            try:
                return self._parse_with_llm(query)
            except Exception as e:
                logger.warning(f"LLM parsing failed, falling back to rules: {e}")

        # Fallback to rule-based parsing
        return self._parse_with_rules(query)

    def _parse_with_llm(self, query: str) -> ParsedIntent:
        """
        Parse query using LLM for better Turkish language understanding.

        Args:
            query: User query string

        Returns:
            ParsedIntent from LLM analysis
        """
        prompt = get_chat_prompt('intent', query=query)

        # Call LLM
        response = self.analyzer._call_llm(prompt)
        logger.debug(f"LLM intent response: {response[:500]}")

        # Parse JSON response
        try:
            # Clean potential markdown code blocks
            response = response.strip()
            if response.startswith("```"):
                response = re.sub(r'^```\w*\n?', '', response)
                response = re.sub(r'\n?```$', '', response)

            data = json.loads(response)

            # Extract filters and normalize
            filters = data.get('filters', {})

            # Normalize party name if present
            if filters.get('party'):
                filters['party'] = normalize_party_name(filters['party'])

            # Validate dates
            if filters.get('start_date'):
                filters['start_date'] = self._validate_date(filters['start_date'])
            if filters.get('end_date'):
                filters['end_date'] = self._validate_date(filters['end_date'])

            return ParsedIntent(
                intent_type=data.get('intent_type', 'search_topic'),
                filters=filters,
                semantic_query=data.get('semantic_query', query),
                confidence=float(data.get('confidence', 0.7)),
                raw_response=response
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in LLM response: {e}")
            raise

    def _parse_with_rules(self, query: str) -> ParsedIntent:
        """
        Rule-based parsing with Turkish NLP enhancements.

        Uses:
        - Turkish stemming for better matching
        - Synonym expansion
        - Improved keyword extraction

        Args:
            query: User query string

        Returns:
            ParsedIntent from rule-based analysis
        """
        query_lower = query.lower()
        intent_type = "search_topic"
        filters: dict[str, Any] = {
            "username": None,
            "party": None,
            "start_date": None,
            "end_date": None,
            "keywords": [],
            "is_criticism": None,
            "retweet_from": None
        }

        # Criticism-related keywords with synonyms
        criticism_keywords = [
            'elestir', 'eleştir', 'kritik', 'tenkit',
            'muhalefet', 'karsi', 'karşı', 'itiraz',
            'yanlis', 'yanlış', 'basarisiz', 'başarısız', 'yetersiz', 'kifayetsiz',
            'kotu', 'kötü', 'rezalet', 'skandal', 'fiyasko',
            'protesto', 'eylem', 'gösteri',
        ]

        # Government/Target keywords
        government_keywords = [
            'hukumet', 'hükümet', 'iktidar', 'akp', 'ak parti', 'akparti',
            'erdogan', 'erdoğan', 'saray', 'beştepe', 'cumhurbaşkan'
        ]

        # Economic keywords
        economic_keywords = [
            'ekonomi', 'ekonomik', 'enflasyon', 'zam', 'pahalı', 'pahali',
            'dolar', 'kur', 'issizlik', 'işsizlik', 'kriz', 'maaş', 'asgari'
        ]

        # Check for criticism intent using text_contains_any (NLP-aware)
        has_criticism = text_contains_any(query, criticism_keywords[:8])
        has_target = text_contains_any(query, government_keywords) or text_contains_any(query, ['chp', 'muhalefet'])

        # Detect intent type
        if "konulari" in query_lower or "konusu" in query_lower or "hakkinda" in query_lower:
            intent_type = "analyze_topics"
        elif has_criticism and has_target:
            intent_type = "search_criticism"
            filters["is_criticism"] = True
        elif has_criticism:
            intent_type = "search_criticism"
            filters["is_criticism"] = True
        elif "rt" in query_lower or "retweet" in query_lower:
            intent_type = "search_retweets"
        elif "tarih" in query_lower or re.search(r'\d{2}[-/]\d{2}[-/]\d{4}', query):
            intent_type = "search_date"

        # Extract username mentions
        username_match = re.search(r"@(\w+)", query)
        if username_match:
            username = username_match.group(1)
            if intent_type == "search_retweets":
                filters["retweet_from"] = username
            else:
                filters["username"] = username
                intent_type = "search_user"

        # Extract dates (Turkish format: DD-MM-YYYY)
        date_matches = re.findall(r'(\d{2})[-/](\d{2})[-/](\d{4})', query)
        if date_matches:
            dates = []
            for d, m, y in date_matches:
                dates.append(f"{y}-{m}-{d}")
            dates.sort()
            if len(dates) >= 1:
                filters["start_date"] = dates[0]
            if len(dates) >= 2:
                filters["end_date"] = dates[1]

        # Extract party names with normalization
        party_patterns = [
            (r'\bchp\b', 'CHP'),
            (r'\bchp\'li', 'CHP'),
            (r'\bchpliler', 'CHP'),
            (r'\bak\s*parti\b', 'AK Parti'),
            (r'\bakp\b', 'AK Parti'),
            (r'\bakp\'li', 'AK Parti'),
            (r'\bakpliler', 'AK Parti'),
            (r'\bmhp\b', 'MHP'),
            (r'\bmhp\'li', 'MHP'),
            (r'\biyi\s*parti\b', 'IYI Parti'),
            (r'\biyip\b', 'IYI Parti'),
            (r'\bdem\s*parti\b', 'DEM Parti'),
            (r'\bhdp\b', 'DEM Parti'),
            (r'\bbbp\b', 'BBP'),
            (r'\byrp\b', 'YRP'),
            (r'\byeniden\s*refah\b', 'YRP'),
        ]
        for pattern, party in party_patterns:
            if re.search(pattern, query_lower):
                filters["party"] = party
                break

        # Extract keywords using Turkish NLP
        keywords = extract_keywords(query, max_keywords=15)

        # Add relevant topic keywords if detected
        if text_contains_any(query, economic_keywords):
            keywords.extend(['ekonomi', 'ekonomik'])
        if text_contains_any(query, ['eğitim', 'egitim', 'okul']):
            keywords.extend(['eğitim', 'egitim'])
        if text_contains_any(query, ['sağlık', 'saglik', 'hastane']):
            keywords.extend(['sağlık', 'saglik'])
        if text_contains_any(query, ['belediye', 'yerel']):
            keywords.extend(['belediye'])
        if text_contains_any(query, ['ulaşım', 'ulasim', 'metro', 'trafik']):
            keywords.extend(['ulaşım', 'ulasim', 'trafik'])

        # Remove duplicates and limit
        keywords = list(dict.fromkeys(keywords))[:12]
        filters["keywords"] = keywords

        # Build semantic query with expanded keywords
        if keywords:
            # Expand for better semantic matching
            expanded = expand_keywords(keywords[:5])  # Top 5 for expansion
            semantic_query = " ".join(expanded[:20])
        else:
            semantic_query = query

        logger.info(f"Rule-based parse: intent={intent_type}, keywords={keywords[:5]}...")

        return ParsedIntent(
            intent_type=intent_type,
            filters=filters,
            semantic_query=semantic_query,
            confidence=0.65,  # Higher confidence with NLP
            raw_response=""
        )

    def _validate_date(self, date_str: str) -> str | None:
        """
        Validate and normalize date string to YYYY-MM-DD format.

        Args:
            date_str: Date string to validate

        Returns:
            Normalized date string or None if invalid
        """
        if not date_str:
            return None

        # Try different formats
        formats = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y/%m/%d",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None


# ============================================================================
# CLI TEST
# ============================================================================

if __name__ == "__main__":
    parser = IntentParser()

    test_queries = [
        "Belediye hizmetleriyle atilmis tweetleri getir",
        "01-01-2024 tarihinden 31-03-2024 tarihine kadar atilmis tweetleri getir",
        "Atilla Celik'in attigi tweetlerin konulari neledir",
        "Cumhurbaskanina elestiri iceren tweetleri getir",
        "@chp kullanicini rt yapan tweetleri getir",
        "CHP parti uyelerinin tweetlerini goster",
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"QUERY: {query}")
        print(f"{'='*60}")

        intent = parser.parse(query)

        print(f"Intent Type: {intent.intent_type}")
        print(f"Filters: {json.dumps(intent.filters, indent=2, ensure_ascii=False)}")
        print(f"Semantic Query: {intent.semantic_query}")
        print(f"Confidence: {intent.confidence:.2f}")
