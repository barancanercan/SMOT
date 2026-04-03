#!/usr/bin/env python3
"""
Classifier Agent - Content Classification for A-RAG

Provides LLM-based content classification:
- Sentiment analysis (positive/negative/neutral)
- Topic classification
- Criticism detection with target identification

Tools:
- classify_sentiment: Determine content sentiment
- classify_topic: Identify content topics
- classify_criticism: Detect criticism and targets
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import json
import re

from app.services.agents.base import BaseAgent, tool
from app.services.analysis.analyzer import TweetAnalyzer
from app.utils.logger import get_logger

logger = get_logger("ClassifierAgent")


@dataclass
class ClassificationConfig:
    """Configuration for content classification."""
    batch_size: int = 50  # Process in batches
    min_confidence: float = 0.5
    use_llm: bool = True


class ClassifierAgent(BaseAgent):
    """
    Content Classification Agent for A-RAG.

    Uses GPT-4o to classify content by:
    - Sentiment (olumlu/olumsuz/nötr)
    - Topic (ekonomi, belediye, sağlık, etc.)
    - Criticism target (hükümet, CHP, etc.)

    Tools:
    - classify_sentiment: Sentiment analysis
    - classify_topic: Topic extraction
    - classify_criticism: Criticism detection
    """

    def __init__(self, config: ClassificationConfig = None):
        """Initialize classifier agent."""
        super().__init__("ClassifierAgent")
        self.config = config or ClassificationConfig()

        try:
            self.analyzer = TweetAnalyzer()
            self.llm_available = True
            logger.info("ClassifierAgent initialized with LLM support")
        except Exception as e:
            self.analyzer = None
            self.llm_available = False
            logger.warning(f"LLM not available: {e}")

    def execute(
        self,
        query: str,
        contents: List[Dict],
        context: Any = None
    ) -> Dict[str, Any]:
        """
        Execute content classification.

        Args:
            query: Original user query
            contents: List of content items to classify
            context: Session context

        Returns:
            Dict with classified contents and summary
        """
        if not contents:
            return {"contents": [], "summary": {}}

        if not self.llm_available:
            logger.warning("LLM not available, skipping classification")
            return {"contents": contents, "summary": {}}

        # Detect classification type from query
        query_lower = query.lower()
        is_criticism = any(kw in query_lower for kw in [
            'eleştir', 'elestir', 'kritik', 'karşı', 'karsi'
        ])
        wants_topics = any(kw in query_lower for kw in [
            'konu', 'tema', 'analiz', 'ne hakkında', 'ne hakkinda'
        ])
        wants_sentiment = any(kw in query_lower for kw in [
            'duygu', 'olumlu', 'olumsuz', 'pozitif', 'negatif'
        ])

        # Build classification prompt
        if is_criticism:
            result = self.call_tool("classify_criticism", contents=contents, query=query)
        elif wants_topics:
            result = self.call_tool("classify_topic", contents=contents)
        elif wants_sentiment:
            result = self.call_tool("classify_sentiment", contents=contents)
        else:
            # Default: classify by relevance to query
            result = self._classify_by_relevance(contents, query)

        return result

    @tool(name="classify_sentiment", description="Analyze sentiment of content (positive/negative/neutral)")
    def classify_sentiment(self, contents: List[Dict]) -> Dict[str, Any]:
        """
        Classify content by sentiment.

        Args:
            contents: List of content items

        Returns:
            Dict with classified contents and sentiment summary
        """
        if not self.llm_available or not contents:
            return {"contents": contents, "summary": {"sentiment": "notr"}}

        # Build prompt
        content_text = self._format_contents_for_prompt(contents[:50])
        prompt = f"""Sen Türkçe duygu analizi uzmanısın.

Aşağıdaki içeriklerin duygu durumunu analiz et.

İÇERİKLER:
{content_text}

Her içerik için duygu durumunu belirle (olumlu/olumsuz/notr).

ÇIKTI (JSON):
{{
  "classifications": [
    {{"index": 0, "sentiment": "olumlu|olumsuz|notr", "confidence": 0.0-1.0}},
    ...
  ],
  "overall_sentiment": "olumlu|olumsuz|notr|karisik",
  "summary": "Kısa duygu özeti"
}}

JSON:"""

        try:
            response = self.analyzer._call_llm(prompt)
            data = self._parse_json_response(response)

            # Apply classifications to contents
            classifications = data.get("classifications", [])
            for cls in classifications:
                idx = cls.get("index", -1)
                if 0 <= idx < len(contents):
                    contents[idx]["sentiment"] = cls.get("sentiment", "notr")
                    contents[idx]["sentiment_confidence"] = cls.get("confidence", 0.5)

            return {
                "contents": contents,
                "summary": {
                    "sentiment": data.get("overall_sentiment", "notr"),
                    "description": data.get("summary", "")
                }
            }

        except Exception as e:
            logger.error(f"Sentiment classification failed: {e}")
            return {"contents": contents, "summary": {"sentiment": "notr"}}

    @tool(name="classify_topic", description="Identify topics and themes in content")
    def classify_topic(self, contents: List[Dict]) -> Dict[str, Any]:
        """
        Classify content by topic.

        Args:
            contents: List of content items

        Returns:
            Dict with classified contents and topic summary
        """
        if not self.llm_available or not contents:
            return {"contents": contents, "summary": {"topics": []}}

        content_text = self._format_contents_for_prompt(contents[:50])
        prompt = f"""Sen Türk siyasi içerik analisti olarak konuları sınıflandırıyorsun.

İÇERİKLER:
{content_text}

Her içeriğin ana konusunu belirle. Olası konular:
- ekonomi (enflasyon, zam, maaş, işsizlik)
- belediye (yerel hizmetler, altyapı, park)
- sağlık (hastane, doktor, ilaç)
- eğitim (okul, öğretmen, üniversite)
- ulaşım (metro, otobüs, trafik)
- güvenlik (polis, asker, terör)
- dış politika (AB, ABD, Suriye)
- siyaset (seçim, parti, hükümet)
- sosyal (kadın, aile, gençlik)
- diğer

ÇIKTI (JSON):
{{
  "classifications": [
    {{"index": 0, "topic": "ekonomi", "subtopics": ["enflasyon"], "confidence": 0.8}},
    ...
  ],
  "main_topics": ["ekonomi", "belediye", ...],
  "topic_distribution": {{"ekonomi": 10, "belediye": 5, ...}}
}}

JSON:"""

        try:
            response = self.analyzer._call_llm(prompt)
            data = self._parse_json_response(response)

            # Apply classifications
            classifications = data.get("classifications", [])
            for cls in classifications:
                idx = cls.get("index", -1)
                if 0 <= idx < len(contents):
                    contents[idx]["topic"] = cls.get("topic", "diğer")
                    contents[idx]["subtopics"] = cls.get("subtopics", [])

            return {
                "contents": contents,
                "summary": {
                    "topics": data.get("main_topics", []),
                    "distribution": data.get("topic_distribution", {})
                }
            }

        except Exception as e:
            logger.error(f"Topic classification failed: {e}")
            return {"contents": contents, "summary": {"topics": []}}

    @tool(name="classify_criticism", description="Detect criticism and identify targets")
    def classify_criticism(
        self,
        contents: List[Dict],
        query: str = ""
    ) -> Dict[str, Any]:
        """
        Classify content for criticism with target identification.

        Args:
            contents: List of content items
            query: Original query for context

        Returns:
            Dict with classified contents (criticism matches) and summary
        """
        if not self.llm_available or not contents:
            return {"contents": contents, "summary": {"total_criticism": 0}}

        # Detect target from query
        target = self._detect_target(query)

        content_text = self._format_contents_for_prompt(contents[:50])
        prompt = f"""Sen Türk siyasi içerik analistisin. Eleştiri içeren içerikleri tespit edeceksin.

KULLANICI SORUSU: {query}
HEDEFLENEBİLECEK: {target or 'Belirtilmemiş'}

İÇERİKLER:
{content_text}

Her içeriği analiz et:
1. Eleştiri içeriyor mu?
2. Kimi/neyi eleştiriyor?
3. Eleştiri konusu nedir?

ÇIKTI (JSON):
{{
  "matches": [
    {{
      "index": 0,
      "is_criticism": true,
      "target": "hükümet|chp|mhp|belediye|...",
      "topic": "ekonomi yönetimi",
      "explanation": "Kısa açıklama",
      "confidence": 0.85
    }},
    ...
  ],
  "total_criticism": 10,
  "main_targets": ["hükümet", "belediye"],
  "main_topics": ["ekonomi", "ulaşım"]
}}

JSON:"""

        try:
            response = self.analyzer._call_llm(prompt)
            data = self._parse_json_response(response)

            # Filter to only criticism matches
            matches = data.get("matches", [])
            criticism_contents = []

            for match in matches:
                idx = match.get("index", -1)
                if 0 <= idx < len(contents) and match.get("is_criticism", False):
                    content = contents[idx].copy()
                    content["_classification"] = {
                        "is_criticism": True,
                        "target": match.get("target", ""),
                        "topic": match.get("topic", ""),
                        "explanation": match.get("explanation", ""),
                        "confidence": match.get("confidence", 0.5)
                    }
                    content["criticism_topic"] = match.get("topic", "")
                    content["criticism_explanation"] = match.get("explanation", "")
                    criticism_contents.append(content)

            return {
                "contents": criticism_contents,
                "summary": {
                    "total_found": len(criticism_contents),
                    "total_analyzed": len(contents),
                    "main_targets": data.get("main_targets", []),
                    "main_topics": data.get("main_topics", [])
                }
            }

        except Exception as e:
            logger.error(f"Criticism classification failed: {e}")
            return {"contents": contents, "summary": {"total_criticism": 0}}

    # ==========================================================================
    # Private Helper Methods
    # ==========================================================================

    def _classify_by_relevance(
        self,
        contents: List[Dict],
        query: str
    ) -> Dict[str, Any]:
        """Classify contents by relevance to query."""
        if not self.llm_available:
            return {"contents": contents, "summary": {}}

        content_text = self._format_contents_for_prompt(contents[:50])
        prompt = f"""Kullanıcı şu soruyu sordu: "{query}"

Aşağıdaki içeriklerden hangilerinin bu soruyla en alakalı olduğunu belirle.

İÇERİKLER:
{content_text}

ÇIKTI (JSON):
{{
  "relevant_indices": [0, 2, 5, ...],
  "main_topics": ["konu1", "konu2"],
  "summary": "Kısa özet"
}}

JSON:"""

        try:
            response = self.analyzer._call_llm(prompt)
            data = self._parse_json_response(response)

            relevant_indices = set(data.get("relevant_indices", range(len(contents))))

            for i, content in enumerate(contents):
                content["relevant"] = i in relevant_indices

            return {
                "contents": contents,
                "summary": {
                    "topics": data.get("main_topics", []),
                    "description": data.get("summary", "")
                }
            }

        except Exception as e:
            logger.error(f"Relevance classification failed: {e}")
            return {"contents": contents, "summary": {}}

    def _format_contents_for_prompt(self, contents: List[Dict], max_length: int = 300) -> str:
        """Format contents for LLM prompt."""
        lines = []
        for i, c in enumerate(contents):
            text = c.get("tweet_text", c.get("caption", ""))
            if len(text) > max_length:
                text = text[:max_length] + "..."
            text = text.replace("\n", " ").strip()
            username = c.get("username", "")
            party = c.get("party", "")
            party_str = f" [{party}]" if party else ""
            lines.append(f"[{i}] @{username}{party_str}: {text}")
        return "\n\n".join(lines)

    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from LLM response."""
        response = response.strip()
        if response.startswith("```"):
            response = re.sub(r'^```\w*\n?', '', response)
            response = re.sub(r'\n?```$', '', response)
        return json.loads(response)

    def _detect_target(self, query: str) -> Optional[str]:
        """Detect criticism target from query."""
        query_lower = query.lower()

        targets = [
            (["hükümet", "hukumet", "iktidar", "akp", "ak parti", "erdoğan", "erdogan"], "hükümet"),
            (["chp", "muhalefet", "kılıçdaroğlu", "imamoglu", "imamoğlu"], "CHP"),
            (["mhp", "bahçeli", "bahceli"], "MHP"),
            (["belediye", "başkan", "baskan"], "belediye"),
        ]

        for keywords, target in targets:
            if any(kw in query_lower for kw in keywords):
                return target

        return None
