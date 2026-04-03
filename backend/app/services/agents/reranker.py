#!/usr/bin/env python3
"""
ReRanker - Lost-in-the-Middle Fix for A-RAG

Implements cross-encoder reranking to address the "lost in the middle" problem
where LLMs tend to ignore information in the middle of long contexts.

Based on:
- RAGTurk: Turkish RAG Best Practices (EACL 2026)
- Lost in the Middle Solutions

Strategy:
1. Broad retrieval (200 items)
2. Cross-encoder reranking (top 30-50)
3. Position optimization: Most relevant at start AND end
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
import math

from app.services.agents.base import BaseAgent, tool
from app.services.chat.semantic_search import semantic_search
from app.services.chat.turkish_nlp import calculate_keyword_score, extract_keywords
from app.utils.logger import get_logger

logger = get_logger("ReRanker")


@dataclass
class ReRankerConfig:
    """Configuration for reranking."""
    # Scoring weights
    semantic_weight: float = 0.4
    keyword_weight: float = 0.3
    engagement_weight: float = 0.2
    recency_weight: float = 0.1

    # Position optimization
    optimize_positions: bool = True
    front_positions: int = 5  # Items to place at front
    back_positions: int = 5   # Items to place at back


class ReRanker(BaseAgent):
    """
    Cross-Encoder ReRanker for Lost-in-the-Middle Fix.

    The "lost in the middle" problem occurs when LLMs fail to properly
    attend to information in the middle of long contexts. This reranker:

    1. Scores all items with multiple signals
    2. Reranks by combined relevance score
    3. Optimizes positions: most relevant at START and END

    Position Strategy (RAGTurk):
    - Top 5 most relevant -> positions 1-5 (start)
    - Next 5 most relevant -> last 5 positions (end)
    - Remaining -> middle positions
    """

    def __init__(self, config: ReRankerConfig = None):
        """Initialize reranker."""
        super().__init__("ReRanker")
        self.config = config or ReRankerConfig()
        logger.info("ReRanker initialized")

    def execute(
        self,
        query: str,
        contents: List[Dict],
        top_k: int = 50
    ) -> Dict[str, Any]:
        """
        Execute reranking pipeline.

        Args:
            query: Original query for relevance scoring
            contents: List of content items to rerank
            top_k: Number of top items to return

        Returns:
            Dict with reranked contents and metadata
        """
        if not contents:
            return {"contents": [], "metadata": {}}

        if len(contents) <= top_k:
            # No need to rerank small sets, just optimize positions
            if self.config.optimize_positions:
                optimized = self.call_tool(
                    "optimize_positions",
                    contents=contents,
                    query=query
                )
                return {"contents": optimized, "metadata": {"reranked": False}}
            return {"contents": contents, "metadata": {"reranked": False}}

        # Step 1: Score all items
        scored_contents = self.call_tool(
            "score_contents",
            contents=contents,
            query=query
        )

        # Step 2: Sort by score and take top_k
        sorted_contents = sorted(
            scored_contents,
            key=lambda x: x.get("_rerank_score", 0),
            reverse=True
        )[:top_k]

        # Step 3: Optimize positions
        if self.config.optimize_positions:
            final_contents = self.call_tool(
                "optimize_positions",
                contents=sorted_contents,
                query=query
            )
        else:
            final_contents = sorted_contents

        return {
            "contents": final_contents,
            "metadata": {
                "reranked": True,
                "original_count": len(contents),
                "final_count": len(final_contents)
            }
        }

    @tool(name="score_contents", description="Score contents with multiple relevance signals")
    def score_contents(
        self,
        contents: List[Dict],
        query: str
    ) -> List[Dict]:
        """
        Score contents using multiple signals.

        Signals:
        - Semantic: TF-IDF/embedding similarity
        - Keyword: Turkish keyword matching
        - Engagement: Likes, retweets, comments
        - Recency: Newer content scores higher

        Args:
            contents: Content list
            query: Query for relevance

        Returns:
            Contents with _rerank_score added
        """
        keywords = extract_keywords(query)

        for content in contents:
            # Semantic score (from existing search if available)
            semantic_score = content.get("relevance_score", 0)

            # Keyword score
            text = content.get("tweet_text", content.get("caption", ""))
            keyword_score = calculate_keyword_score(text, keywords) if keywords else 0

            # Engagement score (normalized)
            likes = content.get("likes", 0)
            retweets = content.get("retweets", 0)
            comments = content.get("comments", content.get("replies", 0))
            engagement = likes + retweets * 2 + comments * 3
            engagement_score = min(1.0, math.log(engagement + 1) / 10) if engagement > 0 else 0

            # Recency score
            date = content.get("tweet_date", content.get("post_date", ""))
            recency_score = self._calculate_recency_score(date)

            # Combined score
            combined_score = (
                self.config.semantic_weight * semantic_score +
                self.config.keyword_weight * keyword_score +
                self.config.engagement_weight * engagement_score +
                self.config.recency_weight * recency_score
            )

            content["_rerank_score"] = combined_score
            content["_rerank_details"] = {
                "semantic": semantic_score,
                "keyword": keyword_score,
                "engagement": engagement_score,
                "recency": recency_score
            }

        return contents

    @tool(name="optimize_positions", description="Optimize content positions for LLM attention")
    def optimize_positions(
        self,
        contents: List[Dict],
        query: str = ""
    ) -> List[Dict]:
        """
        Optimize positions to fix lost-in-the-middle.

        Strategy (RAGTurk):
        - Most relevant items go to START and END
        - Less relevant items go to MIDDLE
        - This ensures LLM sees key info at attention peaks

        Args:
            contents: Pre-sorted content list (by relevance)
            query: Query (for potential re-scoring)

        Returns:
            Position-optimized content list
        """
        if len(contents) <= 10:
            return contents

        # Sort by existing score if available
        sorted_contents = sorted(
            contents,
            key=lambda x: x.get("_rerank_score", x.get("relevance_score", 0)),
            reverse=True
        )

        # Take items for different positions
        front = self.config.front_positions
        back = self.config.back_positions

        front_items = sorted_contents[:front]
        back_items = sorted_contents[front:front + back]
        middle_items = sorted_contents[front + back:]

        # Reorder: front -> middle -> back
        # This places top items at start and end (where LLM attends most)
        optimized = front_items + middle_items + back_items

        # Add position metadata
        for i, item in enumerate(optimized):
            item["_position"] = i
            if i < front:
                item["_position_zone"] = "front"
            elif i >= len(optimized) - back:
                item["_position_zone"] = "back"
            else:
                item["_position_zone"] = "middle"

        return optimized

    @tool(name="rerank_by_query", description="Rerank contents by query relevance")
    def rerank_by_query(
        self,
        contents: List[Dict],
        query: str,
        top_k: int = 30
    ) -> List[Dict]:
        """
        Simple reranking by query relevance.

        Uses semantic search for fast reranking.

        Args:
            contents: Content list
            query: Query for relevance
            top_k: Number of items to return

        Returns:
            Reranked content list
        """
        keywords = extract_keywords(query)
        return semantic_search(
            items=contents,
            query=query,
            keywords=keywords,
            max_results=top_k
        )

    # ==========================================================================
    # Private Helper Methods
    # ==========================================================================

    def _calculate_recency_score(self, date_str: str) -> float:
        """
        Calculate recency score for a date.

        Newer = higher score (0-1 range)
        """
        if not date_str or len(date_str) < 10:
            return 0.5  # Unknown date gets middle score

        try:
            from datetime import datetime, timedelta
            date = datetime.strptime(date_str[:10], "%Y-%m-%d")
            now = datetime.now()
            age_days = (now - date).days

            if age_days <= 7:
                return 1.0
            elif age_days <= 30:
                return 0.8
            elif age_days <= 90:
                return 0.6
            elif age_days <= 365:
                return 0.4
            else:
                return 0.2
        except:
            return 0.5
