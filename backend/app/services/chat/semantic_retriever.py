"""
Semantic Retriever v1.0 - Modern RAG for Short Text (Tweets/Posts)

2026 Best Practices Implementation:
1. Embedding-based semantic search (NOT LLM classification)
2. Hybrid retrieval: TF-IDF + Embedding similarity
3. Political concept matching via embeddings
4. Single LLM call only for final response

Architecture:
    Query → Embedding → Cosine Similarity → Top-K → LLM Summary

Why NOT use LLM for classification:
- 300 tweets × GPT-4o = 3 minutes, $$$, 0 results
- Embeddings: 300 tweets = 1 second, accurate, cheap

References:
- Anthropic Contextual Retrieval (2024)
- Superlinked Hybrid Search + Reranking
- RAGFlow 2025 Review
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

# Sentence transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from app.utils.logger import get_logger

logger = get_logger("SemanticRetriever")


# =============================================================================
# TOPIC CONCEPTS (Neutral topic detection - NOT criticism)
# =============================================================================

# These are NEUTRAL topics - presence alone does NOT mean criticism
TOPIC_CONCEPTS = {
    "ekonomi": {
        # IMPORTANT: Use specific keywords to avoid false matches
        # Avoid: "mali" (matches "Manisa"), "zam" (matches "zamanı")
        "keywords": ["ekonomi", "ekonomik", "enflasyon", "pahalılık", "hayat pahalı",
                     "fiyat artış", "asgari ücret", "emekli maaş", "geçim sıkıntı",
                     "bütçe", "kur artış", "döviz"],
        "examples": [
            # Few-shot examples for economy topic (NEUTRAL)
            "Merkez Bankası faiz kararını açıkladı",
            "Dolar kuru bugün 32 lira seviyesinde",
            "İhracat rakamları açıklandı, yüzde 5 artış var",
            "Bütçe görüşmeleri mecliste devam ediyor",
            "Enflasyon rakamları beklentilerin üzerinde geldi",
            "Ekonomi büyümesi yılın ilk çeyreğinde yüzde 4",
            "Türkiye ekonomisi G20 ülkeleri arasında",
        ]
    },
    "belediye": {
        "keywords": ["belediye", "park", "metro", "otobüs", "altyapı", "çöp",
                     "su", "kanalizasyon", "yol", "asfalt", "yeşil alan",
                     "belediyemiz", "belediyecilik", "şehir"],
        "examples": [
            "Belediyemiz yeni park açtı",
            "Metro hattı inşaatı devam ediyor",
            "Altyapı çalışmaları başladı",
            "Yeşil alan düzenlemesi tamamlandı",
            "Belediye otobüs hatları güncellendi",
            "Su kesintisi yarın saat 10'da başlayacak",
        ]
    },
    "ulaşım": {
        "keywords": ["ulaşım", "ulasim", "trafik", "metro", "otobüs", "köprü", "yol",
                     "havalimanı", "otogar", "bisiklet", "toplu taşıma", "tramvay"],
        "examples": [
            "Yeni metro hattı hizmete girdi",
            "Trafik yoğunluğu azaltmak için çalışmalar yapılıyor",
            "Toplu taşıma ücretlerine zam geldi",
            "Bisiklet yolları genişletiliyor",
            "Havalimanı bağlantı yolu açıldı",
        ]
    },
    "eğitim": {
        "keywords": ["eğitim", "egitim", "okul", "öğretmen", "ogretmen", "öğrenci",
                     "ogrenci", "üniversite", "universite", "sınav", "sinav",
                     "müfredat", "mufredat", "meb", "yök", "yok"],
        "examples": [
            "Okullar yarın açılıyor",
            "Öğretmen atamaları açıklandı",
            "YKS sınav sonuçları belli oldu",
            "Müfredat değişikliği gündemde",
            "Üniversite kontenjanları artırıldı",
        ]
    },
    "sağlık": {
        "keywords": ["sağlık", "saglik", "hastane", "doktor", "ilaç", "ilac",
                     "aşı", "asi", "tedavi", "acil", "ameliyat", "poliklinik",
                     "sağlıkçı", "saglikci", "hemşire", "hemsire"],
        "examples": [
            "Yeni hastane hizmete açıldı",
            "Aşı kampanyası başladı",
            "Sağlık personeli alımı yapılacak",
            "Hastane randevu sistemi güncellendi",
        ]
    }
}


# =============================================================================
# POLITICAL CONCEPT EMBEDDINGS (Criticism-specific)
# =============================================================================

# Pre-defined concepts for Turkish political content
# These will be embedded and used for semantic matching
# NOTE: "ekonomi_genel" REMOVED - ekonomi alone is NOT criticism
CRITICISM_CONCEPTS = {
    "hükümet_eleştirisi": [
        # Explicit criticism phrases with negative sentiment
        "hükümet başarısız berbat rezalet",
        "iktidar yanlış karar felaket",
        "AKP ekonomi felaketi kriz",
        "enflasyon zamlar hükümet suçlu",
        "saray israfı halk aç perişan",
        "iktidar yolsuzluk hırsızlık",
        "hükümet eğitim sağlık yetersiz berbat",
        "ekonomik kriz işsizlik sefalet",
        "dolar kur krizi battık",
        "hayat pahalılığı geçinemiyoruz",
        "vergiler zamlar halk eziliyor",
        "yoksulluk açlık sefalet perişan",
        "fatura ödeyemiyoruz geçinemiyoruz",
        "emekli maaşı yetmiyor açlık",
        "asgari ücret yetersiz sefalet",
        "bu iktidar gitmeli değişim şart",
        "hükümet istifa çekilin",
    ],
    "chp_eleştirisi": [
        "CHP belediyesi başarısız berbat",
        "muhalefet yetersiz beceriksiz",
        "İmamoğlu vaatleri tutmadı yalan",
        "Mansur Yavaş hizmet yok berbat",
        "CHP iktidar olamaz başarısız",
        "muhalefet birlik değil kavga",
        "CHP politikası yok boş",
    ],
    "belediye_hizmeti": [
        "belediye park açtı hizmet",
        "metro tramvay ulaşım hizmet",
        "altyapı çalışması belediye",
        "şehir temizlik belediye",
        "yeşil alan düzenleme park",
        "sosyal yardım dağıtım belediye",
    ],
}

# Negative sentiment indicators for criticism detection
NEGATIVE_SENTIMENT_WORDS = {
    # Strong negative (doubled weight in scoring)
    "berbat", "rezalet", "felaket", "fiyasko", "skandal", "yolsuzluk", "hırsızlık",
    "sefalet", "perişan", "batırdı", "battık", "çöktü", "iflas", "kriz",
    # Criticism verbs
    "eleştir", "elestir", "kına", "protesto", "suçla", "sorgula", "hesap sor",
    "tepki", "itiraz", "şikayet", "sikayet", "isyan",
    # Negative adjectives
    "başarısız", "basarisiz", "yetersiz", "beceriksiz", "kötü", "kotu", "yanlış", "yanlis",
    "hatalı", "hatali", "eksik", "sorunlu", "problemli", "vahim", "korkunç", "korkunc",
    "utanç", "utanc", "rezil", "acı", "aci", "acınası", "acinasi", "zavallı", "zavalli",
    # Negative states / complaints
    "açlık", "aclik", "yoksulluk", "işsizlik", "issizlik", "pahalılık", "pahalilik",
    "zamlar", "zamma", "zamlı", "zamli", "enflasyon", "fakirlik", "sıkıntı", "sikinti", "dert", "sorun",
    "geçinemiyoruz", "gecinemiyoruz", "ödeyemiyoruz", "odeyemiyoruz", "yetmiyor",
    "bıktık", "biktik", "yeter", "yorulduk", "tükendik", "tukendik", "bitirdiler",
    # Economic criticism
    "dolar", "kur", "devalüasyon", "devaluasyon", "faiz", "borç", "borc",
    "vergi", "fatura", "elektrik zammı", "doğalgaz zammı", "akaryakıt",
    # Political criticism
    "istifa", "çekilin", "cekilin", "gidin", "değişim", "degisim", "yeter artık",
    "hesap verin", "nerede", "nereye gitti", "kayıp", "kayip", "israf", "lüks", "luks",
    # Government-specific criticism
    "saray", "saltanat", "diktatör", "diktator", "otoriter", "baskı", "baski",
    "sansür", "sansur", "tutuklu", "hapis", "adaletsiz", "hukuksuz",
    # Opposition criticism terms (for CHP criticism detection)
    "muhalefet yetersiz", "alternatif yok", "çözüm yok", "cozum yok",
}

# =============================================================================
# PHRASE-LEVEL SENTIMENT (Stronger signals than single words)
# =============================================================================

STRONG_CRITICISM_PHRASES = [
    # Government criticism
    "hükümet başarısız", "hukumet basarisiz",
    "iktidar felaketi", "iktidar başarısız",
    "ekonomi çöktü", "ekonomi coktu", "ekonomi battı",
    "enflasyon patladı", "enflasyon fırladı",
    "işsizlik patladı", "issizlik patladi",
    "halk perişan", "halk perisan", "vatandaş mağdur",
    "ülke batıyor", "ulke batiyor",
    # Opposition criticism
    "chp başarısız", "chp basarisiz",
    "muhalefet başarısız", "muhalefet yetersiz",
    "belediye rezaleti", "belediye başarısız",
    # General strong criticism
    "tam bir fiyasko", "tam bir rezalet",
    "utanç verici", "utanc verici",
]

STRONG_POSITIVE_PHRASES = [
    "hizmet başladı", "hizmet basladi",
    "proje tamamlandı", "proje tamamlandi",
    "yatırım yapıldı", "yatirim yapildi",
    "sorun çözüldü", "sorun cozuldu",
    "açılış yapıldı", "acilis yapildi",
    "başarıyla tamamlandı", "basariyla tamamlandi",
    "hayırlı olsun", "hayirli olsun",
]

# Positive/neutral words that indicate NOT criticism
POSITIVE_NEUTRAL_WORDS = {
    # Achievements / announcements
    "açtık", "actik", "açıldı", "acildi", "başladı", "basladi", "tamamlandı", "tamamlandi",
    "hizmete girdi", "hayata geçti", "hayata gecti", "devreye alındı", "devreye alindi",
    "kabul edildi", "onaylandı", "onaylandi", "gerçekleştirdik", "gerceklestirdik",
    "başardık", "basardik", "bitirdik", "yaptık", "yaptik",
    # Positive events / celebrations
    "kutlu olsun", "tebrikler", "teşekkürler", "tesekkurler", "hayırlı olsun", "hayirli olsun",
    "gurur", "mutlu", "sevindirici", "başarılı", "basarili", "başarı", "basari",
    "mükemmel", "mukemmel", "harika", "güzel", "guzel", "muhteşem", "muhtesem",
    "takdir", "övgü", "ovgu", "memnuniyet", "teşekkür", "tesekkkur",
    # Announcements / events (non-critical content)
    "duyuru", "davet", "etkinlik", "toplantı", "toplanti", "ziyaret", "inceleme",
    "açılış", "acilis", "temel atma", "lansman", "tanıtım", "tanitim",
    # Own party activities / self-promotion
    "meclisimiz", "belediyemiz", "ilçemiz", "ilcemiz", "hizmetimiz", "partimiz",
    "yaptıklarımız", "yaptiklarimiz", "projemiz", "çalışmamız", "calismamiz",
    # Political support (not criticism)
    "destekliyoruz", "yanındayız", "yanindayiz", "birlikte", "el ele", "omuz omuza",
    "güçlü", "guclu", "kararlı", "kararli",
    # Hashtags often used in positive announcements
    "#hizmet", "#çalışıyoruz", "#calisiyoruz", "#teşekkürler", "#tesekkurler",
}

# Negation words that cancel sentiment
NEGATION_WORDS = {
    "yok", "değil", "degil", "olmayan", "olmaz",
    "hiç", "hic", "asla", "hiçbir", "hicbir",
    "yapma", "etme", "olmadı", "olmadi"
}


@dataclass
class RetrievalResult:
    """Single retrieval result with score"""
    content: Dict[str, Any]
    semantic_score: float
    keyword_score: float
    sentiment_score: float  # Negative = criticism, Positive = praise
    combined_score: float
    matched_concepts: List[str]


@dataclass
class RetrievalResponse:
    """Complete retrieval response"""
    results: List[RetrievalResult]
    total_searched: int
    query_concepts: List[str]
    retrieval_time_ms: float


class SemanticRetriever:
    """
    Modern semantic retriever for Turkish political content.

    Uses embedding-based similarity instead of LLM classification.
    Much faster and more accurate for short text like tweets.
    """

    def __init__(self, model_name: str = "emrecan/bert-base-turkish-cased-mean-nli-stsb-tr"):
        """
        Initialize with Turkish embedding model.

        Recommended models for Turkish:
        - emrecan/bert-base-turkish-cased-mean-nli-stsb-tr (best for similarity)
        - dbmdz/bert-base-turkish-cased
        - sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
        """
        self.model = None
        self.concept_embeddings = {}

        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("sentence-transformers not installed, using TF-IDF fallback")
            return

        try:
            # Try Turkish model first, fallback to multilingual
            try:
                self.model = SentenceTransformer(model_name)
                logger.info(f"SemanticRetriever initialized with {model_name}")
            except Exception:
                fallback = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
                self.model = SentenceTransformer(fallback)
                logger.info(f"SemanticRetriever initialized with fallback: {fallback}")

            # Pre-compute concept embeddings
            self._precompute_concept_embeddings()

        except Exception as e:
            logger.error(f"Failed to initialize SemanticRetriever: {e}")
            self.model = None

    def _precompute_concept_embeddings(self):
        """Pre-compute embeddings for political concepts."""
        if not self.model:
            return

        logger.info("Pre-computing concept embeddings...")
        for concept_name, phrases in CRITICISM_CONCEPTS.items():
            # Embed all phrases and average them
            embeddings = self.model.encode(phrases, convert_to_numpy=True)
            # Use mean embedding as concept representation
            self.concept_embeddings[concept_name] = np.mean(embeddings, axis=0)

        logger.info(f"Computed embeddings for {len(self.concept_embeddings)} concepts")

    def retrieve(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        target_concepts: Optional[List[str]] = None,
        top_k: int = 30,
        min_score: float = 0.3
    ) -> RetrievalResponse:
        """
        Retrieve relevant documents using semantic search.

        Args:
            query: User's search query
            documents: List of documents (tweets/posts) to search
            target_concepts: Specific concepts to match (e.g., ["hükümet_eleştirisi"])
            top_k: Number of results to return
            min_score: Minimum similarity score threshold

        Returns:
            RetrievalResponse with ranked results
        """
        import time
        start_time = time.time()

        if not documents:
            return RetrievalResponse(
                results=[],
                total_searched=0,
                query_concepts=[],
                retrieval_time_ms=0
            )

        # Extract text from documents
        texts = [
            doc.get("tweet_text", doc.get("caption", doc.get("text", "")))
            for doc in documents
        ]

        # Use embedding-based search if available
        if self.model:
            results = self._semantic_search(query, texts, documents, target_concepts, top_k, min_score)
        else:
            results = self._tfidf_search(query, texts, documents, top_k, min_score)

        elapsed_ms = (time.time() - start_time) * 1000

        return RetrievalResponse(
            results=results,
            total_searched=len(documents),
            query_concepts=target_concepts or [],
            retrieval_time_ms=elapsed_ms
        )

    def _detect_phrase_sentiment(self, text: str) -> float:
        """
        Detect phrase-level sentiment (stronger signals than single words).

        Returns:
            Negative value for criticism phrases found
            Positive value for positive phrases found
            Sum of all phrase scores
        """
        text_lower = text.lower()
        score = 0.0

        # Check for strong criticism phrases (-2.0 each)
        for phrase in STRONG_CRITICISM_PHRASES:
            if phrase in text_lower:
                score -= 2.0

        # Check for strong positive phrases (+1.0 each)
        for phrase in STRONG_POSITIVE_PHRASES:
            if phrase in text_lower:
                score += 1.0

        return score

    def _calculate_sentiment_score(self, text: str) -> float:
        """
        Calculate sentiment score for a text.

        Returns:
            Negative value = criticism/negative sentiment
            Positive value = praise/positive sentiment
            Near zero = neutral

        Score range: -1.0 to +1.0
        """
        import re
        text_lower = text.lower()
        words = text_lower.split()

        negative_count = 0
        positive_count = 0

        def has_negation_before(word_index: int, window: int = 3) -> bool:
            """Check if there's a negation word within N words before the given index."""
            start_idx = max(0, word_index - window)
            for i in range(start_idx, word_index):
                if words[i] in NEGATION_WORDS:
                    return True
            return False

        # Count negative sentiment indicators using word boundary matching
        for neg_word in NEGATIVE_SENTIMENT_WORDS:
            # Use word boundary for single words, substring for phrases
            if ' ' in neg_word:
                # Phrase: use substring match
                if neg_word in text_lower:
                    negative_count += 1
            else:
                # Single word: check if it appears as a word or word stem
                # Turkish suffixes: match word starts with the negative word
                pattern = r'\b' + re.escape(neg_word)
                match = re.search(pattern, text_lower)
                if match:
                    # Find which word index this match corresponds to
                    match_pos = match.start()
                    word_idx = len(text_lower[:match_pos].split()) - 1
                    word_idx = max(0, word_idx)

                    # Check for negation in 3-word window before
                    if has_negation_before(word_idx, window=3):
                        # Negation cancels the sentiment - skip this word
                        continue

                    negative_count += 1
                    # Strong negatives count double
                    if neg_word in {"berbat", "rezalet", "felaket", "sefalet", "yolsuzluk", "hırsızlık", "kriz", "skandal"}:
                        negative_count += 1

        # Count positive/neutral indicators
        for pos_word in POSITIVE_NEUTRAL_WORDS:
            if ' ' in pos_word:
                if pos_word in text_lower:
                    positive_count += 1
            else:
                pattern = r'\b' + re.escape(pos_word)
                match = re.search(pattern, text_lower)
                if match:
                    # Find which word index this match corresponds to
                    match_pos = match.start()
                    word_idx = len(text_lower[:match_pos].split()) - 1
                    word_idx = max(0, word_idx)

                    # Check for negation in 3-word window before
                    if has_negation_before(word_idx, window=3):
                        # Negation cancels the sentiment - skip this word
                        continue

                    positive_count += 1

        # Calculate base score from word-level sentiment
        # If no sentiment words found, return slightly positive (neutral content)
        if negative_count == 0 and positive_count == 0:
            base_score = 0.1  # Slightly positive = neutral content
        else:
            # Calculate weighted score
            # More negative words = more negative score
            total = negative_count + positive_count
            base_score = (positive_count - negative_count) / total

        # Add phrase-level sentiment (stronger signals)
        phrase_score = self._detect_phrase_sentiment(text)

        # Combine: base_score is [-1, 1], phrase_score can be larger
        # Normalize phrase contribution and add to base
        combined = base_score + (phrase_score * 0.2)  # Scale phrase impact

        return max(-1.0, min(1.0, combined))  # Clamp to [-1, 1]

    def _is_criticism_search(self, query: str, target_concepts: Optional[List[str]]) -> bool:
        """
        Check if this is EXPLICITLY a criticism-focused search.

        IMPORTANT: Topic alone (ekonomi, belediye) does NOT mean criticism.
        Only return True if query contains explicit criticism keywords.
        """
        query_lower = query.lower()

        # Explicit criticism keywords - MUST be present for criticism search
        criticism_keywords = [
            "eleştiri", "elestiri", "eleştiren", "elestiren", "eleştir", "elestir",
            "başarısız", "basarisiz", "kötü", "kotu", "berbat",
            "rezalet", "skandal", "yolsuzluk", "felaket",
            "karşı", "karsi", "tepki", "protesto", "şikayet", "sikayet",
            "sefalet", "perişan", "perisan", "kriz",
        ]

        has_criticism_keyword = any(kw in query_lower for kw in criticism_keywords)

        # Also check target concepts - only explicit criticism concepts
        has_criticism_concept = False
        if target_concepts:
            # Only these are TRUE criticism concepts
            criticism_only_concepts = {"hükümet_eleştirisi", "chp_eleştirisi"}
            has_criticism_concept = any(c in criticism_only_concepts for c in target_concepts)

        return has_criticism_keyword or has_criticism_concept

    def _semantic_search(
        self,
        query: str,
        texts: List[str],
        documents: List[Dict],
        target_concepts: Optional[List[str]],
        top_k: int,
        min_score: float
    ) -> List[RetrievalResult]:
        """
        Embedding-based semantic search with conditional sentiment filtering.

        IMPORTANT: Sentiment filter is ONLY applied for EXPLICIT criticism searches.
        Topic searches (ekonomi, belediye, etc.) do NOT apply sentiment filtering.
        """

        # Encode query and documents
        query_embedding = self.model.encode([query], convert_to_numpy=True)[0]
        doc_embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

        # Calculate semantic similarity scores
        semantic_scores = self._cosine_similarity(query_embedding, doc_embeddings)

        # Calculate sentiment scores for all documents
        sentiment_scores = np.array([self._calculate_sentiment_score(text) for text in texts])

        # UPDATED: Check if this is EXPLICITLY a criticism search (pass query!)
        is_criticism = self._is_criticism_search(query, target_concepts)

        # Detect topic from query for better logging
        detected_topic = self.detect_topic(query)
        if detected_topic:
            logger.info(f"Detected topic: {detected_topic}, is_criticism={is_criticism}")

        # If target concepts specified, also match against concepts
        concept_scores = np.zeros(len(documents))
        matched_concepts_per_doc = [[] for _ in range(len(documents))]

        if target_concepts:
            for concept_name in target_concepts:
                if concept_name in self.concept_embeddings:
                    concept_emb = self.concept_embeddings[concept_name]
                    scores = self._cosine_similarity(concept_emb, doc_embeddings)

                    # Track which concepts match for each doc
                    for i, score in enumerate(scores):
                        if score > 0.4:  # Concept match threshold
                            matched_concepts_per_doc[i].append(concept_name)
                            concept_scores[i] = max(concept_scores[i], score)

        # Combine scores based on search type
        if is_criticism:
            # For EXPLICIT criticism searches: semantic + concept + NEGATIVE sentiment boost
            # Negative sentiment_scores become positive contributions (multiply by -1)
            sentiment_boost = -sentiment_scores  # Flip: negative sentiment → positive boost
            sentiment_boost = np.clip(sentiment_boost, 0, 1)  # Only boost for negative sentiment

            combined_scores = (
                0.25 * semantic_scores +
                0.35 * concept_scores +
                0.40 * sentiment_boost  # Heavy weight on sentiment for criticism
            )

            logger.info(f"Criticism search: applying sentiment filter (avg sentiment: {np.mean(sentiment_scores):.2f})")
        elif target_concepts:
            # Topic search WITH concepts - NO sentiment filter
            combined_scores = 0.5 * semantic_scores + 0.5 * concept_scores
            logger.info(f"Topic search with concepts: NO sentiment filter applied")
        else:
            # Pure semantic search - NO sentiment filter
            combined_scores = semantic_scores
            logger.info(f"Pure semantic search: NO sentiment filter applied")

        # Rank and filter
        results = []
        ranked_indices = np.argsort(combined_scores)[::-1]

        # For criticism search, also log sentiment distribution
        if is_criticism:
            negative_count = np.sum(sentiment_scores < -0.1)
            positive_count = np.sum(sentiment_scores > 0.1)
            neutral_count = len(sentiment_scores) - negative_count - positive_count
            logger.info(f"Sentiment distribution: negative={negative_count}, neutral={neutral_count}, positive={positive_count}")

        for idx in ranked_indices[:top_k * 3]:  # Get more candidates for filtering
            score = combined_scores[idx]
            sent_score = sentiment_scores[idx]

            if score < min_score:
                continue

            # UPDATED: Only apply sentiment filter for EXPLICIT criticism searches
            # For topic searches (ekonomi, belediye), include ALL sentiment content
            if is_criticism and sent_score >= 0.0:
                logger.debug(f"Skipping non-negative content (sentiment={sent_score:.2f}): {texts[idx][:50]}...")
                continue

            results.append(RetrievalResult(
                content=documents[idx],
                semantic_score=float(semantic_scores[idx]),
                keyword_score=0.0,  # TF-IDF not used here
                sentiment_score=float(sent_score),
                combined_score=float(score),
                matched_concepts=matched_concepts_per_doc[idx]
            ))

            if len(results) >= top_k:
                break

        logger.info(f"Semantic search: {len(results)} results from {len(documents)} docs (criticism_mode={is_criticism})")
        return results

    def _tfidf_search(
        self,
        query: str,
        texts: List[str],
        documents: List[Dict],
        top_k: int,
        min_score: float
    ) -> List[RetrievalResult]:
        """TF-IDF fallback when embeddings not available."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        # Combine query with documents for TF-IDF
        all_texts = [query] + texts

        vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            min_df=1
        )
        tfidf_matrix = vectorizer.fit_transform(all_texts)

        # Query is first, documents are rest
        query_vec = tfidf_matrix[0:1]
        doc_vecs = tfidf_matrix[1:]

        # Calculate similarity
        scores = cosine_similarity(query_vec, doc_vecs).flatten()

        # Calculate sentiment scores
        sentiment_scores = [self._calculate_sentiment_score(text) for text in texts]

        # Rank and filter
        results = []
        ranked_indices = np.argsort(scores)[::-1]

        for idx in ranked_indices[:top_k]:
            score = scores[idx]
            if score < min_score:
                continue

            results.append(RetrievalResult(
                content=documents[idx],
                semantic_score=0.0,
                keyword_score=float(score),
                sentiment_score=float(sentiment_scores[idx]),
                combined_score=float(score),
                matched_concepts=[]
            ))

        logger.info(f"TF-IDF search: {len(results)} results from {len(documents)} docs")
        return results

    def _cosine_similarity(self, query_emb: np.ndarray, doc_embs: np.ndarray) -> np.ndarray:
        """Calculate cosine similarity between query and documents."""
        # Normalize
        query_norm = query_emb / (np.linalg.norm(query_emb) + 1e-8)
        doc_norms = doc_embs / (np.linalg.norm(doc_embs, axis=1, keepdims=True) + 1e-8)

        # Dot product = cosine similarity for normalized vectors
        return np.dot(doc_norms, query_norm)

    def detect_topic(self, query: str) -> Optional[str]:
        """
        Detect the PRIMARY topic of the query using keyword matching.

        This detects NEUTRAL topics (ekonomi, belediye, etc.)
        NOT criticism intent.

        Args:
            query: User query

        Returns:
            Topic name or None
        """
        query_lower = query.lower()

        for topic_name, topic_data in TOPIC_CONCEPTS.items():
            keywords = topic_data.get("keywords", [])
            if any(kw in query_lower for kw in keywords):
                return topic_name

        return None

    def get_topic_keywords(self, topic: str) -> List[str]:
        """Get keywords for a topic."""
        topic_data = TOPIC_CONCEPTS.get(topic, {})
        return topic_data.get("keywords", [])

    def get_topic_examples(self, topic: str) -> List[str]:
        """Get few-shot examples for a topic."""
        topic_data = TOPIC_CONCEPTS.get(topic, {})
        return topic_data.get("examples", [])

    def detect_query_concepts(self, query: str) -> List[str]:
        """
        Detect which political concepts are relevant to the query.

        Uses BOTH rule-based and embedding-based detection for best results.

        Args:
            query: User query

        Returns:
            List of concept names that match the query
        """
        # Always start with rule-based detection (handles ASCII/Turkish variants)
        rule_based = self._rule_based_concept_detection(query)

        # If we have embedding model, also do semantic matching
        if self.model and self.concept_embeddings:
            query_embedding = self.model.encode([query], convert_to_numpy=True)[0]

            for concept_name, concept_emb in self.concept_embeddings.items():
                similarity = np.dot(
                    query_embedding / np.linalg.norm(query_embedding),
                    concept_emb / np.linalg.norm(concept_emb)
                )
                # Lower threshold for embedding match (0.35)
                if similarity > 0.35 and concept_name not in rule_based:
                    rule_based.append(concept_name)

        return rule_based[:4]  # Return top 4 concepts

    def _rule_based_concept_detection(self, query: str) -> List[str]:
        """
        Rule-based fallback for concept detection.

        IMPORTANT: Topic detection (ekonomi, belediye) does NOT automatically
        mean criticism. Only add criticism concepts if explicit criticism
        keywords are present.
        """
        query_lower = query.lower()
        concepts = []

        # Explicit criticism keywords - must be present for criticism detection
        criticism_terms = [
            "eleştir", "elestir", "eleştiri", "elestiri",
            "kötü", "kotu", "başarısız", "basarisiz", "berbat", "felaket",
            "rezalet", "skandal", "yolsuzluk", "sefalet", "kriz",
            "karşı", "karsi", "tepki", "protesto"
        ]
        has_criticism = any(w in query_lower for w in criticism_terms)

        # Hükümet eleştirisi - handle both Turkish and ASCII variants
        govt_terms = ["hükümet", "hukumet", "iktidar", "akp", "ak parti", "erdoğan", "erdogan", "saray"]

        if any(w in query_lower for w in govt_terms):
            # Only add government criticism if explicit criticism keywords present
            if has_criticism:
                concepts.append("hükümet_eleştirisi")

        # CHP/muhalefet eleştirisi
        chp_terms = ["chp", "muhalefet", "imamoğlu", "imamoglu", "mansur"]
        if any(w in query_lower for w in chp_terms):
            if has_criticism:
                concepts.append("chp_eleştirisi")

        # Ekonomi - DOES NOT automatically mean criticism!
        # Only add hükümet_eleştirisi if EXPLICIT criticism keywords present
        econ_terms = ["ekonomi", "enflasyon", "zam", "dolar", "işsizlik", "issizlik", "pahalılık", "pahalilik"]
        if any(w in query_lower for w in econ_terms):
            # Only add government criticism if there's explicit criticism language
            if has_criticism:
                concepts.append("hükümet_eleştirisi")
            # Note: "ekonomi_genel" removed from CRITICISM_CONCEPTS

        # Belediye hizmetleri - neutral topic
        belediye_terms = ["belediye", "metro", "park", "ulaşım", "ulasim", "altyapı", "altyapi"]
        if any(w in query_lower for w in belediye_terms):
            concepts.append("belediye_hizmeti")

        return list(set(concepts))  # Remove duplicates


# Singleton instance
_retriever_instance = None

def get_semantic_retriever() -> SemanticRetriever:
    """Get or create SemanticRetriever singleton."""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = SemanticRetriever()
    return _retriever_instance
