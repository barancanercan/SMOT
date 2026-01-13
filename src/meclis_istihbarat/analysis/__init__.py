"""
Analysis modulu - Embedding, Vector DB ve LLM Analiz
"""
from .embeddings import (
    create_embedding,
    create_embeddings_batch,
    embed_tweets_from_db,
    preprocess_tweet,
    get_embedding_dimension
)

from .vector_db import (
    search_similar,
    search_by_embedding,
    add_tweet,
    add_tweets_batch,
    get_user_tweets,
    get_stats,
    rebuild_index
)

from .analyzer import (
    TweetAnalyzer,
    analyze_user,
    analyze_user_with_vector_search
)

from .prompts import (
    get_prompt,
    format_tweets_for_prompt,
    SYSTEM_PROMPT
)

__all__ = [
    # Embeddings
    "create_embedding",
    "create_embeddings_batch",
    "embed_tweets_from_db",
    "preprocess_tweet",
    "get_embedding_dimension",
    # Vector DB
    "search_similar",
    "search_by_embedding",
    "add_tweet",
    "add_tweets_batch",
    "get_user_tweets",
    "get_stats",
    "rebuild_index",
    # Analyzer
    "TweetAnalyzer",
    "analyze_user",
    "analyze_user_with_vector_search",
    # Prompts
    "get_prompt",
    "format_tweets_for_prompt",
    "SYSTEM_PROMPT"
]