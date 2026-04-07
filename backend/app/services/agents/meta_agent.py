#!/usr/bin/env python3
"""
Meta-Agent - A-RAG Orchestrator

The Meta-Agent is the central orchestrator in the A-RAG architecture.
It analyzes user queries, plans tool sequences, and coordinates sub-agents.

Based on: A-RAG: Scaling Agentic RAG via Hierarchical Retrieval Interfaces

Features:
- Query complexity analysis
- Dynamic tool sequence planning
- Sub-agent coordination
- Result aggregation
"""

import time
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.services.agents.base import BaseAgent, tool
from app.services.agents.classifier import ClassifierAgent
from app.services.agents.reranker import ReRanker
from app.services.agents.retriever import RetrieverAgent
from app.services.agents.summarizer import SummarizerAgent
from app.utils.logger import get_logger

logger = get_logger("MetaAgent")


@dataclass
class QueryPlan:
    """
    Execution plan for a query.

    Attributes:
        steps: List of (agent_name, tool_name, args) tuples
        complexity: Query complexity (simple/medium/complex)
        needs_classification: Whether content needs GPT classification
        needs_reranking: Whether to apply lost-in-the-middle fix
    """
    steps: list[tuple[str, str, dict]] = field(default_factory=list)
    complexity: str = "simple"
    needs_classification: bool = False
    needs_reranking: bool = False


@dataclass
class SessionContext:
    """
    Context for the current query session.

    Attributes:
        platform: Platform filter (twitter/instagram/both)
        party_filter: Party filter
        max_results: Maximum results to return
        include_summary: Whether to generate AI summary
    """
    platform: str = "twitter"
    party_filter: str | None = None
    max_results: int = 20
    include_summary: bool = True


class MetaAgent(BaseAgent):
    """
    A-RAG Meta-Agent: Hierarchical Retrieval Orchestrator

    Responsibilities:
    1. Analyze query to determine complexity and intent
    2. Plan optimal tool sequence
    3. Execute sub-agents in order
    4. Aggregate and format final response

    Sub-agents:
    - RetrieverAgent: Content retrieval
    - ClassifierAgent: Content classification
    - SummarizerAgent: Response generation
    - ReRanker: Lost-in-the-middle fix
    """

    # Complexity thresholds
    SIMPLE_QUERY_MAX_TOKENS = 10
    MEDIUM_QUERY_MAX_TOKENS = 30

    # Classification triggers
    CLASSIFICATION_KEYWORDS = [
        'eleştir', 'elestir', 'kritik', 'destek', 'karşı',
        'olumlu', 'olumsuz', 'analiz', 'konular', 'duygu'
    ]

    def __init__(self, db: Session):
        """Initialize meta-agent with database session."""
        super().__init__("MetaAgent")
        self.db = db

        # Initialize sub-agents
        self.retriever = RetrieverAgent(db)
        self.classifier = ClassifierAgent()
        self.summarizer = SummarizerAgent()
        self.reranker = ReRanker()

        logger.info("MetaAgent initialized with sub-agents")

    def execute(
        self,
        query: str,
        context: SessionContext = None
    ) -> dict[str, Any]:
        """
        Process a query through the A-RAG pipeline.

        Args:
            query: User's natural language query
            context: Session context with filters

        Returns:
            Dict with answer, summary, tweets, and metadata
        """
        context = context or SessionContext()
        start_time = time.time()

        # Step 1: Analyze query and create plan
        plan = self._analyze_and_plan(query, context)
        logger.info(f"Query plan: complexity={plan.complexity}, "
                   f"classification={plan.needs_classification}, "
                   f"reranking={plan.needs_reranking}")

        # Step 2: Retrieve content
        retrieval_result = self.retriever.run(
            query=query,
            platform=context.platform,
            party_filter=context.party_filter,
            max_results=context.max_results * 5 if plan.needs_reranking else context.max_results * 2
        )

        if not retrieval_result.success:
            return {
                "answer": f"İçerik araması başarısız: {retrieval_result.error}",
                "summary": {"total_found": 0},
                "tweets": [],
                "error": retrieval_result.error
            }

        contents = retrieval_result.data.get("contents", [])
        logger.info(f"Retrieved {len(contents)} content items")

        if not contents:
            content_name = self._get_content_name(context.platform)
            return {
                "answer": f"Aramanıza uygun {content_name} bulunamadı.",
                "summary": {"total_found": 0},
                "tweets": [],
            }

        # Step 3: Apply reranking if needed (lost-in-the-middle fix)
        if plan.needs_reranking and len(contents) > 20:
            rerank_result = self.reranker.run(
                query=query,
                contents=contents,
                top_k=min(context.max_results * 2, 50)
            )
            if rerank_result.success:
                contents = rerank_result.data.get("contents", contents)
                logger.info(f"Reranked to {len(contents)} items")

        # Step 4: Classify if needed
        classification_summary = {}
        if plan.needs_classification:
            classify_result = self.classifier.run(
                query=query,
                contents=contents,
                context=context
            )
            if classify_result.success:
                contents = classify_result.data.get("contents", contents)
                classification_summary = classify_result.data.get("summary", {})
                logger.info(f"Classified {len(contents)} items")

        # Step 5: Limit results
        final_contents = contents[:context.max_results]

        # Step 6: Generate summary
        if context.include_summary and final_contents:
            summary_result = self.summarizer.run(
                query=query,
                contents=final_contents,
                platform=context.platform,
                classification_summary=classification_summary
            )
            if summary_result.success:
                answer = summary_result.data.get("answer", "")
                summary = summary_result.data.get("summary", {})
            else:
                answer = self._generate_simple_answer(final_contents, context.platform)
                summary = {"total_found": len(final_contents)}
        else:
            answer = self._generate_simple_answer(final_contents, context.platform)
            summary = {"total_found": len(final_contents)}

        execution_time_ms = (time.time() - start_time) * 1000

        return {
            "answer": answer,
            "summary": summary,
            "tweets": final_contents,
            "execution_time_ms": execution_time_ms,
            "plan": {
                "complexity": plan.complexity,
                "needs_classification": plan.needs_classification,
                "needs_reranking": plan.needs_reranking
            }
        }

    def _analyze_and_plan(self, query: str, context: SessionContext) -> QueryPlan:
        """
        Analyze query and create execution plan.

        Args:
            query: User query
            context: Session context

        Returns:
            QueryPlan with execution steps
        """
        query_lower = query.lower()
        words = query_lower.split()
        word_count = len(words)

        # Determine complexity
        if word_count <= self.SIMPLE_QUERY_MAX_TOKENS:
            complexity = "simple"
        elif word_count <= self.MEDIUM_QUERY_MAX_TOKENS:
            complexity = "medium"
        else:
            complexity = "complex"

        # Check if classification needed
        needs_classification = any(
            kw in query_lower for kw in self.CLASSIFICATION_KEYWORDS
        )

        # Check if reranking needed (complex queries or large result sets)
        needs_reranking = (
            complexity in ["medium", "complex"] or
            needs_classification or
            context.max_results > 20
        )

        return QueryPlan(
            complexity=complexity,
            needs_classification=needs_classification,
            needs_reranking=needs_reranking
        )

    def _generate_simple_answer(
        self,
        contents: list[dict],
        platform: str
    ) -> str:
        """Generate a simple answer without LLM."""
        content_name = self._get_content_name(platform)
        return f"Aramanıza uygun {len(contents)} {content_name} bulundu."

    def _get_content_name(self, platform: str) -> str:
        """Get platform-aware content name."""
        names = {
            "twitter": "tweet",
            "instagram": "post",
            "both": "içerik"
        }
        return names.get(platform, "tweet")

    @tool(name="analyze_query", description="Analyze query complexity and intent")
    def analyze_query(self, query: str) -> dict[str, Any]:
        """
        Analyze a query to determine its complexity and requirements.

        Args:
            query: User's natural language query

        Returns:
            Dict with analysis results
        """
        query_lower = query.lower()
        words = query_lower.split()

        return {
            "word_count": len(words),
            "has_date_filter": any(w in query_lower for w in ['tarih', 'gün', 'ay', 'yıl']),
            "has_user_filter": '@' in query,
            "has_party_filter": any(w in query_lower for w in ['chp', 'akp', 'mhp', 'parti']),
            "is_criticism_query": any(w in query_lower for w in ['eleştir', 'kritik', 'karşı']),
            "wants_analysis": any(w in query_lower for w in ['analiz', 'konu', 'tema']),
        }

    @tool(name="coordinate_agents", description="Coordinate sub-agent execution")
    def coordinate_agents(
        self,
        query: str,
        plan: QueryPlan,
        context: SessionContext
    ) -> dict[str, Any]:
        """
        Execute the planned sequence of sub-agents.

        Args:
            query: User query
            plan: Execution plan
            context: Session context

        Returns:
            Aggregated results from all agents
        """
        # This is the main execution flow - implemented in execute()
        return self.execute(query, context)
