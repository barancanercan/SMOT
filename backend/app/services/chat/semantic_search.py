#!/usr/bin/env python3
"""
Semantic Search Module for Chat with Tweets

Provides TF-IDF based semantic search for Turkish tweets.
Lightweight alternative to vector databases like ChromaDB.

Features:
1. TF-IDF vectorization with Turkish preprocessing
2. Cosine similarity matching
3. Keyword-boosted relevance scoring
4. In-memory search (fast for moderate datasets)
"""

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

from app.services.chat.turkish_nlp import (
    TURKISH_STOPWORDS,
    calculate_keyword_score,
    expand_keywords,
    normalize_turkish,
    turkish_stem,
)
from app.utils.logger import get_logger

logger = get_logger("SemanticSearch")


# =============================================================================
# TF-IDF IMPLEMENTATION
# =============================================================================

@dataclass
class SearchResult:
    """Single search result with scoring."""
    item: dict[str, Any]
    score: float
    tfidf_score: float
    keyword_score: float
    engagement_score: float


class TurkishTFIDF:
    """
    TF-IDF vectorizer optimized for Turkish text.

    Uses:
    - Turkish stemming
    - Stopword removal
    - Character normalization
    """

    def __init__(self, min_df: int = 1, max_df_ratio: float = 0.95):
        """
        Initialize TF-IDF vectorizer.

        Args:
            min_df: Minimum document frequency
            max_df_ratio: Maximum document frequency ratio
        """
        self.min_df = min_df
        self.max_df_ratio = max_df_ratio

        self.vocabulary: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self.document_count = 0

    def fit(self, documents: list[str]) -> 'TurkishTFIDF':
        """
        Fit the vectorizer on documents.

        Args:
            documents: List of document strings

        Returns:
            self
        """
        self.document_count = len(documents)

        if self.document_count == 0:
            return self

        # Count document frequencies
        df: Counter = Counter()

        for doc in documents:
            tokens = self._tokenize(doc)
            unique_tokens = set(tokens)
            for token in unique_tokens:
                df[token] += 1

        # Filter by document frequency
        max_df = int(self.max_df_ratio * self.document_count)

        self.vocabulary = {}
        self.idf = {}
        idx = 0

        for token, count in df.items():
            if count >= self.min_df and count <= max_df:
                self.vocabulary[token] = idx
                # IDF with smoothing
                self.idf[token] = math.log((self.document_count + 1) / (count + 1)) + 1
                idx += 1

        logger.info(f"TF-IDF fitted: {self.document_count} docs, {len(self.vocabulary)} terms")
        return self

    def transform(self, documents: list[str]) -> list[dict[str, float]]:
        """
        Transform documents to TF-IDF vectors.

        Args:
            documents: List of document strings

        Returns:
            List of sparse vectors (dicts)
        """
        vectors = []

        for doc in documents:
            vector = self._document_to_vector(doc)
            vectors.append(vector)

        return vectors

    def fit_transform(self, documents: list[str]) -> list[dict[str, float]]:
        """Fit and transform in one step."""
        self.fit(documents)
        return self.transform(documents)

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize and stem text."""
        # Normalize and lowercase
        text = normalize_turkish(text.lower())

        # Extract words
        words = re.findall(r'\b\w+\b', text)

        # Filter and stem
        tokens = []
        for word in words:
            if len(word) > 2 and word not in TURKISH_STOPWORDS:
                stemmed = turkish_stem(word)
                if len(stemmed) > 2:
                    tokens.append(stemmed)

        return tokens

    def _document_to_vector(self, doc: str) -> dict[str, float]:
        """Convert document to TF-IDF sparse vector."""
        tokens = self._tokenize(doc)

        if not tokens:
            return {}

        # Term frequency
        tf: Counter = Counter(tokens)

        # TF-IDF
        vector = {}
        for token, count in tf.items():
            if token in self.vocabulary:
                # Normalized TF
                tf_score = count / len(tokens)
                # TF-IDF
                tfidf = tf_score * self.idf.get(token, 1.0)
                vector[token] = tfidf

        # L2 normalize
        norm = math.sqrt(sum(v ** 2 for v in vector.values()))
        if norm > 0:
            vector = {k: v / norm for k, v in vector.items()}

        return vector


def cosine_similarity(vec1: dict[str, float], vec2: dict[str, float]) -> float:
    """
    Calculate cosine similarity between two sparse vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Similarity score (0-1)
    """
    if not vec1 or not vec2:
        return 0.0

    # Dot product (only on common keys)
    common_keys = set(vec1.keys()) & set(vec2.keys())
    dot_product = sum(vec1[k] * vec2[k] for k in common_keys)

    # Vectors are already L2 normalized, so dot product = cosine similarity
    return dot_product


# =============================================================================
# SEMANTIC SEARCH ENGINE
# =============================================================================

class SemanticSearchEngine:
    """
    Semantic search engine for tweets.

    Combines TF-IDF similarity with keyword matching and engagement scoring.
    """

    # Weight factors for final score
    TFIDF_WEIGHT = 0.4
    KEYWORD_WEIGHT = 0.4
    ENGAGEMENT_WEIGHT = 0.2

    def __init__(self):
        """Initialize the search engine."""
        self.tfidf = TurkishTFIDF(min_df=1, max_df_ratio=0.9)
        self.documents: list[dict[str, Any]] = []
        self.vectors: list[dict[str, float]] = []
        self.max_engagement = 1

    def index(self, items: list[dict[str, Any]], text_field: str = "tweet_text") -> None:
        """
        Index items for search.

        Args:
            items: List of items (tweets) to index
            text_field: Field name containing text
        """
        if not items:
            return

        self.documents = items

        # Extract texts
        texts = [item.get(text_field, "") or "" for item in items]

        # Fit and transform
        self.vectors = self.tfidf.fit_transform(texts)

        # Calculate max engagement for normalization
        engagements = [self._get_engagement(item) for item in items]
        self.max_engagement = max(engagements) if engagements else 1

        logger.info(f"Indexed {len(items)} items for semantic search")

    def search(
        self,
        query: str,
        keywords: list[str] | None = None,
        top_k: int = 50,
        min_score: float = 0.1
    ) -> list[SearchResult]:
        """
        Search for items matching query.

        Args:
            query: Search query
            keywords: Additional keywords for boosting
            top_k: Maximum results to return
            min_score: Minimum score threshold

        Returns:
            List of SearchResult sorted by score
        """
        if not self.documents:
            return []

        # Transform query
        query_vector = self.tfidf._document_to_vector(query)

        # Expand keywords for matching
        expand_keywords(keywords or [])

        results = []

        for _i, (doc, vec) in enumerate(zip(self.documents, self.vectors, strict=False)):
            # TF-IDF similarity
            tfidf_score = cosine_similarity(query_vector, vec)

            # Keyword matching score
            text = doc.get("tweet_text", "")
            keyword_score = calculate_keyword_score(text, keywords or [])

            # Engagement score (normalized)
            engagement = self._get_engagement(doc)
            engagement_score = engagement / self.max_engagement if self.max_engagement > 0 else 0

            # Combined score
            final_score = (
                self.TFIDF_WEIGHT * tfidf_score +
                self.KEYWORD_WEIGHT * keyword_score +
                self.ENGAGEMENT_WEIGHT * engagement_score
            )

            if final_score >= min_score:
                results.append(SearchResult(
                    item=doc,
                    score=final_score,
                    tfidf_score=tfidf_score,
                    keyword_score=keyword_score,
                    engagement_score=engagement_score
                ))

        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)

        return results[:top_k]

    def _get_engagement(self, item: dict[str, Any]) -> float:
        """Calculate engagement score for an item."""
        likes = item.get("likes", 0) or 0
        retweets = item.get("retweets", 0) or 0
        replies = item.get("replies", 0) or 0
        comments = item.get("comments", 0) or 0

        # Weighted sum
        return likes + (retweets * 2) + replies + comments


# =============================================================================
# HYBRID SEARCH
# =============================================================================

class HybridSearchEngine:
    """
    Hybrid search combining SQL filters with semantic search.

    Flow:
    1. SQL filters narrow down candidates (date, user, party)
    2. Semantic search ranks by relevance
    3. Results are merged and re-ranked
    """

    def __init__(self):
        """Initialize hybrid search."""
        self.semantic = SemanticSearchEngine()

    def search(
        self,
        candidates: list[dict[str, Any]],
        query: str,
        keywords: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        max_results: int = 50
    ) -> list[dict[str, Any]]:
        """
        Perform hybrid search.

        Args:
            candidates: Pre-filtered items from SQL
            query: User query
            keywords: Extracted keywords
            filters: Applied filters (for metadata)
            max_results: Maximum results

        Returns:
            List of items with relevance scores
        """
        if not candidates:
            return []

        # Index candidates
        self.semantic.index(candidates)

        # Search
        results = self.semantic.search(
            query=query,
            keywords=keywords,
            top_k=max_results,
            min_score=0.05
        )

        # Convert to dict list with scores
        output = []
        for r in results:
            item = r.item.copy()
            item["relevance_score"] = round(r.score, 3)
            item["_search_details"] = {
                "tfidf_score": round(r.tfidf_score, 3),
                "keyword_score": round(r.keyword_score, 3),
                "engagement_score": round(r.engagement_score, 3)
            }
            output.append(item)

        return output


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def semantic_search(
    items: list[dict[str, Any]],
    query: str,
    keywords: list[str] | None = None,
    max_results: int = 50
) -> list[dict[str, Any]]:
    """
    Convenience function for one-shot semantic search.

    Args:
        items: Items to search
        query: Search query
        keywords: Optional keywords for boosting
        max_results: Maximum results

    Returns:
        List of items with relevance scores
    """
    engine = HybridSearchEngine()
    return engine.search(
        candidates=items,
        query=query,
        keywords=keywords,
        max_results=max_results
    )


# =============================================================================
# CLI TEST
# =============================================================================

if __name__ == "__main__":
    print("=== SEMANTIC SEARCH TEST ===\n")

    # Test tweets
    test_tweets = [
        {
            "id": 1,
            "username": "user1",
            "tweet_text": "Hükümetin ekonomi politikası başarısız. Enflasyon yükseliyor!",
            "likes": 150
        },
        {
            "id": 2,
            "username": "user2",
            "tweet_text": "Belediyemiz yeni parkı hizmete açtı. Vatandaşlarımız kullanabilir.",
            "likes": 50
        },
        {
            "id": 3,
            "username": "user3",
            "tweet_text": "İktidarın eğitim politikası sorgulanmalı. Öğretmenler mağdur!",
            "likes": 100
        },
        {
            "id": 4,
            "username": "user4",
            "tweet_text": "Ekonomik kriz derinleşiyor. Dolar yükseliyor, maaşlar eriyor.",
            "likes": 200
        },
        {
            "id": 5,
            "username": "user5",
            "tweet_text": "Sağlık hizmetleri iyileştirilmeli. Hastane kuyrukları çok uzun.",
            "likes": 75
        },
    ]

    # Search
    query = "hükümet ekonomi eleştirisi"
    keywords = ["hükümet", "ekonomi", "eleştiri"]

    print(f"Query: {query}")
    print(f"Keywords: {keywords}\n")

    results = semantic_search(test_tweets, query, keywords, max_results=5)

    print("RESULTS:")
    for i, r in enumerate(results, 1):
        print(f"\n{i}. @{r['username']} (score: {r['relevance_score']:.2f})")
        print(f"   {r['tweet_text'][:80]}...")
        details = r.get('_search_details', {})
        print(f"   TF-IDF: {details.get('tfidf_score', 0):.2f}, "
              f"Keyword: {details.get('keyword_score', 0):.2f}, "
              f"Engagement: {details.get('engagement_score', 0):.2f}")
