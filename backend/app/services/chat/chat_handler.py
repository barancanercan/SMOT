#!/usr/bin/env python3
"""
Chat Handler v7 - Hybrid RAG with BM25 + Dense + RRF + Reranking

2026 State-of-the-art pipeline:
    Query → Analyze → [BM25 | Dense] → RRF → Rerank → Generate

Key improvements over v6:
- Single query analysis pass (merged QueryReasoner + IntentParser)
- Hybrid retrieval (BM25 + embeddings + RRF fusion)
- Cross-encoder reranking for precision
- Proper cache keys with party/platform
- Clean response formatting with citations
- Reduced LLM calls: max 1 (response generation only)
"""

import time
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.constants import normalize_party_name
from app.core.models import Councilor, InstagramPost, Tweet
from app.services.chat.hybrid_retriever import get_hybrid_retriever
from app.services.chat.query_analyzer import AnalyzedQuery, get_query_analyzer
from app.services.chat.query_cache import (
    get_response_cache,
    set_response_cache,
)
from app.services.chat.response_generator import (
    ChatResponse,
    ResponseGenerator,
    _get_content_name,
    compute_confidence,
)
from app.services.chat.turkish_nlp import expand_keywords
from app.utils.logger import get_logger

logger = get_logger("ChatHandler")

# Opposite party mapping for suggestions
OPPOSITE_PARTIES = {
    "CHP": "AK Parti",
    "AK Parti": "CHP",
    "AKP": "CHP",
    "MHP": "CHP",
    "BBP": "CHP",
    "İYİ Parti": "AK Parti",
    "YRP": "CHP",
    "Bağımsız": None,
    "BAGIMSIZ": None,
}


@dataclass
class ChatQueryResult:
    """Complete result of a chat query."""
    query: str
    answer: str
    summary: dict[str, Any] = field(default_factory=dict)
    tweets: list[dict] = field(default_factory=list)
    filters_applied: dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    execution_time_ms: float = 0.0
    cached: bool = False
    intent_type: str = "search_topic"


class ChatHandler:
    """
    Chat with Social Media - Main Orchestrator v7.

    Pipeline:
    1. Check cache
    2. Analyze query (rule-based, 0 LLM calls)
    3. Get content pool from DB (SQL filters)
    4. Hybrid retrieval (BM25 + Dense + RRF + Reranking)
    5. Generate response (1 LLM call)
    6. Cache result
    """

    MAX_RESULTS = 50
    DEFAULT_MAX_RESULTS = 20
    CONTENT_POOL_SIZE = 500  # More content for hybrid retrieval

    def __init__(self, db: Session):
        self.db = db
        self.analyzer = get_query_analyzer()
        self.retriever = get_hybrid_retriever()
        self.response_generator = ResponseGenerator()
        logger.info("ChatHandler v7 initialized")

    def process_query(
        self,
        query: str,
        max_results: int = DEFAULT_MAX_RESULTS,
        include_summary: bool = True,
        party_filter: str | None = None,
        platform: str = "twitter",
    ) -> ChatQueryResult:
        """
        Process a natural language query.

        Args:
            query: Turkish natural language query
            max_results: Maximum results to return
            include_summary: Whether to include AI summary
            party_filter: Party filter from UI
            platform: Platform (twitter, instagram, both)
        """
        start_time = time.time()

        if not query or len(query.strip()) < 3:
            return ChatQueryResult(
                query=query,
                answer="Lütfen en az 3 karakterlik bir soru girin.",
                summary={"total_found": 0},
                confidence_score=0.0,
                execution_time_ms=0.0,
            )

        # Normalize party_filter
        if party_filter in (None, "", "None", "null", "undefined"):
            party_filter = None

        max_results = min(max(1, max_results), self.MAX_RESULTS)

        # Check for detailed analysis request
        query_lower = query.lower()
        if any(kw in query_lower for kw in ['detaylı', 'detayli', 'kapsamlı', 'kapsamli']):
            max_results = max(max_results, 30)

        try:
            # --- Step 1: Check response cache ---
            cache_filters = {"party": party_filter, "platform": platform}
            cached = get_response_cache(query, cache_filters, platform)
            if cached:
                logger.info("Response cache HIT")
                return ChatQueryResult(
                    query=query,
                    answer=cached.get("answer", ""),
                    summary=cached.get("summary", {}),
                    tweets=cached.get("tweets", []),
                    filters_applied=cached.get("filters_applied", {}),
                    confidence_score=cached.get("confidence_score", 0.8),
                    execution_time_ms=(time.time() - start_time) * 1000,
                    cached=True,
                    intent_type=cached.get("intent_type", "search_topic"),
                )

            # --- Step 2: Analyze query (rule-based, fast) ---
            analysis = self.analyzer.analyze(query, party_filter, platform)
            logger.info(
                f"Analysis: intent={analysis.intent}, topic={analysis.detected_topic}, "
                f"criticism={analysis.is_criticism}, keywords={analysis.keywords[:5]}"
            )

            # --- Step 3: Get content pool from database ---
            content_pool = self._get_content_pool(analysis, platform)
            logger.info(f"Content pool: {len(content_pool)} items")

            if not content_pool:
                content_name = _get_content_name(platform, "accusative")
                party_note = f" ({party_filter} partisinde)" if party_filter else ""
                return ChatQueryResult(
                    query=query,
                    answer=f"Aramanıza uygun {content_name}{party_note} bulunamadı. "
                           f"Parti filtresini kaldırmayı veya farklı kelimeler denemeyi önerebilirim.",
                    summary={"total_found": 0},
                    confidence_score=0.0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    intent_type=analysis.intent,
                )

            # --- Step 4: Hybrid retrieval (BM25 + Dense + RRF + Reranking) ---
            retrieval = self.retriever.retrieve(
                query=analysis.search_query,
                documents=content_pool,
                top_k=max_results,
                is_criticism=analysis.is_criticism,
            )

            # Convert to tweet dicts
            tweets = []
            retrieval_scores = []
            for result in retrieval.results:
                tweet = result.content.copy()
                tweet["relevance_score"] = result.final_score
                tweet["criticism_topic"] = ""
                tweet["criticism_explanation"] = ""
                tweets.append(tweet)
                retrieval_scores.append(result.final_score)

            logger.info(
                f"Retrieval: {len(tweets)} results in {retrieval.retrieval_time_ms:.0f}ms"
            )

            # Sort by engagement (likes + retweets) for better UX
            tweets.sort(
                key=lambda t: (t.get("likes", 0) + t.get("retweets", 0)),
                reverse=True,
            )

            # --- Step 5: Generate response (1 LLM call) ---
            if include_summary and tweets:
                response = self.response_generator.generate(
                    query=query,
                    tweets=tweets,
                    intent_type=analysis.intent,
                    username=analysis.username,
                    platform=platform,
                    is_criticism=analysis.is_criticism,
                )
            elif not tweets:
                content_name = _get_content_name(platform, "accusative")
                response = ChatResponse(
                    answer=f"Aramanıza uygun {content_name} bulunamadı.",
                    summary={"total_found": 0},
                )
            else:
                content_name = _get_content_name(platform)
                response = ChatResponse(
                    answer=f"**{len(tweets)} {content_name}** bulundu.",
                    summary={"total_found": len(tweets)},
                )

            # Compute confidence from retrieval scores
            confidence = compute_confidence(retrieval_scores, len(tweets))
            if response.confidence_score > 0:
                confidence = max(confidence, response.confidence_score)

            execution_time_ms = (time.time() - start_time) * 1000

            result = ChatQueryResult(
                query=query,
                answer=response.answer,
                summary=response.summary,
                tweets=tweets,
                filters_applied={
                    "party": party_filter,
                    "platform": platform,
                    "topic": analysis.detected_topic,
                    "is_criticism": analysis.is_criticism,
                    "target_party": analysis.target_party,
                    "keywords": analysis.keywords[:5],
                },
                confidence_score=confidence,
                execution_time_ms=execution_time_ms,
                cached=False,
                intent_type=analysis.intent,
            )

            # --- Step 6: Cache result ---
            if tweets:
                cache_data = {
                    "answer": response.answer,
                    "summary": response.summary,
                    "tweets": tweets[:20],
                    "filters_applied": result.filters_applied,
                    "confidence_score": result.confidence_score,
                    "intent_type": result.intent_type,
                }
                set_response_cache(query, cache_data, cache_filters, platform)

            logger.info(
                f"Query completed: {len(tweets)} results, "
                f"{execution_time_ms:.0f}ms, confidence={confidence:.2f}"
            )

            return result

        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return ChatQueryResult(
                query=query,
                answer=f"Sorgu işlenirken hata oluştu: {str(e)}",
                summary={"total_found": 0, "error": str(e)},
                confidence_score=0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    def _get_content_pool(
        self,
        analysis: AnalyzedQuery,
        platform: str,
    ) -> list[dict]:
        """
        Get content pool from database using SQL filters.

        Uses party filter, date range, and keyword pre-filtering to narrow candidates.
        Returns a large pool for hybrid retrieval to rank.

        For criticism queries: uses broader keyword set (target party name + criticism terms).
        For topic queries: uses topic-specific keywords.
        """
        # Get party members if filter is set
        party_usernames = None
        if analysis.source_party:
            party_usernames = self._get_party_members(analysis.source_party)
            if not party_usernames:
                logger.warning(f"No members found for party: {analysis.source_party}")
                return []

        # Build keyword list based on intent
        keywords = analysis.keywords[:]
        if analysis.is_criticism:
            # For criticism queries, cast a WIDE net in SQL
            # Politicians criticize using names, indirect terms, and Turkish political slang
            if analysis.target_party:
                target = analysis.target_party.lower()
                if target in ("ak parti", "akp", "hükümet"):
                    keywords.extend([
                        "hükümet", "hukumet", "iktidar", "akp", "ak parti",
                        "erdoğan", "erdogan", "saray", "ankara",
                        # Criticism terms used against government
                        "başarısız", "basarisiz", "kriz", "enflasyon", "zam",
                        "yolsuzluk", "israf", "pahalılık",
                    ])
                elif target == "chp":
                    keywords.extend([
                        "chp", "muhalefet", "belediye",
                        # CHP leaders that get criticized
                        "mansur", "yavaş", "yavas", "imamoğlu", "imamoglu",
                        "özgür", "ozgur", "özel", "ozel",
                        # Infrastructure/service failure terms (common CHP criticism)
                        "su", "altyapı", "altyapi", "imar",
                        # General criticism terms
                        "beceriksiz", "algı", "algi", "sorumsuz",
                        "rezalet", "fiyasko", "skandal",
                    ])
                elif target == "mhp":
                    keywords.extend(["mhp", "bahçeli", "bahceli"])

            # General criticism keywords for any target
            keywords.extend([
                "eleştiri", "elestiri", "başarısız", "basarisiz",
                "kötü", "kotu", "rezalet", "skandal", "beceriksiz",
                "yolsuzluk", "sorun", "itiraz", "yanlış", "yanlis",
            ])
            keywords = list(set(keywords))

        content = []
        pool_size = self.CONTENT_POOL_SIZE

        # Get Twitter content
        if platform in ("twitter", "both"):
            limit = pool_size if platform == "twitter" else pool_size // 2
            twitter = self._query_twitter(
                party_usernames=party_usernames,
                keywords=keywords,
                username=analysis.username,
                start_date=analysis.start_date,
                end_date=analysis.end_date,
                limit=limit,
            )
            content.extend(twitter)

        # Get Instagram content
        if platform in ("instagram", "both"):
            limit = pool_size if platform == "instagram" else pool_size // 2
            instagram = self._query_instagram(
                party_usernames=party_usernames,
                keywords=keywords,
                username=analysis.username,
                start_date=analysis.start_date,
                end_date=analysis.end_date,
                limit=limit,
            )
            content.extend(instagram)

        return content

    def _query_twitter(
        self,
        party_usernames: list[str] | None,
        keywords: list[str],
        username: str | None,
        start_date: str | None,
        end_date: str | None,
        limit: int,
    ) -> list[dict]:
        """Query Twitter content from database."""
        query = self.db.query(Tweet).filter(Tweet.is_retweet == False)

        if party_usernames:
            query = query.filter(Tweet.username.in_(party_usernames))

        if username:
            query = query.filter(Tweet.username == username)

        if start_date:
            query = query.filter(Tweet.tweet_date >= start_date)
        if end_date:
            query = query.filter(Tweet.tweet_date <= end_date)

        # Keyword pre-filtering: use OR logic with expanded keywords
        if keywords:
            expanded = expand_keywords(keywords[:6])[:15]
            if expanded:
                kw_filters = [Tweet.tweet_text.ilike(f"%{kw}%") for kw in expanded]
                query = query.filter(or_(*kw_filters))

        query = query.order_by(Tweet.likes.desc(), Tweet.tweet_date.desc())
        tweets_orm = query.limit(limit).all()

        results = []
        for t in tweets_orm:
            councilor = self.db.query(Councilor).filter(
                Councilor.username == t.username
            ).first()

            results.append({
                "id": t.id,
                "username": t.username,
                "name": councilor.name if councilor else t.username,
                "party": normalize_party_name(councilor.party) if councilor and councilor.party else None,
                "tweet_text": t.tweet_text,
                "tweet_date": str(t.tweet_date) if t.tweet_date else None,
                "likes": t.likes or 0,
                "retweets": t.retweets or 0,
                "replies": t.replies or 0,
                "views": t.views or 0,
                "platform": "twitter",
                "tweet_url": t.tweet_url if t.tweet_url else (f"https://x.com/{t.username}/status/{t.tweet_id}" if t.tweet_id else None),
            })

        return results

    def _query_instagram(
        self,
        party_usernames: list[str] | None,
        keywords: list[str],
        username: str | None,
        start_date: str | None,
        end_date: str | None,
        limit: int,
    ) -> list[dict]:
        """Query Instagram content from database."""
        query = self.db.query(InstagramPost)

        if party_usernames:
            query = query.filter(InstagramPost.username.in_(party_usernames))

        if username:
            query = query.filter(InstagramPost.username == username)

        if start_date:
            query = query.filter(InstagramPost.post_date >= start_date)
        if end_date:
            query = query.filter(InstagramPost.post_date <= end_date)

        # Keyword pre-filtering
        if keywords:
            expanded = expand_keywords(keywords[:6])[:15]
            if expanded:
                kw_filters = [InstagramPost.caption.ilike(f"%{kw}%") for kw in expanded]
                query = query.filter(or_(*kw_filters))

        query = query.order_by(InstagramPost.likes.desc(), InstagramPost.post_date.desc())
        posts_orm = query.limit(limit).all()

        results = []
        for p in posts_orm:
            councilor = self.db.query(Councilor).filter(
                Councilor.username == p.username
            ).first()

            caption = p.caption or ""
            results.append({
                "id": p.id,
                "username": p.username,
                "name": councilor.name if councilor else p.username,
                "party": normalize_party_name(councilor.party) if councilor and councilor.party else None,
                "tweet_text": caption,
                "caption": caption,
                "tweet_date": str(p.post_date) if p.post_date else None,
                "post_date": str(p.post_date) if p.post_date else None,
                "likes": p.likes or 0,
                "retweets": 0,
                "comments": p.comments or 0,
                "replies": p.comments or 0,
                "views": 0,
                "platform": "instagram",
                "post_url": p.post_url,
                "is_video": p.is_video,
            })

        return results

    def _get_party_members(self, party: str) -> list[str]:
        """Get usernames belonging to a party."""
        normalized = normalize_party_name(party)
        councilors = self.db.query(Councilor).all()
        members = [
            c.username for c in councilors
            if normalize_party_name(c.party) == normalized
        ]
        logger.info(f"Party '{normalized}': {len(members)} members")
        return members

    def get_suggested_questions(
        self,
        platform: str = "twitter",
        party_filter: str | None = None,
    ) -> list[str]:
        """Get suggested questions for chat UI."""
        content_name = _get_content_name(platform)

        opposite = OPPOSITE_PARTIES.get(party_filter) if party_filter else None

        suggestions = [
            f"Belediye hizmetleriyle ilgili {content_name}",
            f"En çok etkileşim alan {content_name}",
            f"Ekonomi hakkında {content_name}",
            f"Ulaşım konulu {content_name}",
        ]

        if opposite:
            suggestions.append(f"{opposite} eleştirisi içeren {content_name}")
        else:
            suggestions.append(f"Hükümet eleştirisi içeren {content_name}")

        if platform == "instagram":
            suggestions.append("En çok beğeni alan paylaşımlar")
        elif platform == "twitter":
            suggestions.append("Viral olan tweetler")
        else:
            suggestions.append("En popüler paylaşımlar")

        return suggestions[:6]
