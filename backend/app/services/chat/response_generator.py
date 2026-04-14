#!/usr/bin/env python3
"""
Response Generator v7 - Clean output with citations and confidence scoring.

Generates user-friendly Turkish responses from retrieved social media content.
Uses LLM for intelligent summarization with inline citations.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any

from app.services.analysis.analyzer import TweetAnalyzer
from app.services.analysis.chat_prompts import get_chat_prompt
from app.utils.logger import get_logger

logger = get_logger("ResponseGenerator")


@dataclass
class ChatResponse:
    """Generated chat response."""
    answer: str
    summary: dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    raw_response: str = ""


# Platform-specific content names in Turkish
CONTENT_NAMES = {
    "twitter": {"singular": "tweet", "plural": "tweetler", "accusative": "tweeti"},
    "instagram": {"singular": "post", "plural": "postlar", "accusative": "postu"},
    "both": {"singular": "içerik", "plural": "içerikler", "accusative": "içeriği"},
}


def _build_url_map(tweets: list[dict]) -> dict[int, str]:
    """Build a mapping of tweet index (1-based) to URL."""
    url_map: dict[int, str] = {}
    for i, t in enumerate(tweets, 1):
        url = t.get("tweet_url") or t.get("post_url")
        if url:
            url_map[i] = url
    return url_map


def _add_citation_links(text: str, url_map: dict[int, str]) -> str:
    """Replace [N] citation markers with clickable markdown links when URL available."""
    if not url_map:
        return text

    def replace_citation(match: re.Match) -> str:
        num = int(match.group(1))
        url = url_map.get(num)
        if url:
            return f"[[{num}]]({url})"
        return match.group(0)

    # Replace [N] not already followed by ( to avoid double-linking
    return re.sub(r"\[(\d+)\](?!\()", replace_citation, text)


def _get_content_name(platform: str, form: str = "plural") -> str:
    """Get platform-aware content name."""
    names = CONTENT_NAMES.get(platform, CONTENT_NAMES["twitter"])
    return names.get(form, names["plural"])


def _detect_platform_from_tweets(tweets: list[dict]) -> str:
    """Detect platform from tweet data."""
    platforms = {t.get("platform", "twitter") for t in tweets}
    if "instagram" in platforms and "twitter" in platforms:
        return "both"
    elif "instagram" in platforms:
        return "instagram"
    return "twitter"


def _extract_stats(tweets: list[dict]) -> dict[str, Any]:
    """Extract statistics from tweet list."""
    if not tweets:
        return {"total_found": 0, "top_topics": [], "sentiment": "notr",
                "most_active_users": [], "date_range": None}

    # Users
    user_counts: dict[str, int] = {}
    for t in tweets:
        u = t.get("username", "")
        user_counts[u] = user_counts.get(u, 0) + 1
    top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:3]

    # Date range
    dates = []
    for t in tweets:
        date = t.get("tweet_date", t.get("post_date", t.get("date", "")))
        if date and len(str(date)) >= 10:
            dates.append(str(date)[:10])
    dates.sort()
    date_range = f"{dates[0]} - {dates[-1]}" if dates else None

    # Topics from common words
    all_text = " ".join(t.get("tweet_text", t.get("caption", "")) for t in tweets)
    words = re.findall(r'\b\w+\b', all_text.lower())
    stopwords = {
        'bir', 've', 'ile', 'icin', 'için', 'bu', 'su', 'şu', 'o', 'da', 'de',
        'mi', 'mu', 'ne', 'ya', 'ki', 'ama', 'olan', 'daha', 'en',
        'rt', 'https', 'http', 'www', 'com', 'tr', 'co', 'ben', 'sen', 'biz',
    }
    word_counts: dict[str, int] = {}
    for w in words:
        if len(w) > 3 and w not in stopwords:
            word_counts[w] = word_counts.get(w, 0) + 1
    top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "total_found": len(tweets),
        "top_topics": [w[0] for w in top_words],
        "sentiment": "notr",
        "most_active_users": [u[0] for u in top_users],
        "date_range": date_range,
    }


def compute_confidence(retrieval_scores: list[float], num_results: int) -> float:
    """
    Compute confidence based on retrieval quality.

    Args:
        retrieval_scores: Scores from retrieval results
        num_results: Number of results found

    Returns:
        Confidence score 0.0-1.0
    """
    if num_results == 0:
        return 0.0

    # Average of top scores
    top_scores = retrieval_scores[:min(5, len(retrieval_scores))]
    avg_score = sum(top_scores) / len(top_scores) if top_scores else 0.0

    # Coverage factor
    coverage = min(1.0, num_results / 5)

    return round(min(1.0, avg_score * 0.6 + coverage * 0.4), 2)


class ResponseGenerator:
    """Generate AI-powered responses from retrieved social media content."""

    MIN_TWEETS_FOR_SUMMARY = 3

    def __init__(self):
        try:
            self.analyzer = TweetAnalyzer()
            self.llm_available = True
            logger.info("ResponseGenerator initialized with LLM support")
        except Exception as e:
            logger.warning(f"LLM not available: {e}")
            self.analyzer = None
            self.llm_available = False

    def generate(
        self,
        query: str,
        tweets: list[dict],
        intent_type: str = "search_topic",
        username: str | None = None,
        platform: str = "twitter",
        is_criticism: bool = False,
    ) -> ChatResponse:
        """
        Generate response from found content.

        Args:
            query: Original query
            tweets: Retrieved content
            intent_type: Query intent
            username: Optional username filter
            platform: Platform
            is_criticism: Whether this is a criticism search

        Returns:
            ChatResponse with answer, summary, and confidence
        """
        if not tweets:
            content_name = _get_content_name(platform, "accusative")
            if is_criticism:
                return ChatResponse(
                    answer=f"Belirtilen kriterlere uygun eleştiri {content_name} bulunamadı.",
                    summary={"total_found": 0},
                    confidence_score=0.0,
                )
            return ChatResponse(
                answer=f"Aramanıza uygun {content_name} bulunamadı.",
                summary={"total_found": 0},
                confidence_score=0.0,
            )

        # Detect platform from actual content
        detected_platform = _detect_platform_from_tweets(tweets)
        if detected_platform != "twitter":
            platform = detected_platform

        stats = _extract_stats(tweets)

        # Few tweets - simple response
        if len(tweets) < self.MIN_TWEETS_FOR_SUMMARY:
            return self._generate_simple(query, tweets, intent_type, platform, stats)

        # LLM summary
        if self.llm_available and self.analyzer:
            try:
                return self._generate_with_llm(query, tweets, intent_type, username, platform, stats)
            except Exception as e:
                logger.warning(f"LLM generation failed: {e}")

        return self._generate_simple(query, tweets, intent_type, platform, stats)

    def _generate_with_llm(
        self,
        query: str,
        tweets: list[dict],
        intent_type: str,
        username: str | None,
        platform: str,
        stats: dict,
    ) -> ChatResponse:
        """Generate response using LLM with citations."""
        query_lower = query.lower()
        wants_detailed = any(kw in query_lower for kw in [
            'detaylı', 'detayli', 'açıkla', 'acikla', 'analiz et',
            'incele', 'kapsamlı', 'kapsamli'
        ])

        # Choose prompt
        if intent_type == "analyze_topics" and username:
            prompt = get_chat_prompt(
                'topic_analysis', username=username,
                tweets=tweets, tweet_count=len(tweets), platform=platform
            )
        elif wants_detailed and len(tweets) >= 3:
            prompt = get_chat_prompt(
                'detailed', query=query,
                tweets=tweets, tweet_count=len(tweets), platform=platform
            )
        else:
            prompt = get_chat_prompt(
                'response', query=query,
                tweets=tweets, tweet_count=len(tweets), platform=platform
            )

        # Build URL map before calling LLM (index matches format_tweets_for_chat order)
        url_map = _build_url_map(tweets)

        # Call LLM
        response = self.analyzer._call_llm(prompt)
        logger.debug(f"LLM response length: {len(response)}")

        # Parse JSON response
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r'^```\w*\n?', '', cleaned)
                cleaned = re.sub(r'\n?```$', '', cleaned)

            data = json.loads(cleaned)

            llm_summary = data.get('summary', stats)
            # Merge LLM summary with our stats
            for key in stats:
                if key not in llm_summary or not llm_summary[key]:
                    llm_summary[key] = stats[key]

            answer = _add_citation_links(data.get('answer', 'Analiz tamamlandı.'), url_map)
            return ChatResponse(
                answer=answer,
                summary=llm_summary,
                confidence_score=float(data.get('confidence_score', 0.75)),
                raw_response=response,
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            # If we got a non-JSON response, use it as the answer directly
            if len(response) > 50 and not response.strip().startswith('{'):
                return ChatResponse(
                    answer=_add_citation_links(response.strip(), url_map),
                    summary=stats,
                    confidence_score=0.6,
                )
            return self._generate_simple(query, tweets, intent_type, platform, stats)

    def _generate_simple(
        self,
        query: str,
        tweets: list[dict],
        intent_type: str,
        platform: str,
        stats: dict,
    ) -> ChatResponse:
        """Generate rule-based response without LLM."""
        count = len(tweets)
        content_name = _get_content_name(platform)

        lines = []
        lines.append("## Sonuçlar")
        lines.append("")
        lines.append(f"**{count} {content_name}** bulundu.")
        lines.append("")

        # Engagement stats
        total_likes = sum(t.get("likes", 0) for t in tweets)
        total_retweets = sum(t.get("retweets", 0) for t in tweets)
        if total_likes > 0 or total_retweets > 0:
            lines.append(f"- **Toplam etkileşim:** {total_likes:,} beğeni, {total_retweets:,} paylaşım")

        if stats.get("most_active_users"):
            users = ", ".join(f"@{u}" for u in stats["most_active_users"][:3])
            lines.append(f"- **En aktif:** {users}")

        if stats.get("date_range"):
            lines.append(f"- **Tarih:** {stats['date_range']}")

        # Top content
        if tweets:
            lines.append("")
            lines.append("## Öne Çıkan İçerikler")
            lines.append("")
            for i, t in enumerate(tweets[:3], 1):
                text = t.get("tweet_text", t.get("caption", ""))[:150]
                text = text.replace('\n', ' ').strip()
                username = t.get("username", "")
                url = t.get("tweet_url") or t.get("post_url")
                if url:
                    lines.append(f"> [@{username}: \"{text}\"]({url}) [{i}]")
                else:
                    lines.append(f"> @{username}: \"{text}\" [{i}]")
                lines.append("")

        return ChatResponse(
            answer="\n".join(lines),
            summary=stats,
            confidence_score=0.5,
        )
