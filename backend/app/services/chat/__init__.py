"""
Chat Service v7 - Hybrid RAG with BM25 + Dense + RRF + Reranking
"""

__all__ = ["ChatHandler", "QueryAnalyzer", "HybridRetriever", "ResponseGenerator"]


def __getattr__(name):
    """Lazy imports to avoid loading ML models at import time."""
    if name == "ChatHandler":
        from app.services.chat.chat_handler import ChatHandler
        return ChatHandler
    if name == "QueryAnalyzer":
        from app.services.chat.query_analyzer import QueryAnalyzer
        return QueryAnalyzer
    if name == "HybridRetriever":
        from app.services.chat.hybrid_retriever import HybridRetriever
        return HybridRetriever
    if name == "ResponseGenerator":
        from app.services.chat.response_generator import ResponseGenerator
        return ResponseGenerator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
