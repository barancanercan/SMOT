#!/usr/bin/env python3
"""
Retriever Agent - Content Retrieval for A-RAG

Provides hybrid search capabilities:
- Keyword search with BM25/TF-IDF
- Semantic search with Turkish NLP
- Filter-based retrieval (date, party, user)

Tools:
- keyword_search: BM25 + Turkish stemming
- semantic_search: TF-IDF + cosine similarity
- filter_results: Apply date/party/user filters
- chunk_read: Read specific content by ID
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.services.agents.base import BaseAgent, tool
from app.core.models import Tweet, Councilor, InstagramPost
from app.core.constants import normalize_party_name
from app.services.chat.turkish_nlp import expand_keywords, calculate_keyword_score
from app.services.chat.semantic_search import semantic_search
from app.utils.logger import get_logger

logger = get_logger("RetrieverAgent")


@dataclass
class RetrievalConfig:
    """Configuration for content retrieval."""
    max_pool_size: int = 200  # Pre-fetch pool size
    keyword_weight: float = 0.4
    semantic_weight: float = 0.4
    engagement_weight: float = 0.2


class RetrieverAgent(BaseAgent):
    """
    Content Retrieval Agent for A-RAG.

    Implements hybrid search combining:
    - SQL-based filtering (fast pre-filtering)
    - Keyword matching with Turkish NLP
    - Semantic ranking with TF-IDF

    Tools:
    - keyword_search: Search by keywords with expansion
    - semantic_search: Semantic similarity search
    - filter_results: Apply metadata filters
    - chunk_read: Read specific content items
    """

    def __init__(self, db: Session, config: RetrievalConfig = None):
        """Initialize retriever with database session."""
        super().__init__("RetrieverAgent")
        self.db = db
        self.config = config or RetrievalConfig()
        logger.info("RetrieverAgent initialized")

    def execute(
        self,
        query: str,
        platform: str = "twitter",
        party_filter: Optional[str] = None,
        max_results: int = 50,
        keywords: List[str] = None
    ) -> Dict[str, Any]:
        """
        Execute content retrieval.

        Args:
            query: Search query
            platform: Platform filter (twitter/instagram/both)
            party_filter: Optional party filter
            max_results: Maximum results to return
            keywords: Optional pre-extracted keywords

        Returns:
            Dict with contents list and metadata
        """
        all_contents = []

        # Get party members if filtering
        party_usernames = None
        if party_filter:
            party_usernames = self._get_party_members(party_filter)
            if not party_usernames:
                return {"contents": [], "metadata": {"party_not_found": party_filter}}

        # Extract keywords if not provided
        if not keywords:
            keywords = self._extract_keywords(query)

        # Search Twitter
        if platform in ["twitter", "both"]:
            twitter_contents = self.call_tool(
                "keyword_search",
                query=query,
                keywords=keywords,
                source="twitter",
                party_usernames=party_usernames,
                limit=self.config.max_pool_size if platform == "both" else self.config.max_pool_size * 2
            )
            all_contents.extend(twitter_contents)
            logger.info(f"Retrieved {len(twitter_contents)} tweets")

        # Search Instagram
        if platform in ["instagram", "both"]:
            instagram_contents = self.call_tool(
                "keyword_search",
                query=query,
                keywords=keywords,
                source="instagram",
                party_usernames=party_usernames,
                limit=self.config.max_pool_size if platform == "both" else self.config.max_pool_size * 2
            )
            all_contents.extend(instagram_contents)
            logger.info(f"Retrieved {len(instagram_contents)} Instagram posts")

        if not all_contents:
            return {"contents": [], "metadata": {"query": query}}

        # Apply semantic ranking
        if keywords or query:
            ranked_contents = self.call_tool(
                "semantic_search",
                contents=all_contents,
                query=query,
                keywords=keywords,
                max_results=max_results
            )
        else:
            # Sort by engagement
            ranked_contents = sorted(
                all_contents,
                key=lambda x: x.get("likes", 0) + x.get("retweets", 0) * 2,
                reverse=True
            )[:max_results]

        return {
            "contents": ranked_contents,
            "metadata": {
                "query": query,
                "platform": platform,
                "total_retrieved": len(all_contents),
                "final_count": len(ranked_contents)
            }
        }

    @tool(name="keyword_search", description="Search content by keywords with Turkish NLP expansion")
    def keyword_search(
        self,
        query: str,
        keywords: List[str] = None,
        source: str = "twitter",
        party_usernames: List[str] = None,
        limit: int = 200
    ) -> List[Dict]:
        """
        Search content using keyword matching with Turkish NLP.

        Args:
            query: Search query
            keywords: Pre-extracted keywords
            source: Content source (twitter/instagram)
            party_usernames: Optional list of usernames to filter
            limit: Maximum items to retrieve

        Returns:
            List of content dicts
        """
        if source == "twitter":
            return self._search_twitter(keywords, party_usernames, limit)
        else:
            return self._search_instagram(keywords, party_usernames, limit)

    @tool(name="semantic_search", description="Rank content by semantic similarity using TF-IDF")
    def semantic_search_tool(
        self,
        contents: List[Dict],
        query: str,
        keywords: List[str] = None,
        max_results: int = 50
    ) -> List[Dict]:
        """
        Rank content by semantic similarity.

        Args:
            contents: List of content items
            query: Original query
            keywords: Keywords for scoring
            max_results: Maximum results to return

        Returns:
            Ranked list of content items
        """
        if not contents:
            return []

        return semantic_search(
            items=contents,
            query=query,
            keywords=keywords or [],
            max_results=max_results
        )

    @tool(name="filter_results", description="Apply date, party, or user filters to content")
    def filter_results(
        self,
        contents: List[Dict],
        start_date: str = None,
        end_date: str = None,
        party: str = None,
        username: str = None
    ) -> List[Dict]:
        """
        Filter content by metadata.

        Args:
            contents: List of content items
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            party: Party filter
            username: Username filter

        Returns:
            Filtered list of content items
        """
        filtered = contents

        if start_date:
            filtered = [c for c in filtered if c.get("tweet_date", "") >= start_date]

        if end_date:
            filtered = [c for c in filtered if c.get("tweet_date", "") <= end_date]

        if party:
            normalized = normalize_party_name(party)
            filtered = [
                c for c in filtered
                if normalize_party_name(c.get("party", "")) == normalized
            ]

        if username:
            filtered = [c for c in filtered if c.get("username") == username]

        return filtered

    @tool(name="chunk_read", description="Read specific content items by their IDs")
    def chunk_read(
        self,
        content_ids: List[int],
        source: str = "twitter"
    ) -> List[Dict]:
        """
        Read specific content items by ID.

        Args:
            content_ids: List of content IDs to read
            source: Content source (twitter/instagram)

        Returns:
            List of content dicts
        """
        if source == "twitter":
            items = self.db.query(Tweet).filter(Tweet.id.in_(content_ids)).all()
            return [self._tweet_to_dict(t) for t in items]
        else:
            items = self.db.query(InstagramPost).filter(InstagramPost.id.in_(content_ids)).all()
            return [self._post_to_dict(p) for p in items]

    # ==========================================================================
    # Private Helper Methods
    # ==========================================================================

    def _search_twitter(
        self,
        keywords: List[str],
        party_usernames: List[str] = None,
        limit: int = 200
    ) -> List[Dict]:
        """Search Twitter content."""
        query = self.db.query(Tweet).filter(Tweet.is_retweet == False)

        if party_usernames:
            query = query.filter(Tweet.username.in_(party_usernames))

        # Keyword filtering with expansion
        if keywords:
            expanded = expand_keywords(keywords)[:15]
            keyword_filters = [Tweet.tweet_text.ilike(f"%{kw}%") for kw in expanded]
            query = query.filter(or_(*keyword_filters))

        query = query.order_by(Tweet.likes.desc(), Tweet.tweet_date.desc())
        tweets = query.limit(limit).all()

        contents = []
        for t in tweets:
            content = self._tweet_to_dict(t)
            if keywords:
                content["keyword_score"] = calculate_keyword_score(
                    content.get("tweet_text", ""),
                    keywords
                )
            contents.append(content)

        return contents

    def _search_instagram(
        self,
        keywords: List[str],
        party_usernames: List[str] = None,
        limit: int = 200
    ) -> List[Dict]:
        """Search Instagram content."""
        query = self.db.query(InstagramPost)

        if party_usernames:
            query = query.filter(InstagramPost.username.in_(party_usernames))

        # Keyword filtering
        if keywords:
            expanded = expand_keywords(keywords)[:15]
            keyword_filters = [InstagramPost.caption.ilike(f"%{kw}%") for kw in expanded]
            query = query.filter(or_(*keyword_filters))

        query = query.order_by(InstagramPost.likes.desc(), InstagramPost.post_date.desc())
        posts = query.limit(limit).all()

        contents = []
        for p in posts:
            content = self._post_to_dict(p)
            if keywords:
                content["keyword_score"] = calculate_keyword_score(
                    content.get("caption", ""),
                    keywords
                )
            contents.append(content)

        return contents

    def _tweet_to_dict(self, tweet: Tweet) -> Dict:
        """Convert Tweet ORM object to dict."""
        councilor = self.db.query(Councilor).filter(
            Councilor.username == tweet.username
        ).first()

        return {
            "id": tweet.id,
            "username": tweet.username,
            "name": councilor.name if councilor else tweet.username,
            "party": normalize_party_name(councilor.party) if councilor and councilor.party else None,
            "tweet_text": tweet.tweet_text,
            "tweet_date": str(tweet.tweet_date) if tweet.tweet_date else None,
            "likes": tweet.likes or 0,
            "retweets": tweet.retweets or 0,
            "replies": tweet.replies or 0,
            "views": tweet.views or 0,
            "platform": "twitter",
        }

    def _post_to_dict(self, post: InstagramPost) -> Dict:
        """Convert InstagramPost ORM object to dict."""
        councilor = self.db.query(Councilor).filter(
            Councilor.username == post.username
        ).first()

        caption = post.caption or ""

        return {
            "id": post.id,
            "username": post.username,
            "name": councilor.name if councilor else post.username,
            "party": normalize_party_name(councilor.party) if councilor and councilor.party else None,
            "tweet_text": caption,  # Compatibility
            "caption": caption,
            "tweet_date": str(post.post_date) if post.post_date else None,
            "post_date": str(post.post_date) if post.post_date else None,
            "likes": post.likes or 0,
            "comments": post.comments or 0,
            "replies": post.comments or 0,  # Compatibility
            "retweets": 0,
            "views": 0,
            "platform": "instagram",
            "post_url": post.post_url,
        }

    def _get_party_members(self, party: str) -> List[str]:
        """Get usernames for a party."""
        normalized_party = normalize_party_name(party)
        councilors = self.db.query(Councilor).all()

        return [
            c.username
            for c in councilors
            if normalize_party_name(c.party) == normalized_party
        ]

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query."""
        # Simple keyword extraction - stopword removal
        stopwords = {
            'bir', 've', 'ile', 'icin', 'bu', 'su', 'o', 'da', 'de',
            'mi', 'mu', 'ne', 'ya', 'ki', 'ama', 'olan', 'daha', 'en',
            'getir', 'göster', 'goster', 'bul', 'ara', 'listele',
            'tweetler', 'tweetleri', 'hakkında', 'hakkinda', 'ilgili'
        }

        words = query.lower().split()
        keywords = [w for w in words if len(w) > 2 and w not in stopwords]

        return keywords[:10]  # Limit to 10 keywords
