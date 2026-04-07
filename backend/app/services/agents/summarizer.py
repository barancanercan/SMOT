#!/usr/bin/env python3
"""
Summarizer Agent - Response Generation for A-RAG

Generates platform-aware responses from content analysis.
Uses proper terminology based on platform (tweet vs post vs content).

Tools:
- summarize: Generate summary from contents
- extract_topics: Extract main topics
- format_response: Platform-aware response formatting
"""

import json
import re
from dataclasses import dataclass
from typing import Any

from app.services.agents.base import BaseAgent, tool
from app.services.analysis.analyzer import TweetAnalyzer
from app.services.analysis.chat_prompts import get_chat_prompt
from app.utils.logger import get_logger

logger = get_logger("SummarizerAgent")


@dataclass
class SummaryConfig:
    """Configuration for summarization."""
    max_content_for_summary: int = 30
    include_examples: bool = True
    max_example_length: int = 200


class SummarizerAgent(BaseAgent):
    """
    Response Generation Agent for A-RAG.

    Generates user-friendly responses with:
    - Platform-aware terminology (tweet/post/content)
    - Markdown formatting
    - Topic summaries
    - Example quotes

    Tools:
    - summarize: Generate overall summary
    - extract_topics: Extract main topics
    - format_response: Format for specific platform
    """

    # Platform-specific content names
    CONTENT_NAMES = {
        "twitter": {"singular": "tweet", "plural": "tweetler"},
        "instagram": {"singular": "post", "plural": "postlar"},
        "both": {"singular": "içerik", "plural": "içerikler"},
    }

    def __init__(self, config: SummaryConfig = None):
        """Initialize summarizer agent."""
        super().__init__("SummarizerAgent")
        self.config = config or SummaryConfig()

        try:
            self.analyzer = TweetAnalyzer()
            self.llm_available = True
            logger.info("SummarizerAgent initialized with LLM support")
        except Exception as e:
            self.analyzer = None
            self.llm_available = False
            logger.warning(f"LLM not available: {e}")

    def execute(
        self,
        query: str,
        contents: list[dict],
        platform: str = "twitter",
        classification_summary: dict = None
    ) -> dict[str, Any]:
        """
        Generate response summary.

        Args:
            query: Original user query
            contents: List of content items
            platform: Platform (twitter/instagram/both)
            classification_summary: Optional summary from classifier

        Returns:
            Dict with answer and summary
        """
        if not contents:
            content_name = self._get_content_name(platform, plural=False)
            return {
                "answer": f"Aramanıza uygun {content_name} bulunamadı.",
                "summary": {"total_found": 0}
            }

        # Use LLM if available
        if self.llm_available and len(contents) >= 3:
            return self.call_tool(
                "summarize",
                query=query,
                contents=contents,
                platform=platform,
                classification_summary=classification_summary
            )

        # Fallback to simple summary
        return self.call_tool(
            "format_response",
            contents=contents,
            platform=platform,
            classification_summary=classification_summary
        )

    @tool(name="summarize", description="Generate AI summary from content list")
    def summarize(
        self,
        query: str,
        contents: list[dict],
        platform: str = "twitter",
        classification_summary: dict = None
    ) -> dict[str, Any]:
        """
        Generate LLM-powered summary.

        Args:
            query: User query
            contents: Content list
            platform: Platform
            classification_summary: Classification results

        Returns:
            Dict with answer and summary
        """
        if not self.llm_available:
            return self.format_response_tool(contents, platform, classification_summary)

        # Detect platform from contents if mixed
        detected_platform = self._detect_platform(contents, platform)

        # Get appropriate prompt
        try:
            prompt = get_chat_prompt(
                'response',
                query=query,
                tweets=contents[:self.config.max_content_for_summary],
                tweet_count=len(contents),
                platform=detected_platform
            )

            response = self.analyzer._call_llm(prompt)
            data = self._parse_json_response(response)

            # Merge with classification summary
            summary = data.get("summary", {})
            if classification_summary:
                summary["main_topics"] = classification_summary.get("main_topics", summary.get("top_topics", []))
                summary["total_analyzed"] = classification_summary.get("total_analyzed", len(contents))

            return {
                "answer": data.get("answer", self._generate_simple_answer(contents, detected_platform)),
                "summary": summary,
                "confidence_score": data.get("confidence_score", 0.7)
            }

        except Exception as e:
            logger.error(f"LLM summarization failed: {e}")
            return self.format_response_tool(contents, platform, classification_summary)

    @tool(name="extract_topics", description="Extract main topics from content")
    def extract_topics(self, contents: list[dict]) -> list[str]:
        """
        Extract main topics from contents.

        Args:
            contents: Content list

        Returns:
            List of topic strings
        """
        # Simple keyword extraction as fallback
        all_text = " ".join([
            c.get("tweet_text", c.get("caption", ""))
            for c in contents
        ])

        words = re.findall(r'\b\w+\b', all_text.lower())

        stopwords = {
            'bir', 've', 'ile', 'icin', 'bu', 'su', 'o', 'da', 'de',
            'mi', 'mu', 'ne', 'ya', 'ki', 'ama', 'olan', 'daha', 'en',
            'rt', 'https', 'http', 'www', 'com', 'tr', 'co'
        }

        word_counts = {}
        for w in words:
            if len(w) > 3 and w not in stopwords:
                word_counts[w] = word_counts.get(w, 0) + 1

        top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        return [w[0] for w in top_words]

    @tool(name="format_response", description="Format response with platform-aware terminology")
    def format_response_tool(
        self,
        contents: list[dict],
        platform: str = "twitter",
        classification_summary: dict = None
    ) -> dict[str, Any]:
        """
        Format a simple response without LLM.

        Args:
            contents: Content list
            platform: Platform
            classification_summary: Optional classification data

        Returns:
            Dict with formatted answer and summary
        """
        content_name = self._get_content_name(platform, plural=False)
        count = len(contents)

        # Build answer
        if classification_summary and classification_summary.get("total_found"):
            total_analyzed = classification_summary.get("total_analyzed", count)
            total_found = classification_summary.get("total_found", count)
            answer = f"**{total_analyzed}** {content_name} analiz edildi, **{total_found}** tanesi eşleşti."
        else:
            answer = f"Aramanıza uygun **{count}** {content_name} bulundu."

        # Extract basic stats
        topics = self.extract_topics(contents)
        most_active = self._get_most_active_users(contents)
        date_range = self._get_date_range(contents)

        summary = {
            "total_found": count,
            "top_topics": topics,
            "sentiment": "notr",
            "most_active_users": most_active,
            "date_range": date_range
        }

        if classification_summary:
            summary["main_topics"] = classification_summary.get("main_topics", topics)

        return {
            "answer": answer,
            "summary": summary,
            "confidence_score": 0.5
        }

    # ==========================================================================
    # Private Helper Methods
    # ==========================================================================

    def _get_content_name(self, platform: str, plural: bool = True) -> str:
        """Get platform-aware content name in Turkish."""
        names = self.CONTENT_NAMES.get(platform, self.CONTENT_NAMES["twitter"])
        return names["plural"] if plural else names["singular"]

    def _detect_platform(self, contents: list[dict], default: str) -> str:
        """Detect actual platform from contents."""
        platforms = {c.get("platform", "twitter") for c in contents}
        if "instagram" in platforms and "twitter" in platforms:
            return "both"
        elif "instagram" in platforms:
            return "instagram"
        elif "twitter" in platforms:
            return "twitter"
        return default

    def _generate_simple_answer(self, contents: list[dict], platform: str) -> str:
        """Generate a simple answer without LLM."""
        content_name = self._get_content_name(platform, plural=False)
        return f"Aramanıza uygun {len(contents)} {content_name} bulundu."

    def _get_most_active_users(self, contents: list[dict], limit: int = 3) -> list[str]:
        """Get most active users from content list."""
        user_counts = {}
        for c in contents:
            user = c.get("username", "")
            user_counts[user] = user_counts.get(user, 0) + 1
        sorted_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)
        return [u[0] for u in sorted_users[:limit]]

    def _get_date_range(self, contents: list[dict]) -> str | None:
        """Get date range from content list."""
        dates = []
        for c in contents:
            date = c.get("tweet_date", c.get("post_date", ""))
            if date and len(date) >= 10:
                dates.append(date[:10])

        if dates:
            dates.sort()
            return f"{dates[0]} - {dates[-1]}"
        return None

    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON from LLM response."""
        response = response.strip()
        if response.startswith("```"):
            response = re.sub(r'^```\w*\n?', '', response)
            response = re.sub(r'\n?```$', '', response)
        return json.loads(response)
