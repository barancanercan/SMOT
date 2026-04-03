#!/usr/bin/env python3
# UPDATED: 2026-04-03 - Fixed output format, removed semantic scores
"""
Chat Handler v6 - Modern RAG with Semantic Retrieval

2026 Architecture (based on Anthropic Contextual Retrieval research):
1. Query Reasoner: Political context understanding (AKP=hükümet=iktidar)
2. Semantic Retriever: Embedding-based search (NOT LLM classification!)
3. Single LLM call: Only for final response generation

Key insight: DON'T use LLM to classify 300 tweets.
Instead: Use embeddings for retrieval, LLM for response.

Performance:
- Old: 300 tweets × GPT-4o batches = 3 minutes, 0 results
- New: 300 tweets × embeddings = 1 second, accurate results

References:
- https://www.anthropic.com/news/contextual-retrieval
- https://superlinked.com/vectorhub/articles/optimizing-rag-with-hybrid-search-reranking
"""

import re
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.services.chat.intent_parser import IntentParser, ParsedIntent
from app.services.chat.response_generator import ResponseGenerator, ChatResponse
from app.services.chat.turkish_nlp import (
    expand_keywords,
    calculate_keyword_score,
)
from app.services.chat.semantic_search import semantic_search
from app.services.chat.query_cache import (
    get_intent_cache,
    set_intent_cache,
    get_response_cache,
    set_response_cache,
    get_cache_stats
)
from app.services.chat.query_reasoner import get_reasoner, ReasonedQuery
from app.services.chat.semantic_retriever import get_semantic_retriever, CRITICISM_CONCEPTS, TOPIC_CONCEPTS
from app.core.models import Tweet, Councilor, InstagramPost
from app.core.constants import normalize_party_name
from app.utils.logger import get_logger

logger = get_logger("ChatHandler")

# =============================================================================
# SEARCH STOPWORDS - Words that dilute search results
# =============================================================================
SEARCH_STOPWORDS = {
    # Meta words that don't add search value
    "tweetler", "tweet", "tweetleri", "tweetlerin",
    "paylaşım", "paylaşımlar", "paylaşımları",
    "içerik", "içerikler", "içerikleri",
    "hakkında", "hakkindaki", "ilgili",
    "bilgi", "bilgiler", "bilgileri",
    # Question words
    "nasıl", "neden", "nedir", "ne", "kim",
    # Generic verbs
    "göster", "listele", "bul", "ara", "getir",
    # Very common words
    "var", "yok", "olan", "olmayan",
    "çok", "az", "fazla", "büyük", "küçük",
}


# =============================================================================
# PARTY DETECTION PATTERNS
# =============================================================================

PARTY_PATTERNS = {
    "AK Parti": [
        r'\b(akp|ak\s*parti|akpartili|akp\'li)\b',
        r'\b(iktidar|hükümet|hukumet)\b',
        r'\b(erdoğan|erdogan)\b',
    ],
    "CHP": [
        r'\b(chp|chp\'li|chpli)\b',
        r'\b(kılıçdaroğlu|kilicdaroglu|özgür\s*özel|ozgur\s*ozel)\b',
    ],
    "MHP": [
        r'\b(mhp|mhp\'li|mhpli)\b',
        r'\b(bahçeli|bahceli)\b',
    ],
    "İYİ Parti": [
        r'\b(iyi\s*parti|iyip|iyi\'li)\b',
        r'\b(akşener|aksener)\b',
    ],
    "DEM Parti": [
        r'\b(dem\s*parti|hdp|dem\'li)\b',
    ],
}

# Karşı parti mapping - bir parti için karşı tarafı belirler
OPPOSITE_PARTIES = {
    "CHP": "AK Parti",
    "AK Parti": "CHP",
    "AKP": "CHP",
    "MHP": "CHP",
    "BBP": "CHP",
    "İYİ Parti": "AK Parti",
    "Yeniden Refah Partisi": "CHP",
    "YRP": "CHP",
    "Bağımsız": None,
    "BAGIMSIZ": None,
}


@dataclass
class QueryAnalysis:
    """Analysis of user query"""
    source_party: Optional[str]  # Party whose tweets we're searching
    target_party: Optional[str]  # Party being criticized/discussed
    is_criticism: bool
    topic: Optional[str]
    original_query: str


@dataclass
class ChatQueryResult:
    """Complete result of a chat query"""
    query: str
    answer: str
    summary: Dict[str, Any] = field(default_factory=dict)
    tweets: List[Dict] = field(default_factory=list)
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    execution_time_ms: float = 0.0
    cached: bool = False
    intent_type: str = "search_topic"


class ChatHandler:
    """
    Main handler for Chat with Tweets functionality.

    v6 Architecture (2026 Best Practices):
    1. Query Reasoner: Political context understanding
    2. Semantic Retriever: Embedding-based search (fast!)
    3. Single LLM call for response (no batch classification)

    Why this is better:
    - Old: 300 tweets × GPT-4o = 3 min, expensive, inaccurate
    - New: 300 tweets × embeddings = 1 sec, cheap, accurate
    """

    MAX_RESULTS = 50
    DEFAULT_MAX_RESULTS = 20
    SEMANTIC_POOL_SIZE = 300  # More content for semantic retrieval

    def _determine_intent_ensemble(
        self,
        query: str,
        reasoned: Optional[ReasonedQuery],
        parsed: ParsedIntent
    ) -> tuple[str, float]:
        """
        Ensemble intent detection - Keywords most trusted, LLM least trusted.

        Returns:
            tuple of (intent_type, confidence)
        """
        query_lower = query.lower()
        score = 0.0

        # KEYWORDS - Most reliable signal (50% weight)
        criticism_keywords = [
            "eleştiri", "elestiri", "eleştir", "elestir",
            "başarısız", "basarisiz", "berbat", "rezalet",
            "skandal", "felaket", "kötü", "kotu",
            "karşı", "karsi", "protesto", "tepki"
        ]
        if any(kw in query_lower for kw in criticism_keywords):
            score += 0.5

        # RULE-BASED - Secondary signal (30% weight)
        if parsed.filters.get('is_criticism'):
            score += 0.3

        # LLM - Only for confirmation (20% weight)
        if reasoned and reasoned.intent == "criticism" and reasoned.confidence > 0.8:
            score += 0.2

        intent = "criticism" if score >= 0.5 else "information"
        confidence = min(score + 0.3, 1.0)  # Base confidence

        return intent, confidence

    def __init__(self, db: Session):
        """Initialize chat handler with modern RAG components."""
        self.db = db
        self.intent_parser = IntentParser()
        self.response_generator = ResponseGenerator()
        self.query_reasoner = get_reasoner()
        self.semantic_retriever = get_semantic_retriever()
        logger.info("ChatHandler v6 initialized with semantic retrieval")

    def process_query(
        self,
        query: str,
        max_results: int = DEFAULT_MAX_RESULTS,
        include_summary: bool = True,
        party_filter: Optional[str] = None,
        platform: str = "twitter"
    ) -> ChatQueryResult:
        """
        Process a natural language query with optional party filter.

        Args:
            query: Turkish natural language query
            max_results: Maximum number of tweets to return
            include_summary: Whether to include AI summary
            party_filter: Party filter from UI (source party)
            platform: Platform to search (twitter, instagram, both)
        """
        self.current_platform = platform
        start_time = time.time()

        if not query or len(query.strip()) < 3:
            return ChatQueryResult(
                query=query,
                answer="Lütfen en az 3 karakterlik bir soru girin.",
                summary={"total_found": 0},
                confidence_score=0.0,
                execution_time_ms=0.0
            )

        # Check for detailed analysis request
        query_lower = query.lower()
        wants_detailed = any(kw in query_lower for kw in [
            'detayli', 'detaylı', 'acikla', 'açıkla', 'kapsamli', 'kapsamlı'
        ])
        if wants_detailed and max_results < 30:
            max_results = 30

        max_results = min(max_results, self.MAX_RESULTS)

        try:
            # Check response cache first
            cache_filters = {"party": party_filter, "platform": platform}
            cached_response = get_response_cache(query, cache_filters, platform)
            if cached_response:
                logger.info("Using cached response")
                execution_time_ms = (time.time() - start_time) * 1000
                return ChatQueryResult(
                    query=query,
                    answer=cached_response.get("answer", ""),
                    summary=cached_response.get("summary", {}),
                    tweets=cached_response.get("tweets", []),
                    filters_applied=cached_response.get("filters_applied", {}),
                    confidence_score=cached_response.get("confidence_score", 0.8),
                    execution_time_ms=execution_time_ms,
                    cached=True,
                    intent_type=cached_response.get("intent_type", "search_topic")
                )

            # Normalize party_filter - treat "None", "", None all as no filter
            if party_filter in (None, "", "None", "null", "undefined"):
                party_filter = None

            # Step 0: TOPIC DETECTION FIRST (before intent)
            # Topic detection drives keyword selection for better relevance
            detected_topic = self.semantic_retriever.detect_topic(query)
            topic_keywords = []
            if detected_topic:
                topic_keywords = TOPIC_CONCEPTS.get(detected_topic, {}).get("keywords", [])[:5]
                logger.info(f"Topic detected FIRST: {detected_topic}, keywords: {topic_keywords}")

            # Step 1: Query Reasoning - "Dusunme" katmani
            # GPT-4o sorguyu politik baglamda analiz eder
            logger.info(f"Party filter from UI: '{party_filter}'")
            reasoned = self.query_reasoner.reason(query, party_filter, platform)
            logger.info(f"QueryReasoner dusundu: {reasoned.reasoning[:200]}...")
            logger.info(f"Hedef parti: {reasoned.target_party}, Niyet: {reasoned.intent}")
            logger.info(f"Arama terimleri: {reasoned.search_terms[:5]}")

            # Step 2: Analyze query to detect parties and intent
            # QueryReasoner sonuclarini kullan
            query_analysis = self._analyze_query(query, party_filter)
            # Add detected topic to query_analysis
            if detected_topic and not query_analysis.topic:
                query_analysis.topic = detected_topic

            # QueryReasoner'dan gelen bilgilerle zenginlestir
            if reasoned.target_party and not query_analysis.target_party:
                query_analysis.target_party = reasoned.target_party
            if reasoned.intent == "criticism" and not query_analysis.is_criticism:
                query_analysis.is_criticism = True

            logger.info(f"Query analysis: source={query_analysis.source_party}, "
                       f"target={query_analysis.target_party}, topic={query_analysis.topic}, criticism={query_analysis.is_criticism}")

            # Step 3: Parse intent (with cache) - topic context already available
            cached_intent = get_intent_cache(query)
            if cached_intent:
                parsed_intent = ParsedIntent(
                    intent_type=cached_intent.get("intent_type", "search_topic"),
                    filters=cached_intent.get("filters", {}),
                    semantic_query=cached_intent.get("semantic_query", ""),
                    confidence=cached_intent.get("confidence", 0.7)
                )
                logger.info(f"Using cached intent: {parsed_intent.intent_type}")
            else:
                parsed_intent = self.intent_parser.parse(query)
                # Cache the intent
                set_intent_cache(query, {
                    "intent_type": parsed_intent.intent_type,
                    "filters": parsed_intent.filters,
                    "semantic_query": parsed_intent.semantic_query,
                    "confidence": parsed_intent.confidence
                })
            logger.info(f"Intent: {parsed_intent.intent_type}, confidence: {parsed_intent.confidence}")

            # Override party from UI filter
            # IMPORTANT: Clear cached party if UI has no filter selected
            if party_filter:
                parsed_intent.filters['party'] = party_filter
            elif query_analysis.source_party:
                parsed_intent.filters['party'] = query_analysis.source_party
            else:
                # No party filter - clear any cached party
                parsed_intent.filters.pop('party', None)

            # Merge keywords: Topic keywords (highest priority) + QueryReasoner + existing
            existing_keywords = parsed_intent.filters.get('keywords', [])
            reasoner_terms = reasoned.search_terms or []
            # Topic keywords take priority (detected in Step 0)
            if topic_keywords:
                merged_keywords = list(set(topic_keywords + existing_keywords + reasoner_terms))
                parsed_intent.filters['detected_topic'] = detected_topic
            else:
                merged_keywords = list(set(existing_keywords + reasoner_terms))

            # CRITICAL: Filter out stopwords that dilute search results
            if merged_keywords:
                filtered_keywords = [
                    kw for kw in merged_keywords
                    if kw.lower() not in SEARCH_STOPWORDS and len(kw) > 2
                ]
                # If all keywords were filtered, keep topic keywords at minimum
                if not filtered_keywords and topic_keywords:
                    filtered_keywords = topic_keywords[:3]
                parsed_intent.filters['keywords'] = filtered_keywords
                logger.info(f"Filtered keywords (stopwords removed): {filtered_keywords[:10]}")

            # Update semantic query with enhanced version
            if reasoned.enhanced_query:
                parsed_intent.semantic_query = reasoned.enhanced_query

            # Step 3: Search and classify
            # Use ensemble intent detection - keywords most trusted, LLM least trusted
            ensemble_intent, ensemble_confidence = self._determine_intent_ensemble(
                query=query,
                reasoned=reasoned,
                parsed=parsed_intent
            )
            is_criticism_query = ensemble_intent == "criticism"
            logger.info(f"Ensemble intent: {ensemble_intent} (confidence: {ensemble_confidence:.2f})")

            if is_criticism_query:
                logger.info(f"Criticism mode: ensemble_confidence={ensemble_confidence:.2f}")
                tweets, classification_summary = self._search_with_classification(
                    query_analysis=query_analysis,
                    parsed_intent=parsed_intent,
                    max_results=max_results,
                    reasoned_query=reasoned
                )

                if tweets:
                    answer = self._generate_formatted_answer(
                        tweets=tweets,
                        summary=classification_summary,
                        query_analysis=query_analysis
                    )
                    response = ChatResponse(
                        answer=answer,
                        summary=classification_summary,
                        confidence_score=0.85
                    )
                else:
                    # Platform-aware "not found" message with Turkish accusative suffix
                    not_found_term = {
                        "twitter": "tweeti",
                        "instagram": "postu",
                        "both": "içeriği"
                    }.get(platform, "içeriği")
                    response = ChatResponse(
                        answer=f"Belirtilen kriterlere uygun eleştiri {not_found_term} bulunamadı.",
                        summary={"total_found": 0}
                    )
            else:
                # Regular search - topic already detected in Step 0 and keywords merged
                # No need to detect again - use parsed_intent.filters which has topic_keywords

                tweets = self._search_tweets(parsed_intent, max_results)
                search_topic = parsed_intent.filters.get('detected_topic')

                # If topic was detected but very few results found, warn user
                if search_topic and len(tweets) < 3:
                    topic_name_tr = {
                        "ekonomi": "ekonomi",
                        "belediye": "belediye hizmetleri",
                        "ulaşım": "ulaşım",
                        "eğitim": "eğitim",
                        "sağlık": "sağlık"
                    }.get(search_topic, search_topic)

                    party_note = f" ({party_filter} partisinde)" if party_filter else ""
                    response = ChatResponse(
                        answer=f"**{topic_name_tr.capitalize()}** konusunda{party_note} yeterli icerik bulunamadi ({len(tweets)} sonuc).\n\nBu konuda daha fazla icerik icin parti filtresini kaldirmayi veya farkli anahtar kelimeler denemeyi onerebilirim.",
                        summary={"total_found": len(tweets), "topic": search_topic}
                    )
                    execution_time_ms = (time.time() - start_time) * 1000
                    return ChatQueryResult(
                        query=query,
                        answer=response.answer,
                        summary=response.summary,
                        tweets=tweets,
                        filters_applied=parsed_intent.filters,
                        confidence_score=0.5,
                        execution_time_ms=execution_time_ms,
                        cached=False,
                        intent_type=parsed_intent.intent_type
                    )

                logger.info(f"Found {len(tweets)} tweets")

                # Get platform-aware content name
                content_name = self._get_content_name(platform)
                content_name_singular = self._get_content_name_singular(platform)

                if include_summary and tweets:
                    response = self.response_generator.generate(
                        query=query,
                        tweets=tweets,
                        intent_type=parsed_intent.intent_type,
                        username=parsed_intent.filters.get('username'),
                        platform=platform
                    )
                else:
                    if not tweets:
                        response = ChatResponse(
                            answer=f"Aramanıza uygun {content_name_singular} bulunamadı.",
                            summary={"total_found": 0}
                        )
                    else:
                        response = ChatResponse(
                            answer=f"{len(tweets)} {content_name_singular} bulundu.",
                            summary={"total_found": len(tweets)}
                        )

            execution_time_ms = (time.time() - start_time) * 1000

            result = ChatQueryResult(
                query=query,
                answer=response.answer,
                summary=response.summary,
                tweets=tweets,
                filters_applied={
                    **parsed_intent.filters,
                    "source_party": query_analysis.source_party,
                    "target_party": query_analysis.target_party
                },
                confidence_score=response.confidence_score,
                execution_time_ms=execution_time_ms,
                cached=False,
                intent_type=parsed_intent.intent_type
            )

            # Cache the response (only if we have results)
            if tweets and len(tweets) > 0:
                cache_data = {
                    "answer": response.answer,
                    "summary": response.summary,
                    "tweets": tweets[:20],  # Cache limited tweets
                    "filters_applied": result.filters_applied,
                    "confidence_score": result.confidence_score,
                    "intent_type": result.intent_type
                }
                set_response_cache(query, cache_data, cache_filters, platform)
                logger.info(f"Response cached for: {query[:30]}...")

            return result

        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            execution_time_ms = (time.time() - start_time) * 1000

            return ChatQueryResult(
                query=query,
                answer=f"Sorgu işlenirken hata oluştu: {str(e)}",
                summary={"total_found": 0, "error": str(e)},
                confidence_score=0.0,
                execution_time_ms=execution_time_ms
            )

    def _analyze_query(self, query: str, party_filter: Optional[str]) -> QueryAnalysis:
        """
        Analyze query to detect source party, target party, and intent.

        Examples:
        - "CHP'lilerin hükümet eleştirisi" -> source=CHP, target=AK Parti
        - "AKP'lilerin CHP'yi eleştirdiği" -> source=AK Parti, target=CHP
        - "Ekonomi hakkında tweetler" -> source=None, target=None, topic=ekonomi
        """
        query_lower = query.lower()

        # Detect if this is a criticism query
        criticism_keywords = [
            'eleştir', 'elestir', 'kritik', 'suçla', 'sucla',
            'karşı', 'karsi', 'saldır', 'saldir', 'hedef al'
        ]
        is_criticism = any(kw in query_lower for kw in criticism_keywords)

        # Detect source party (who is tweeting)
        source_party = party_filter  # Use UI filter if provided

        if not source_party:
            # Try to detect from query patterns like "CHP'lilerin", "AKP'liler"
            source_patterns = [
                (r"(chp)'?l[iı]ler", "CHP"),
                (r"(akp|ak\s*parti)'?l[iı]ler", "AK Parti"),
                (r"(mhp)'?l[iı]ler", "MHP"),
                (r"(iyi\s*parti)'?l[iı]ler", "İYİ Parti"),
                (r"(dem\s*parti|hdp)'?l[iı]ler", "DEM Parti"),
            ]
            for pattern, party in source_patterns:
                if re.search(pattern, query_lower):
                    source_party = party
                    break

        # Detect target party (who is being criticized)
        target_party = None

        if is_criticism:
            # Check what's being criticized
            if any(kw in query_lower for kw in ['hükümet', 'hukumet', 'iktidar', 'akp', 'ak parti', 'erdoğan', 'erdogan']):
                target_party = "hükümet"
            elif any(kw in query_lower for kw in ['chp', 'muhalefet', 'mansur', 'imamoğlu', 'imamoglu']):
                target_party = "CHP"
            elif any(kw in query_lower for kw in ['mhp', 'bahçeli', 'bahceli']):
                target_party = "MHP"

        # Detect topic
        topic = None
        topic_patterns = {
            "ekonomi": ["ekonomi", "enflasyon", "zam", "fiyat", "maaş", "asgari"],
            "eğitim": ["eğitim", "egitim", "okul", "öğretmen", "ogretmen"],
            "sağlık": ["sağlık", "saglik", "hastane", "doktor"],
            "ulaşım": ["ulaşım", "ulasim", "metro", "trafik", "otobüs"],
            "belediye": ["belediye", "şehir", "park", "altyapı"],
        }
        for topic_name, keywords in topic_patterns.items():
            if any(kw in query_lower for kw in keywords):
                topic = topic_name
                break

        return QueryAnalysis(
            source_party=source_party,
            target_party=target_party,
            is_criticism=is_criticism,
            topic=topic,
            original_query=query
        )

    def _search_with_classification(
        self,
        query_analysis: QueryAnalysis,
        parsed_intent: ParsedIntent,
        max_results: int,
        reasoned_query: Optional[ReasonedQuery] = None
    ) -> Tuple[List[Dict], Dict]:
        """
        Search content using SEMANTIC RETRIEVAL (not LLM classification!).

        Modern RAG Architecture (2026):
        - Use embeddings for retrieval (fast, accurate)
        - Don't send 300 tweets to GPT-4o (slow, expensive, inaccurate)

        Args:
            query_analysis: Basic query analysis
            parsed_intent: Parsed intent from IntentParser
            max_results: Maximum results to return
            reasoned_query: Enhanced query from QueryReasoner (optional)
        """
        filters = parsed_intent.filters.copy()
        platform = getattr(self, 'current_platform', 'twitter')
        source_party = query_analysis.source_party or filters.get('party')

        # Use reasoned query's target party if available
        target_party = query_analysis.target_party
        if reasoned_query and reasoned_query.target_party:
            target_party = reasoned_query.target_party
            logger.info(f"Using reasoned target party: {target_party}")

        # UPDATED: Detect topic and add PRIMARY keywords for STRICT SQL filtering
        # Use fewer but more specific keywords to ensure relevant content
        topic = self.semantic_retriever.detect_topic(query_analysis.original_query)
        if topic:
            # Use ONLY the primary topic keywords (first 3-4) for strict filtering
            topic_keywords = TOPIC_CONCEPTS.get(topic, {}).get("keywords", [])[:4]
            # Replace existing keywords with topic-specific ones for accuracy
            filters['keywords'] = topic_keywords
            filters['strict_keywords'] = True  # Flag for AND-like filtering
            logger.info(f"Topic detected: {topic}, STRICT keywords: {filters['keywords']}")
        else:
            # No topic detected - keep existing keywords if any, otherwise clear
            if not filters.get('keywords'):
                filters.pop('keywords', None)
                logger.info("No topic detected, no keyword pre-filtering")

        # Get party members for filtering
        party_usernames = None
        if source_party:
            party_usernames = self._get_party_members(source_party)
            if not party_usernames:
                logger.warning(f"No members found for party: {source_party}")
                return [], {}
            logger.info(f"Filtering by party {source_party}: {len(party_usernames)} members")

        # Get content pool for semantic search
        all_content = []
        sample_size = self.SEMANTIC_POOL_SIZE

        # Search Twitter
        if platform in ["twitter", "both"]:
            twitter_content = self._get_twitter_content(
                party_usernames=party_usernames,
                filters=filters,
                limit=sample_size if platform == "twitter" else sample_size // 2
            )
            all_content.extend(twitter_content)
            logger.info(f"📥 Got {len(twitter_content)} tweets for semantic search")

        # Search Instagram
        if platform in ["instagram", "both"]:
            instagram_content = self._get_instagram_content(
                party_usernames=party_usernames,
                filters=filters,
                limit=sample_size if platform == "instagram" else sample_size // 2
            )
            all_content.extend(instagram_content)
            logger.info(f"📥 Got {len(instagram_content)} Instagram posts for semantic search")

        if not all_content:
            return [], {}

        logger.info(f"🔍 Semantic retrieval on {len(all_content)} items (platform: {platform})")

        # Determine target concepts for semantic matching
        # IMPORTANT: Topic alone does NOT mean criticism
        # Only add criticism concepts if query explicitly asks for criticism
        target_concepts = []

        # Check if this is explicitly a criticism query
        query_lower = query_analysis.original_query.lower()
        criticism_keywords = [
            "eleştiri", "elestiri", "eleştiren", "elestiren", "eleştir", "elestir",
            "başarısız", "basarisiz", "kötü", "kotu", "berbat", "rezalet",
            "karşı", "karsi", "tepki", "protesto"
        ]
        is_explicit_criticism = any(kw in query_lower for kw in criticism_keywords)

        if target_party and is_explicit_criticism:
            target_lower = target_party.lower()
            if target_lower in ["hükümet", "hukumet", "iktidar", "akp", "ak parti"]:
                target_concepts.append("hükümet_eleştirisi")
            elif target_lower in ["chp", "muhalefet"]:
                target_concepts.append("chp_eleştirisi")

        # Topic-based concepts (neutral, NOT criticism)
        if query_analysis.topic in ["belediye", "ulaşım", "ulasim"]:
            target_concepts.append("belediye_hizmeti")

        # Note: ekonomi topic does NOT automatically add hükümet_eleştirisi
        # unless explicit criticism keywords are present

        # Also let retriever detect concepts from query
        auto_concepts = self.semantic_retriever.detect_query_concepts(query_analysis.original_query)
        target_concepts = list(set(target_concepts + auto_concepts))

        logger.info(f"🎯 Target concepts: {target_concepts}")

        # Build search query from reasoner insights
        search_query = query_analysis.original_query
        if reasoned_query and reasoned_query.enhanced_query:
            search_query = reasoned_query.enhanced_query
        if reasoned_query and reasoned_query.search_terms:
            search_query += " " + " ".join(reasoned_query.search_terms[:5])

        logger.info(f"🔎 Search query: {search_query[:100]}...")

        # SEMANTIC RETRIEVAL - The key step!
        # This uses embeddings, NOT LLM classification
        # min_score=0.1 is low to ensure we get results (will rank by score anyway)
        retrieval_result = self.semantic_retriever.retrieve(
            query=search_query,
            documents=all_content,
            target_concepts=target_concepts if target_concepts else None,
            top_k=max_results * 2,  # Get more, filter later
            min_score=0.1  # Low threshold - let ranking do the work
        )

        logger.info(f"✅ Semantic retrieval: {len(retrieval_result.results)} results in {retrieval_result.retrieval_time_ms:.0f}ms")

        # Convert retrieval results to expected format
        matches = []
        topics = set()

        # Human-readable topic names
        TOPIC_DISPLAY_NAMES = {
            "hükümet_eleştirisi": "Hükümet Eleştirisi",
            "chp_eleştirisi": "CHP Eleştirisi",
            "ekonomi": "Ekonomi",
            "belediye": "Belediye",
            "ulaşım": "Ulaşım",
            "eğitim": "Eğitim",
            "sağlık": "Sağlık",
            "Genel": "Genel",
        }

        for result in retrieval_result.results[:max_results]:
            tweet = result.content.copy()
            tweet["relevance_score"] = result.combined_score

            # Transform topic names to human-readable format
            if result.matched_concepts:
                readable_topics = [TOPIC_DISPLAY_NAMES.get(c, c.replace("_", " ").title()) for c in result.matched_concepts]
                tweet["criticism_topic"] = ", ".join(readable_topics)
            else:
                tweet["criticism_topic"] = ""

            # Don't show any technical info to users
            tweet["criticism_explanation"] = ""
            matches.append(tweet)
            topics.update(result.matched_concepts)

        # Convert topics to human-readable for summary
        readable_summary_topics = [TOPIC_DISPLAY_NAMES.get(t, t.replace("_", " ").title()) for t in list(topics)[:5]]

        summary = {
            "total_found": len(matches),
            "total_analyzed": retrieval_result.total_searched,
            "top_topics": readable_summary_topics,
            "sentiment": "olumsuz" if query_analysis.is_criticism else "notr",
            "most_active_users": self._get_most_active_users(matches),
            "date_range": self._get_date_range(matches),
            "retrieval_time_ms": retrieval_result.retrieval_time_ms
        }

        # Sort by engagement (likes + retweets) descending - always show most engaging first
        matches.sort(key=lambda t: (t.get("likes", 0) + t.get("retweets", 0)), reverse=True)

        return matches, summary

    def _get_content_name(self, platform: str = None, plural: bool = True) -> str:
        """
        Get platform-aware content name.

        Args:
            platform: Platform type (twitter, instagram, both)
            plural: Use plural form

        Returns:
            Content name in Turkish
        """
        platform = platform or getattr(self, 'current_platform', 'twitter')
        if platform == "instagram":
            return "postlar" if plural else "post"
        elif platform == "both":
            return "içerikler" if plural else "içerik"
        else:
            return "tweetler" if plural else "tweet"

    def _get_content_name_singular(self, platform: str = None) -> str:
        """Get singular content name."""
        return self._get_content_name(platform, plural=False)

    def _generate_formatted_answer(
        self,
        tweets: List[Dict],
        summary: Dict,
        query_analysis: QueryAnalysis
    ) -> str:
        """
        Generate a concise analysis summary.
        NO tweet examples - they are shown separately below.
        Focus on insights and statistics only.
        """
        if not tweets:
            return "Belirtilen kriterlere uygun içerik bulunamadı."

        total = summary.get("total_found", len(tweets))
        total_analyzed = summary.get("total_analyzed", 0)

        # Determine context
        source = query_analysis.source_party or "Tüm partiler"
        target = query_analysis.target_party

        # Calculate statistics
        total_likes = sum(t.get("likes", 0) for t in tweets)
        total_retweets = sum(t.get("retweets", 0) for t in tweets)
        avg_engagement = (total_likes + total_retweets) / len(tweets) if tweets else 0

        # Find most active users
        user_counts = {}
        for t in tweets:
            u = t.get("username", "")
            user_counts[u] = user_counts.get(u, 0) + 1
        top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:3]

        # Build concise answer
        lines = []

        if query_analysis.is_criticism and target:
            # Criticism analysis header - NO TWEETS IN ANSWER!
            lines.append(f"📊 **{total_analyzed}** içerik analiz edildi, **{total}** eşleşme bulundu.")
        else:
            lines.append(f"**{total}** sonuç bulundu.")

        lines.append("")

        # Key metrics in one line
        if total_likes > 0 or total_retweets > 0:
            lines.append(f"📊 **Toplam etkileşim:** {total_likes:,} beğeni, {total_retweets:,} paylaşım")

        # Top contributors
        if top_users and len(top_users) > 1:
            contributors = ", ".join([f"@{u[0]} ({u[1]})" for u in top_users])
            lines.append(f"👥 **En aktif:** {contributors}")

        # Date range if available
        date_range = summary.get("date_range")
        if date_range:
            lines.append(f"📅 **Tarih aralığı:** {date_range}")

        return "\n".join(lines)

    def _search_tweets(
        self,
        parsed_intent: ParsedIntent,
        max_results: int
    ) -> List[Dict]:
        """
        Search tweets using hybrid approach: SQL filters + Semantic search.

        Flow:
        1. SQL filters narrow down candidates (date, user, party)
        2. Keyword expansion with Turkish NLP
        3. Semantic search ranks by relevance
        """
        filters = parsed_intent.filters
        original_query = parsed_intent.semantic_query or ""

        # Step 1: SQL pre-filtering - get larger pool for semantic ranking
        query = self.db.query(Tweet).filter(Tweet.is_retweet == False)

        if filters.get('username'):
            query = query.filter(Tweet.username == filters['username'])

        if filters.get('party'):
            party_usernames = self._get_party_members(filters['party'])
            if party_usernames:
                query = query.filter(Tweet.username.in_(party_usernames))

        if filters.get('start_date'):
            query = query.filter(Tweet.tweet_date >= filters['start_date'])
        if filters.get('end_date'):
            query = query.filter(Tweet.tweet_date <= filters['end_date'])

        # Step 2: Expand keywords using Turkish NLP
        keywords = filters.get('keywords', [])
        expanded_keywords = expand_keywords(keywords) if keywords else []
        logger.info(f"Keywords expanded: {keywords} -> {len(expanded_keywords)} terms")

        # Broader keyword filter using expanded terms (OR logic)
        if expanded_keywords:
            from sqlalchemy import or_
            # Use first 15 expanded keywords for SQL filter
            sql_keywords = expanded_keywords[:15]
            keyword_filters = [Tweet.tweet_text.ilike(f"%{kw}%") for kw in sql_keywords]
            query = query.filter(or_(*keyword_filters))

        # Get larger pool for semantic ranking
        pool_size = max(self.SEMANTIC_POOL_SIZE, max_results * 3)
        query = query.order_by(Tweet.likes.desc(), Tweet.tweet_date.desc())
        tweets_orm = query.limit(pool_size).all()

        if not tweets_orm:
            logger.info("No tweets found in SQL query")
            return []

        logger.info(f"SQL returned {len(tweets_orm)} tweets for semantic ranking")

        # Step 3: Convert to dict format
        candidates = []
        for t in tweets_orm:
            councilor = self.db.query(Councilor).filter(
                Councilor.username == t.username
            ).first()

            candidates.append({
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
                "is_retweet": t.is_retweet,
                "platform": "twitter",
            })

        # Step 4: Semantic search and ranking
        if keywords or original_query:
            search_query = original_query if original_query else " ".join(keywords)
            results = semantic_search(
                items=candidates,
                query=search_query,
                keywords=keywords,
                max_results=max_results
            )
            logger.info(f"Semantic search returned {len(results)} ranked results")
            return results
        else:
            # No semantic query - return by engagement
            return candidates[:max_results]

    def _get_twitter_content(
        self,
        party_usernames: Optional[List[str]],
        filters: Dict,
        limit: int
    ) -> List[Dict]:
        """
        Get Twitter content for classification with semantic pre-ranking.

        Uses Turkish NLP for better keyword matching.
        UPDATED: Supports strict_keywords mode for topic-based searches.
        """
        query = self.db.query(Tweet).filter(Tweet.is_retweet == False)

        if party_usernames:
            query = query.filter(Tweet.username.in_(party_usernames))

        if filters.get('start_date'):
            query = query.filter(Tweet.tweet_date >= filters['start_date'])
        if filters.get('end_date'):
            query = query.filter(Tweet.tweet_date <= filters['end_date'])

        # Keyword filtering - STRICT or LOOSE mode
        keywords = filters.get('keywords', [])
        if keywords:
            from sqlalchemy import or_, and_
            strict_mode = filters.get('strict_keywords', False)

            if strict_mode:
                # STRICT MODE: Tweet must contain at least one PRIMARY keyword
                # Use original keywords without expansion for accuracy
                primary_keywords = keywords[:3]  # Top 3 most important
                keyword_filters = [Tweet.tweet_text.ilike(f"%{kw}%") for kw in primary_keywords]
                query = query.filter(or_(*keyword_filters))
                logger.info(f"STRICT keyword filter: {primary_keywords}")
            else:
                # LOOSE MODE: Use expanded keywords (original behavior)
                expanded = expand_keywords(keywords)[:15]
                keyword_filters = [Tweet.tweet_text.ilike(f"%{kw}%") for kw in expanded]
                query = query.filter(or_(*keyword_filters))

        query = query.order_by(Tweet.likes.desc(), Tweet.tweet_date.desc())
        tweets_orm = query.limit(limit * 2).all()  # Get more for ranking

        content = []
        for t in tweets_orm:
            councilor = self.db.query(Councilor).filter(
                Councilor.username == t.username
            ).first()

            content.append({
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
            })

        # Rank by keyword relevance if we have keywords
        if keywords and content:
            for item in content:
                item["keyword_score"] = calculate_keyword_score(
                    item.get("tweet_text", ""),
                    keywords
                )
            content.sort(key=lambda x: x.get("keyword_score", 0), reverse=True)

        return content[:limit]

    def _get_instagram_content(
        self,
        party_usernames: Optional[List[str]],
        filters: Dict,
        limit: int
    ) -> List[Dict]:
        """
        Get Instagram content for classification with semantic pre-ranking.

        Uses Turkish NLP for better keyword matching on captions.
        UPDATED: Supports strict_keywords mode for topic-based searches.
        """
        query = self.db.query(InstagramPost)

        if party_usernames:
            query = query.filter(InstagramPost.username.in_(party_usernames))

        if filters.get('start_date'):
            query = query.filter(InstagramPost.post_date >= filters['start_date'])
        if filters.get('end_date'):
            query = query.filter(InstagramPost.post_date <= filters['end_date'])

        # Keyword filtering - STRICT or LOOSE mode
        keywords = filters.get('keywords', [])
        if keywords:
            from sqlalchemy import or_
            strict_mode = filters.get('strict_keywords', False)

            if strict_mode:
                # STRICT MODE: Post must contain at least one PRIMARY keyword
                primary_keywords = keywords[:3]
                keyword_filters = [InstagramPost.caption.ilike(f"%{kw}%") for kw in primary_keywords]
                query = query.filter(or_(*keyword_filters))
                logger.info(f"STRICT keyword filter (IG): {primary_keywords}")
            else:
                # LOOSE MODE: Use expanded keywords
                expanded = expand_keywords(keywords)[:15]
                keyword_filters = [InstagramPost.caption.ilike(f"%{kw}%") for kw in expanded]
                query = query.filter(or_(*keyword_filters))

        query = query.order_by(InstagramPost.likes.desc(), InstagramPost.post_date.desc())
        posts_orm = query.limit(limit * 2).all()  # Get more for ranking

        content = []
        for p in posts_orm:
            councilor = self.db.query(Councilor).filter(
                Councilor.username == p.username
            ).first()

            caption = p.caption or ""

            content.append({
                "id": p.id,
                "username": p.username,
                "name": councilor.name if councilor else p.username,
                "party": normalize_party_name(councilor.party) if councilor and councilor.party else None,
                "tweet_text": caption,  # For compatibility with classifier
                "caption": caption,  # Original field name
                "tweet_date": str(p.post_date) if p.post_date else None,
                "post_date": str(p.post_date) if p.post_date else None,
                "likes": p.likes or 0,
                "retweets": 0,  # Instagram doesn't have retweets
                "comments": p.comments or 0,
                "replies": p.comments or 0,  # Alias for compatibility
                "views": 0,
                "platform": "instagram",
                "post_url": p.post_url,
                "is_video": p.is_video,
            })

        # Rank by keyword relevance if we have keywords
        if keywords and content:
            for item in content:
                item["keyword_score"] = calculate_keyword_score(
                    item.get("caption", ""),
                    keywords
                )
            content.sort(key=lambda x: x.get("keyword_score", 0), reverse=True)

        return content[:limit]

    def _get_party_members(self, party: str) -> List[str]:
        """Get all usernames belonging to a party."""
        normalized_party = normalize_party_name(party)
        logger.info(f"Looking for party members: '{party}' -> normalized: '{normalized_party}'")

        councilors = self.db.query(Councilor).all()

        members = [
            c.username
            for c in councilors
            if normalize_party_name(c.party) == normalized_party
        ]

        logger.info(f"Found {len(members)} members for party '{normalized_party}'")
        return members

    def _get_most_active_users(self, tweets: List[Dict]) -> List[str]:
        """Get top 3 most active users."""
        user_counts = {}
        for t in tweets:
            user = t.get("username", "")
            user_counts[user] = user_counts.get(user, 0) + 1
        sorted_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)
        return [u[0] for u in sorted_users[:3]]

    def _get_date_range(self, tweets: List[Dict]) -> Optional[str]:
        """Get date range from tweet list."""
        dates = [t.get("tweet_date", "")[:10] for t in tweets if t.get("tweet_date")]
        if dates:
            dates.sort()
            return f"{dates[0]} - {dates[-1]}"
        return None

    def get_suggested_questions(
        self,
        platform: str = "twitter",
        party_filter: Optional[str] = None
    ) -> List[str]:
        """
        Get suggested questions for the chat UI.

        Args:
            platform: Platform type (twitter, instagram, both)
            party_filter: Selected party filter

        Returns:
            List of suggested questions with platform-aware terminology
        """
        # Platform-aware content name
        content_name = self._get_content_name(platform)

        # Find opposite party for criticism suggestions
        opposite_party = None
        if party_filter:
            opposite_party = OPPOSITE_PARTIES.get(party_filter)

        suggestions = [
            f"Belediye hizmetleriyle ilgili {content_name}",
            f"En çok etkileşim alan {content_name}",
            f"Ekonomi hakkında {content_name}",
            f"Ulaşım konulu {content_name}",
        ]

        # Party-aware criticism suggestion
        if opposite_party:
            suggestions.append(f"{opposite_party} eleştirisi içeren {content_name}")
        else:
            suggestions.append(f"Hükümet eleştirisi içeren {content_name}")

        # Platform-specific suggestion
        if platform == "instagram":
            suggestions.append("En çok beğeni alan fotoğraflar")
        elif platform == "twitter":
            suggestions.append("Viral olan tweetler")
        else:
            suggestions.append("En popüler paylaşımlar")

        return suggestions[:6]
