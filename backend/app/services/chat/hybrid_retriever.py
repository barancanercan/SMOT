"""
Hybrid Retriever v7 - BM25 + Dense Embeddings + RRF + Cross-Encoder Reranking

2026 State-of-the-art RAG pipeline:
1. BM25 sparse retrieval (keyword matching)
2. Dense embedding retrieval (semantic similarity)
3. Reciprocal Rank Fusion to merge results
4. Cross-encoder reranking for final precision

Architecture:
    Query → [BM25 | Dense] → RRF Fusion → Cross-Encoder Rerank → Top-K

Performance:
    - BM25: exact keyword matching, handles Turkish morphology
    - Dense: semantic understanding, handles paraphrases
    - RRF: combines both without score normalization
    - Reranker: precision boost on top candidates
"""

import re
import time
from dataclasses import dataclass
from typing import Any

import numpy as np
from rank_bm25 import BM25Okapi

try:
    from sentence_transformers import CrossEncoder, SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from app.services.chat.turkish_nlp import (
    TURKISH_STOPWORDS,
    normalize_turkish,
)
from app.utils.logger import get_logger

logger = get_logger("HybridRetriever")


# =============================================================================
# TOPIC & CRITICISM DEFINITIONS
# =============================================================================

TOPIC_KEYWORDS = {
    "ekonomi": [
        "ekonomi", "ekonomik", "enflasyon", "pahalılık", "pahalilik",
        "hayat pahalı", "fiyat artış", "asgari ücret", "asgari ucret",
        "emekli maaş", "emekli maas", "geçim sıkıntı", "gecim sikinti",
        "bütçe", "butce", "kur", "döviz", "doviz", "işsizlik", "issizlik",
        "maaş", "maas", "zam",
    ],
    "belediye": [
        "belediye", "park", "metro", "otobüs", "otobus", "altyapı", "altyapi",
        "çöp", "cop", "su", "kanalizasyon", "yol", "asfalt", "yeşil alan",
        "yesil alan", "belediyemiz", "belediyecilik", "şehir", "sehir",
    ],
    "ulaşım": [
        "ulaşım", "ulasim", "trafik", "metro", "otobüs", "otobus",
        "köprü", "kopru", "yol", "havalimanı", "havalimani",
        "bisiklet", "toplu taşıma", "toplu tasima", "tramvay",
    ],
    "eğitim": [
        "eğitim", "egitim", "okul", "öğretmen", "ogretmen",
        "öğrenci", "ogrenci", "üniversite", "universite",
        "sınav", "sinav", "müfredat", "mufredat", "meb", "yök", "yok",
    ],
    "sağlık": [
        "sağlık", "saglik", "hastane", "doktor", "ilaç", "ilac",
        "aşı", "asi", "tedavi", "acil", "ameliyat", "hemşire", "hemsire",
    ],
}

CRITICISM_KEYWORDS = [
    "eleştiri", "elestiri", "eleştir", "elestir", "eleştiren", "elestiren",
    "başarısız", "basarisiz", "kötü", "kotu", "berbat",
    "rezalet", "skandal", "yolsuzluk", "felaket", "sefalet", "kriz",
    "karşı", "karsi", "tepki", "protesto", "şikayet", "sikayet",
    "yetersiz", "beceriksiz", "perişan", "perisan",
    "batırdı", "batirdi", "çöktü", "coktu", "iflas",
]

NEGATIVE_WORDS = {
    # Strong negative
    "berbat", "rezalet", "felaket", "fiyasko", "skandal", "yolsuzluk",
    "sefalet", "perişan", "perisan", "batırdı", "battık", "çöktü", "coktu",
    "iflas", "kriz",
    # Criticism adjectives
    "başarısız", "basarisiz", "yetersiz", "beceriksiz", "kötü", "kotu",
    "yanlış", "yanlis", "hatalı", "hatali", "vahim", "korkunç", "korkunc",
    "rezil", "zavallı",
    # Economic criticism
    "açlık", "aclik", "yoksulluk", "işsizlik", "issizlik",
    "pahalılık", "pahalilik", "geçinemiyoruz", "yetmiyor", "bıktık",
    "yeter", "tükendik", "israf",
    # Political criticism
    "diktatör", "otoriter", "sansür", "adaletsiz", "hukuksuz",
    "eleştir", "elestir", "itiraz", "iftira", "yalan",
    # Turkish political slang used in criticism
    "algı", "algi", "sorumsuz", "sorumsuzluk", "plansız", "plansiz",
    "öngörüsüz", "ongörusuz", "vurgun", "talan", "oyun",
    # Mocking/dismissive
    "aciz", "komik", "trajikomik", "utanç", "utanc",
}


@dataclass
class RetrievalResult:
    """Single retrieval result with scores."""
    content: dict[str, Any]
    bm25_score: float = 0.0
    dense_score: float = 0.0
    rrf_score: float = 0.0
    rerank_score: float = 0.0
    final_score: float = 0.0
    is_negative: bool = False


@dataclass
class RetrievalResponse:
    """Complete retrieval response."""
    results: list[RetrievalResult]
    total_searched: int
    detected_topic: str | None
    is_criticism: bool
    retrieval_time_ms: float


def _tokenize_turkish(text: str) -> list[str]:
    """Tokenize Turkish text for BM25: lowercase, normalize, remove stopwords."""
    text_lower = text.lower()
    # Also create normalized version
    text_norm = normalize_turkish(text_lower)
    # Combine both for better matching
    combined = text_lower + " " + text_norm
    tokens = re.findall(r'\b\w+\b', combined)
    # Remove stopwords and very short tokens
    return [t for t in tokens if t not in TURKISH_STOPWORDS and len(t) > 2]


def _has_negative_sentiment(text: str) -> bool:
    """Quick check if text contains negative/critical sentiment words."""
    text_lower = text.lower()
    text_norm = normalize_turkish(text_lower)
    count = 0
    for w in NEGATIVE_WORDS:
        w_norm = normalize_turkish(w)
        if w in text_lower or w_norm in text_norm:
            count += 1
    return count >= 1  # At least 1 negative word - retriever handles ranking


def reciprocal_rank_fusion(
    rankings: list[list[int]],
    k: int = 60
) -> list[tuple]:
    """
    Reciprocal Rank Fusion - merge multiple rankings without score normalization.

    Args:
        rankings: List of ranked doc ID lists
        k: RRF constant (default 60)

    Returns:
        List of (doc_id, fused_score) sorted by score descending
    """
    fused = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            fused[doc_id] = fused.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(fused.items(), key=lambda x: x[1], reverse=True)


class HybridRetriever:
    """
    Modern hybrid retriever combining BM25 + Dense Embeddings + RRF + Reranking.

    This replaces the old SemanticRetriever with a production-grade pipeline.
    """

    # Embedding model - good multilingual support for Turkish
    EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
    # Cross-encoder for reranking
    RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(self):
        self.embed_model = None
        self.rerank_model = None

        if not TRANSFORMERS_AVAILABLE:
            logger.warning("sentence-transformers not available, using BM25 only")
            return

        try:
            self.embed_model = SentenceTransformer(self.EMBED_MODEL)
            logger.info(f"Embedding model loaded: {self.EMBED_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")

        try:
            self.rerank_model = CrossEncoder(self.RERANK_MODEL)
            logger.info(f"Reranker model loaded: {self.RERANK_MODEL}")
        except Exception as e:
            logger.warning(f"Cross-encoder not available, skipping reranking: {e}")

    def detect_topic(self, query: str) -> str | None:
        """Detect topic from query using keyword matching."""
        query_lower = query.lower()
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                return topic
        return None

    def is_criticism_query(self, query: str) -> bool:
        """Check if query explicitly asks for criticism/negative content."""
        query_lower = query.lower()
        return any(kw in query_lower for kw in CRITICISM_KEYWORDS)

    def get_topic_keywords(self, topic: str) -> list[str]:
        """Get keywords for a detected topic."""
        return TOPIC_KEYWORDS.get(topic, [])

    def retrieve(
        self,
        query: str,
        documents: list[dict[str, Any]],
        top_k: int = 20,
        is_criticism: bool = False,
    ) -> RetrievalResponse:
        """
        Retrieve relevant documents using hybrid BM25 + Dense + RRF + Reranking.

        Args:
            query: Search query
            documents: List of document dicts with 'tweet_text' or 'caption'
            top_k: Number of results to return
            is_criticism: Whether to filter for negative sentiment

        Returns:
            RetrievalResponse with ranked results
        """
        start_time = time.time()

        if not documents:
            return RetrievalResponse(
                results=[], total_searched=0,
                detected_topic=self.detect_topic(query),
                is_criticism=is_criticism,
                retrieval_time_ms=0,
            )

        # Extract texts
        all_texts = [
            doc.get("tweet_text", doc.get("caption", doc.get("text", "")))
            for doc in documents
        ]

        detected_topic = self.detect_topic(query)

        # --- Pre-filter for criticism: only search negative content ---
        if is_criticism:
            # Filter to only negative-sentiment documents BEFORE retrieval
            neg_indices = [i for i, t in enumerate(all_texts) if _has_negative_sentiment(t)]
            if not neg_indices:
                logger.info(f"No negative content found in {len(documents)} docs")
                return RetrievalResponse(
                    results=[], total_searched=len(documents),
                    detected_topic=detected_topic,
                    is_criticism=True,
                    retrieval_time_ms=(time.time() - start_time) * 1000,
                )
            # Build filtered corpus
            filtered_docs = [documents[i] for i in neg_indices]
            filtered_texts = [all_texts[i] for i in neg_indices]
            logger.info(f"Criticism pre-filter: {len(filtered_docs)}/{len(documents)} negative docs")
        else:
            filtered_docs = documents
            filtered_texts = all_texts

        texts = filtered_texts

        # --- Step 1: BM25 Sparse Retrieval ---
        bm25_ranking = self._bm25_search(query, texts)

        # --- Step 2: Dense Embedding Retrieval ---
        dense_ranking = self._dense_search(query, texts)

        # --- Step 3: RRF Fusion ---
        if bm25_ranking and dense_ranking:
            fused = reciprocal_rank_fusion([bm25_ranking, dense_ranking], k=60)
        elif dense_ranking:
            fused = [(idx, 1.0 / (60 + rank + 1)) for rank, idx in enumerate(dense_ranking)]
        elif bm25_ranking:
            fused = [(idx, 1.0 / (60 + rank + 1)) for rank, idx in enumerate(bm25_ranking)]
        else:
            return RetrievalResponse(
                results=[], total_searched=len(documents),
                detected_topic=detected_topic,
                is_criticism=is_criticism,
                retrieval_time_ms=(time.time() - start_time) * 1000,
            )

        # Take top candidates for reranking
        rerank_pool_size = min(len(fused), max(top_k * 3, 50))
        candidates = fused[:rerank_pool_size]

        # --- Step 4: Cross-Encoder Reranking ---
        if self.rerank_model and len(candidates) > 0:
            reranked = self._rerank(query, texts, candidates)
        else:
            reranked = candidates

        # --- Step 5: Build results ---
        results = []
        for doc_idx, score in reranked:
            if doc_idx >= len(filtered_docs):
                continue

            result = RetrievalResult(
                content=filtered_docs[doc_idx],
                rrf_score=dict(fused).get(doc_idx, 0.0),
                rerank_score=score,
                final_score=score,
                is_negative=is_criticism,
            )
            results.append(result)

            if len(results) >= top_k:
                break

        elapsed_ms = (time.time() - start_time) * 1000

        logger.info(
            f"Hybrid retrieval: {len(results)}/{len(documents)} docs "
            f"in {elapsed_ms:.0f}ms (topic={detected_topic}, criticism={is_criticism})"
        )

        return RetrievalResponse(
            results=results,
            total_searched=len(documents),
            detected_topic=detected_topic,
            is_criticism=is_criticism,
            retrieval_time_ms=elapsed_ms,
        )

    def _bm25_search(self, query: str, texts: list[str]) -> list[int]:
        """BM25 sparse retrieval - returns ranked doc indices."""
        try:
            # Tokenize all documents
            tokenized_corpus = [_tokenize_turkish(t) for t in texts]

            # Handle empty corpus
            if not any(tokenized_corpus):
                return []

            bm25 = BM25Okapi(tokenized_corpus)

            # Tokenize query
            query_tokens = _tokenize_turkish(query)
            if not query_tokens:
                return []

            scores = bm25.get_scores(query_tokens)

            # Return indices sorted by score (descending), filter zero scores
            ranked = np.argsort(scores)[::-1]
            return [int(idx) for idx in ranked if scores[idx] > 0][:100]

        except Exception as e:
            logger.warning(f"BM25 search failed: {e}")
            return []

    def _dense_search(self, query: str, texts: list[str]) -> list[int]:
        """Dense embedding retrieval - returns ranked doc indices."""
        if not self.embed_model:
            return []

        try:
            # Encode query and documents
            query_emb = self.embed_model.encode([query], convert_to_numpy=True)[0]
            doc_embs = self.embed_model.encode(
                texts, convert_to_numpy=True, show_progress_bar=False,
                batch_size=64
            )

            # Cosine similarity
            query_norm = query_emb / (np.linalg.norm(query_emb) + 1e-8)
            doc_norms = doc_embs / (np.linalg.norm(doc_embs, axis=1, keepdims=True) + 1e-8)
            scores = np.dot(doc_norms, query_norm)

            # Return indices sorted by score (descending), filter low scores
            ranked = np.argsort(scores)[::-1]
            return [int(idx) for idx in ranked if scores[idx] > 0.1][:100]

        except Exception as e:
            logger.warning(f"Dense search failed: {e}")
            return []

    def _rerank(
        self,
        query: str,
        texts: list[str],
        candidates: list[tuple],
    ) -> list[tuple]:
        """Cross-encoder reranking on candidate set."""
        try:
            # Build query-document pairs
            pairs = []
            indices = []
            for doc_idx, _rrf_score in candidates:
                if doc_idx < len(texts):
                    # Truncate long texts for reranker efficiency
                    text = texts[doc_idx][:512]
                    pairs.append([query, text])
                    indices.append(doc_idx)

            if not pairs:
                return candidates

            # Score all pairs
            scores = self.rerank_model.predict(pairs, show_progress_bar=False)

            # Combine RRF score (30%) with rerank score (70%)
            combined = []
            for i, (doc_idx, rrf_score) in enumerate(candidates):
                if i < len(scores):
                    # Normalize rerank score to [0, 1] range
                    rerank_norm = float(1.0 / (1.0 + np.exp(-scores[i])))  # sigmoid
                    final = 0.3 * rrf_score * 100 + 0.7 * rerank_norm
                    combined.append((doc_idx, final))
                else:
                    combined.append((doc_idx, rrf_score))

            combined.sort(key=lambda x: x[1], reverse=True)
            return combined

        except Exception as e:
            logger.warning(f"Reranking failed, using RRF scores: {e}")
            return candidates


# Singleton
_retriever_instance = None


def get_hybrid_retriever() -> HybridRetriever:
    """Get or create HybridRetriever singleton."""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = HybridRetriever()
    return _retriever_instance
