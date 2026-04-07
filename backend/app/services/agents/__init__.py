"""
Agents Module - A-RAG (Agentic RAG) Architecture

This module implements a hierarchical retrieval system based on:
- A-RAG: Scaling Agentic RAG via Hierarchical Retrieval Interfaces
- RAGTurk: Turkish RAG Best Practices

Components:
- MetaAgent: Orchestrator that plans and coordinates sub-agents
- RetrieverAgent: Handles content retrieval (keyword/semantic search)
- ClassifierAgent: Content classification (sentiment, topic, criticism)
- SummarizerAgent: Response generation with platform-aware formatting
- ReRanker: Cross-encoder reranking to fix lost-in-the-middle problem

v5.0 - Initial implementation
"""

from app.services.agents.base import AgentResult, BaseAgent, Tool
from app.services.agents.classifier import ClassifierAgent
from app.services.agents.meta_agent import MetaAgent
from app.services.agents.reranker import ReRanker
from app.services.agents.retriever import RetrieverAgent
from app.services.agents.summarizer import SummarizerAgent

__all__ = [
    "BaseAgent",
    "Tool",
    "AgentResult",
    "MetaAgent",
    "RetrieverAgent",
    "ClassifierAgent",
    "SummarizerAgent",
    "ReRanker",
]
