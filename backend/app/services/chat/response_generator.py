#!/usr/bin/env python3
"""
Response Generator - Generate AI summaries from found tweets
Uses LLM to create user-friendly responses from tweet search results
"""

import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from app.services.analysis.chat_prompts import get_chat_prompt
from app.services.analysis.analyzer import TweetAnalyzer
from app.utils.logger import get_logger

logger = get_logger("ResponseGenerator")


@dataclass
class ChatResponse:
    """Generated chat response"""
    answer: str
    summary: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    raw_response: str = ""


class ResponseGenerator:
    """
    Generate AI-powered summaries and responses from tweet search results.
    Uses platform-aware terminology (tweet vs post vs content).
    """

    # Minimum tweets for AI summary
    MIN_TWEETS_FOR_SUMMARY = 3

    # Platform-specific content names
    CONTENT_NAMES = {
        "twitter": {"singular": "tweet", "plural": "tweetler"},
        "instagram": {"singular": "post", "plural": "postlar"},
        "both": {"singular": "içerik", "plural": "içerikler"},
    }

    def __init__(self):
        """Initialize the response generator with LLM analyzer"""
        try:
            self.analyzer = TweetAnalyzer()
            self.llm_available = True
            logger.info("ResponseGenerator initialized with LLM support")
        except Exception as e:
            logger.warning(f"LLM not available: {e}")
            self.analyzer = None
            self.llm_available = False

    def _get_content_name(self, platform: str, plural: bool = True) -> str:
        """Get platform-aware content name in Turkish."""
        names = self.CONTENT_NAMES.get(platform, self.CONTENT_NAMES["twitter"])
        return names["plural"] if plural else names["singular"]

    def generate(
        self,
        query: str,
        tweets: List[Dict],
        intent_type: str = "search_topic",
        username: Optional[str] = None,
        platform: str = "twitter"
    ) -> ChatResponse:
        """
        Generate a response summarizing the found tweets.

        Args:
            query: Original user query
            tweets: List of found tweets
            intent_type: Type of intent (from IntentParser)
            username: Optional username for user-specific queries

        Returns:
            ChatResponse with answer and summary
        """
        tweet_count = len(tweets)

        # No tweets found - use platform-aware terminology
        content_name = self._get_content_name(platform, plural=False)
        if tweet_count == 0:
            return ChatResponse(
                answer=f"Aramaniza uygun {content_name} bulunamadi.",
                summary={
                    "total_found": 0,
                    "top_topics": [],
                    "sentiment": "notr",
                    "most_active_users": [],
                    "date_range": None
                },
                confidence_score=1.0
            )

        # Few tweets - no AI needed
        if tweet_count < self.MIN_TWEETS_FOR_SUMMARY:
            return self._generate_simple_response(query, tweets, intent_type)

        # Use AI for summarization
        if self.llm_available and self.analyzer:
            try:
                return self._generate_with_llm(query, tweets, intent_type, username, platform)
            except Exception as e:
                logger.warning(f"LLM generation failed, falling back to simple: {e}")

        # Fallback to simple response
        return self._generate_simple_response(query, tweets, intent_type)

    def _generate_with_llm(
        self,
        query: str,
        tweets: List[Dict],
        intent_type: str,
        username: Optional[str] = None,
        platform: str = "twitter"
    ) -> ChatResponse:
        """
        Generate response using LLM for intelligent summarization.

        Args:
            query: User query
            tweets: Tweet list
            intent_type: Intent type
            username: Optional username
            platform: Platform (twitter, instagram, both)

        Returns:
            ChatResponse from LLM
        """
        # Check if user wants detailed analysis
        query_lower = query.lower()
        wants_detailed = any(kw in query_lower for kw in [
            'detayli', 'detaylı', 'acikla', 'açıkla', 'analiz et',
            'incele', 'detayinda', 'detayında', 'kapsamli', 'kapsamlı'
        ])

        # Detect platform from tweets if not specified
        if platform == "twitter":
            platforms_in_tweets = set(t.get('platform', 'twitter') for t in tweets)
            if 'instagram' in platforms_in_tweets and 'twitter' in platforms_in_tweets:
                platform = 'both'
            elif 'instagram' in platforms_in_tweets:
                platform = 'instagram'

        logger.info(f"Generating response for platform: {platform}")

        # Choose prompt type based on intent and detail request
        if intent_type == "analyze_topics" and username:
            prompt = get_chat_prompt(
                'topic_analysis',
                username=username,
                tweets=tweets,
                tweet_count=len(tweets),
                platform=platform
            )
        elif wants_detailed and len(tweets) >= 3:
            # Use detailed analysis prompt
            prompt = get_chat_prompt(
                'detailed',
                query=query,
                tweets=tweets,
                tweet_count=len(tweets),
                platform=platform
            )
        else:
            prompt = get_chat_prompt(
                'response',
                query=query,
                tweets=tweets,
                tweet_count=len(tweets),
                platform=platform
            )

        # Call LLM
        response = self.analyzer._call_llm(prompt)
        logger.debug(f"LLM response: {response[:500]}")

        # Parse JSON response
        try:
            # Clean potential markdown code blocks
            response = response.strip()
            if response.startswith("```"):
                response = re.sub(r'^```\w*\n?', '', response)
                response = re.sub(r'\n?```$', '', response)

            data = json.loads(response)

            return ChatResponse(
                answer=data.get('answer', 'Analiz tamamlandi.'),
                summary=data.get('summary', {
                    "total_found": len(tweets),
                    "top_topics": [],
                    "sentiment": "notr",
                    "most_active_users": [],
                    "date_range": None
                }),
                confidence_score=float(data.get('confidence_score', 0.7)),
                raw_response=response
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in LLM response: {e}")
            # Return fallback
            return self._generate_simple_response(query, tweets, intent_type)

    def _generate_simple_response(
        self,
        query: str,
        tweets: List[Dict],
        intent_type: str
    ) -> ChatResponse:
        """
        Generate a simple rule-based response without LLM.

        Args:
            query: User query
            tweets: Tweet list
            intent_type: Intent type

        Returns:
            Simple ChatResponse
        """
        tweet_count = len(tweets)

        # Extract basic statistics
        usernames = [t.get('username', '') for t in tweets]
        unique_users = list(set(usernames))

        # Count most active users
        user_counts = {}
        for u in usernames:
            user_counts[u] = user_counts.get(u, 0) + 1
        top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        most_active = [u[0] for u in top_users]

        # Extract date range
        dates = []
        for t in tweets:
            date = t.get('tweet_date', t.get('date', ''))
            if date and len(date) >= 10:
                dates.append(date[:10])
        dates.sort()
        date_range = f"{dates[0]} - {dates[-1]}" if dates else None

        # Extract common words for topics (basic)
        all_text = " ".join([t.get('tweet_text', t.get('text', '')) for t in tweets])
        words = re.findall(r'\b\w+\b', all_text.lower())
        word_counts = {}
        stopwords = {
            'bir', 've', 'ile', 'icin', 'bu', 'su', 'o', 'da', 'de',
            'mi', 'mu', 'ne', 'ya', 'ki', 'ama', 'olan', 'daha', 'en',
            'rt', 'https', 'http', 'www', 'com', 'tr', 'co'
        }
        for w in words:
            if len(w) > 3 and w not in stopwords:
                word_counts[w] = word_counts.get(w, 0) + 1
        top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_topics = [w[0] for w in top_words]

        # Generate answer based on intent - use platform-aware terminology
        # Note: platform is not passed to this method, detect from tweets
        platforms_in_tweets = set(t.get('platform', 'twitter') for t in tweets)
        if 'instagram' in platforms_in_tweets and 'twitter' in platforms_in_tweets:
            detected_platform = 'both'
        elif 'instagram' in platforms_in_tweets:
            detected_platform = 'instagram'
        else:
            detected_platform = 'twitter'

        content_name = self._get_content_name(detected_platform, plural=False)

        if intent_type == "analyze_topics":
            answer = f"{tweet_count} {content_name} analiz edildi. One cikan konular: {', '.join(top_topics) if top_topics else 'cesitli konular'}."
        elif intent_type == "search_user":
            answer = f"{tweet_count} {content_name} bulundu. En cok etkilesim alan konular: {', '.join(top_topics[:3]) if top_topics else 'cesitli konular'}."
        elif intent_type == "search_date":
            answer = f"Belirtilen tarih araliginda {tweet_count} {content_name} bulundu."
        elif intent_type == "search_criticism":
            answer = f"Elestiri iceren {tweet_count} {content_name} bulundu."
        elif intent_type == "search_retweets":
            if detected_platform == 'twitter':
                answer = f"{tweet_count} retweet bulundu."
            else:
                answer = f"{tweet_count} {content_name} bulundu."
        else:
            answer = f"Aramaniza uygun {tweet_count} {content_name} bulundu."

        return ChatResponse(
            answer=answer,
            summary={
                "total_found": tweet_count,
                "top_topics": top_topics,
                "sentiment": "notr",  # Can't determine without AI
                "most_active_users": most_active,
                "date_range": date_range
            },
            confidence_score=0.5  # Lower confidence for rule-based
        )

    def should_generate_summary(self, tweet_count: int, intent_type: str) -> bool:
        """
        Determine if AI summary should be generated.

        Args:
            tweet_count: Number of tweets found
            intent_type: Type of query intent

        Returns:
            True if summary should be generated
        """
        # Always summarize for analysis queries
        if intent_type in ["analyze_topics", "search_criticism"]:
            return True

        # 5+ tweets get summary
        if tweet_count >= 5:
            return True

        # 10+ always gets summary
        if tweet_count >= 10:
            return True

        return False


# ============================================================================
# CLI TEST
# ============================================================================

if __name__ == "__main__":
    generator = ResponseGenerator()

    # Test tweets
    test_tweets = [
        {
            "username": "test_user1",
            "tweet_text": "Belediyemiz yeni parki acti. Halka hayirli olsun!",
            "tweet_date": "2024-01-15",
            "likes": 150
        },
        {
            "username": "test_user1",
            "tweet_text": "Sosyal yardim dagitimlari basliyor. Ihtiyac sahibi vatandaslarimiz basvurabilir.",
            "tweet_date": "2024-01-20",
            "likes": 200
        },
        {
            "username": "test_user2",
            "tweet_text": "Belediye hizmetleri cok iyi calisiyor. Tesekkurler baskanim!",
            "tweet_date": "2024-01-22",
            "likes": 75
        },
        {
            "username": "test_user2",
            "tweet_text": "Yeni yapilan yol cok guzele oldu.",
            "tweet_date": "2024-02-01",
            "likes": 50
        },
        {
            "username": "test_user3",
            "tweet_text": "Belediye otobuslerinde yeni uygulamaya gecildi.",
            "tweet_date": "2024-02-05",
            "likes": 30
        },
    ]

    print("=== RESPONSE GENERATOR TEST ===\n")

    response = generator.generate(
        query="Belediye hizmetleriyle ilgili tweetler",
        tweets=test_tweets,
        intent_type="search_topic"
    )

    print(f"Answer: {response.answer}")
    print(f"Summary: {json.dumps(response.summary, indent=2, ensure_ascii=False)}")
    print(f"Confidence: {response.confidence_score:.2f}")
