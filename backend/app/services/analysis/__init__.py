"""
Analysis modulu - Embedding, Vector DB ve LLM Analiz
"""
from .analyzer import TweetAnalyzer, analyze_user, analyze_user_with_vector_search
from .embeddings import (
    create_embedding,
    create_embeddings_batch,
    embed_tweets_from_db,
    get_embedding_dimension,
    preprocess_tweet,
)
from .prompts import SYSTEM_PROMPT, format_tweets_for_prompt, get_prompt
from .vector_db import (
    add_tweet,
    add_tweets_batch,
    get_stats,
    get_user_tweets,
    rebuild_index,
    search_by_embedding,
    search_similar,
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
