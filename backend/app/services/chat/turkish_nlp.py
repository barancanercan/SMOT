#!/usr/bin/env python3
"""
Turkish NLP Module for Chat with Tweets

Provides Turkish-specific text processing:
1. Suffix stripping (lightweight stemming)
2. Synonym expansion
3. Text normalization
4. Keyword extraction
"""

import re
from typing import List, Set, Dict, Tuple
from dataclasses import dataclass


# =============================================================================
# TURKISH CHARACTER NORMALIZATION
# =============================================================================

TURKISH_CHAR_MAP = {
    'ı': 'i', 'İ': 'i',
    'ğ': 'g', 'Ğ': 'g',
    'ü': 'u', 'Ü': 'u',
    'ş': 's', 'Ş': 's',
    'ö': 'o', 'Ö': 'o',
    'ç': 'c', 'Ç': 'c',
}

def normalize_turkish(text: str) -> str:
    """Normalize Turkish characters to ASCII equivalents."""
    result = text.lower()
    for tr_char, ascii_char in TURKISH_CHAR_MAP.items():
        result = result.replace(tr_char, ascii_char)
    return result


def preserve_turkish_lower(text: str) -> str:
    """Lowercase while preserving Turkish characters."""
    # Handle Turkish I specially
    text = text.replace('I', 'ı').replace('İ', 'i')
    return text.lower()


# =============================================================================
# TURKISH STOPWORDS
# =============================================================================

TURKISH_STOPWORDS = {
    # Pronouns
    'ben', 'sen', 'o', 'biz', 'siz', 'onlar',
    # Conjunctions
    've', 'ile', 'veya', 'ya', 'yahut', 'ama', 'fakat', 'ancak', 'lakin',
    'oysa', 'halbuki', 'ne', 'hem', 'ki', 'de', 'da',
    # Prepositions
    'icin', 'için', 'gibi', 'kadar', 'gore', 'göre', 'dolayi', 'dolayı',
    'ile', 'karsi', 'karşı', 'uzerine', 'üzerine',
    # Question words
    'mi', 'mı', 'mu', 'mü', 'ne', 'kim', 'hangi', 'nasil', 'nasıl', 'neden', 'niye',
    # Demonstratives
    'bu', 'su', 'şu', 'o', 'bunlar', 'sunlar', 'şunlar', 'onlar',
    # Quantifiers
    'bir', 'iki', 'uc', 'üç', 'tum', 'tüm', 'hep', 'her', 'bazi', 'bazı',
    'cok', 'çok', 'az', 'en', 'daha', 'pek', 'hic', 'hiç',
    # Verbs (common)
    'var', 'yok', 'olan', 'olarak', 'olmak', 'etmek', 'yapmak',
    'dedi', 'soyledi', 'söyledi', 'bildirdi', 'acikladi', 'açıkladı',
    # Time expressions
    'bugun', 'bugün', 'dun', 'dün', 'yarin', 'yarın', 'simdi', 'şimdi',
    'once', 'önce', 'sonra', 'hala', 'hâlâ',
    # Twitter/Social specific
    'rt', 'via', 'https', 'http', 'www', 'com', 'tr', 'co',
    # Common fillers
    'iste', 'işte', 'evet', 'hayir', 'hayır', 'tamam', 'peki',
    # Chat query specific
    'getir', 'goster', 'göster', 'listele', 'bul', 'ara',
    'tweetleri', 'tweetlerini', 'tweet', 'paylasimlari', 'paylaşımları',
    'atan', 'atti', 'attı', 'atilan', 'atılan', 'atilmis', 'atılmış',
    'iceren', 'içeren', 'hakkinda', 'hakkında', 'ilgili', 'konulu',
}


# =============================================================================
# TURKISH SUFFIX STRIPPING (Lightweight Stemming)
# =============================================================================

# Common Turkish suffixes in order of length (longer first)
TURKISH_SUFFIXES = [
    # Verb suffixes
    'maktadır', 'mektedir', 'maktatır', 'mektedir',
    'ıyorlar', 'iyorlar', 'uyorlar', 'üyorlar',
    'ıyoruz', 'iyoruz', 'uyoruz', 'üyoruz',
    'ıyorsun', 'iyorsun', 'uyorsun', 'üyorsun',
    'ıyorum', 'iyorum', 'uyorum', 'üyorum',
    'acak', 'ecek', 'ıyor', 'iyor', 'uyor', 'üyor',
    'mış', 'miş', 'muş', 'müş', 'mis', 'mus',
    'dı', 'di', 'du', 'dü', 'tı', 'ti', 'tu', 'tü',
    # Noun suffixes
    'ların', 'lerin', 'larını', 'lerini',
    'ları', 'leri', 'lar', 'ler',
    'ında', 'inde', 'unda', 'ünde', 'nda', 'nde',
    'ından', 'inden', 'undan', 'ünden', 'ndan', 'nden',
    'ına', 'ine', 'una', 'üne', 'na', 'ne',
    'ını', 'ini', 'unu', 'ünü', 'nı', 'ni', 'nu', 'nü',
    'ın', 'in', 'un', 'ün',
    'ı', 'i', 'u', 'ü',
    'yla', 'yle', 'la', 'le',
    'dan', 'den', 'tan', 'ten',
    'da', 'de', 'ta', 'te',
    'ca', 'ce', 'ça', 'çe',
    # Derivational suffixes
    'lık', 'lik', 'luk', 'lük',
    'sız', 'siz', 'suz', 'süz',
    'lı', 'li', 'lu', 'lü',
    'cı', 'ci', 'cu', 'cü', 'çı', 'çi', 'çu', 'çü',
    'sal', 'sel',
    'ık', 'ik', 'uk', 'ük',
]

def turkish_stem(word: str, min_stem_length: int = 3) -> str:
    """
    Apply lightweight Turkish suffix stripping.

    Args:
        word: Word to stem
        min_stem_length: Minimum length of resulting stem

    Returns:
        Stemmed word
    """
    word = word.lower()

    for suffix in TURKISH_SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= min_stem_length:
            return word[:-len(suffix)]

    return word


def stem_text(text: str) -> List[str]:
    """Stem all words in text."""
    words = re.findall(r'\b\w+\b', text.lower())
    return [turkish_stem(w) for w in words if len(w) > 2]


# =============================================================================
# TURKISH SYNONYMS
# =============================================================================

# Synonym groups - each tuple contains words that should match each other
SYNONYM_GROUPS: List[Tuple[str, ...]] = [
    # Government/Power
    ('hükümet', 'hukumet', 'iktidar', 'yönetim', 'yonetim', 'devlet'),
    ('cumhurbaşkanı', 'cumhurbaskani', 'erdoğan', 'erdogan', 'saray', 'beştepe', 'bestepe'),
    ('başbakan', 'basbakan', 'hükümet başkanı'),

    # Parties
    ('akp', 'ak parti', 'akparti', 'adalet ve kalkınma'),
    ('chp', 'cumhuriyet halk partisi', 'ana muhalefet'),
    ('mhp', 'milliyetçi hareket', 'milliyetci hareket'),
    ('iyi parti', 'iyip', 'iyi'),
    ('dem parti', 'hdp', 'yeşil sol', 'yesil sol'),

    # Opposition
    ('muhalefet', 'karşı', 'karsi', 'rakip', 'hasım', 'hasim'),

    # Economy
    # NOTE: "mali" removed - causes false positives with "Manisa", "Kemal" etc.
    # NOTE: "zam" removed - causes false positives with "zamanı", "zamanında" etc.
    ('ekonomi', 'ekonomik', 'iktisadi', 'finansal'),
    ('enflasyon', 'pahalılık', 'pahalilik', 'hayat pahalılığı', 'zamlar'),
    ('işsizlik', 'issizlik', 'istihdam'),
    ('dolar', 'kur', 'döviz', 'doviz', 'euro', 'sterlin'),
    ('fiyat artışı', 'artış', 'artis'),
    ('maaş', 'maas', 'ücret', 'ucret', 'gelir'),
    ('asgari', 'minimum', 'en düşük', 'en dusuk'),

    # Politics
    ('eleştiri', 'elestiri', 'tenkit', 'kritik', 'itiraz'),
    ('protesto', 'eylem', 'gösteri', 'gosteri', 'yürüyüş', 'yuruyus'),
    ('seçim', 'secim', 'oy', 'sandık', 'sandik'),
    ('meclis', 'tbmm', 'parlamento'),

    # Services
    ('belediye', 'yerel yönetim', 'yerel yonetim', 'kent', 'şehir', 'sehir'),
    ('ulaşım', 'ulasim', 'trafik', 'toplu taşıma', 'toplu tasima'),
    ('metro', 'tramvay', 'otobüs', 'otobus', 'metrobüs', 'metrobus'),
    ('eğitim', 'egitim', 'okul', 'öğretmen', 'ogretmen', 'öğrenci', 'ogrenci'),
    ('sağlık', 'saglik', 'hastane', 'doktor', 'hekim'),

    # Criticism words
    ('başarısız', 'basarisiz', 'yetersiz', 'kifayetsiz', 'beceriksiz'),
    ('yolsuzluk', 'rüşvet', 'rusvet', 'hırsızlık', 'hirsizlik'),
    ('skandal', 'rezalet', 'fiyasko', 'felaket'),
    ('kriz', 'buhran', 'çöküş', 'cokus'),

    # Support words
    ('destek', 'yardım', 'yardim', 'katkı', 'katki'),
    ('başarı', 'basari', 'zafer', 'kazanım', 'kazanim'),
    ('hizmet', 'icraat', 'faaliyet'),

    # Time
    ('bugün', 'bugun', 'şimdi', 'simdi', 'günümüz', 'gunumuz'),
    ('dün', 'dun', 'geçen', 'gecen', 'önceki', 'onceki'),
]

# Build synonym lookup dictionary
SYNONYM_MAP: Dict[str, Set[str]] = {}
for group in SYNONYM_GROUPS:
    normalized_group = set()
    for word in group:
        normalized_group.add(normalize_turkish(word))
        normalized_group.add(word.lower())

    for word in group:
        norm_word = normalize_turkish(word)
        SYNONYM_MAP[norm_word] = normalized_group
        SYNONYM_MAP[word.lower()] = normalized_group


def get_synonyms(word: str) -> Set[str]:
    """Get all synonyms for a word."""
    word_lower = word.lower()
    word_norm = normalize_turkish(word)

    synonyms = set()

    if word_lower in SYNONYM_MAP:
        synonyms.update(SYNONYM_MAP[word_lower])

    if word_norm in SYNONYM_MAP:
        synonyms.update(SYNONYM_MAP[word_norm])

    # Always include original
    synonyms.add(word_lower)
    synonyms.add(word_norm)

    return synonyms


def expand_keywords(keywords: List[str]) -> List[str]:
    """Expand keywords with their synonyms."""
    expanded = set()

    for keyword in keywords:
        expanded.add(keyword.lower())
        expanded.add(normalize_turkish(keyword))

        # Add synonyms
        synonyms = get_synonyms(keyword)
        expanded.update(synonyms)

        # Add stemmed version
        stemmed = turkish_stem(keyword)
        expanded.add(stemmed)

    return list(expanded)


# =============================================================================
# TEXT PROCESSING
# =============================================================================

@dataclass
class ProcessedText:
    """Result of text processing."""
    original: str
    normalized: str
    tokens: List[str]
    stems: List[str]
    keywords: List[str]  # Without stopwords


def process_text(text: str) -> ProcessedText:
    """
    Process Turkish text for search/matching.

    Args:
        text: Input text

    Returns:
        ProcessedText with various representations
    """
    # Normalize
    normalized = preserve_turkish_lower(text)

    # Tokenize
    tokens = re.findall(r'\b\w+\b', normalized)

    # Remove stopwords
    keywords = [t for t in tokens if t not in TURKISH_STOPWORDS and len(t) > 2]

    # Stem
    stems = [turkish_stem(t) for t in keywords]

    return ProcessedText(
        original=text,
        normalized=normalized,
        tokens=tokens,
        stems=stems,
        keywords=keywords
    )


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract meaningful keywords from text."""
    processed = process_text(text)

    # Count keyword frequency
    keyword_counts: Dict[str, int] = {}
    for kw in processed.keywords:
        keyword_counts[kw] = keyword_counts.get(kw, 0) + 1

    # Sort by frequency
    sorted_keywords = sorted(
        keyword_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [kw for kw, _ in sorted_keywords[:max_keywords]]


# =============================================================================
# MATCHING UTILITIES
# =============================================================================

def text_contains_any(text: str, keywords: List[str], use_stems: bool = True) -> bool:
    """
    Check if text contains any of the keywords.
    Uses stemming and synonym expansion.

    Args:
        text: Text to search in
        keywords: Keywords to look for
        use_stems: Whether to use stemming

    Returns:
        True if any keyword matches
    """
    text_lower = text.lower()
    text_norm = normalize_turkish(text)

    # Expand keywords
    expanded = expand_keywords(keywords)

    # Check direct match
    for kw in expanded:
        if kw in text_lower or kw in text_norm:
            return True

    # Check stemmed match
    if use_stems:
        text_stems = set(stem_text(text))
        for kw in keywords:
            if turkish_stem(kw) in text_stems:
                return True

    return False


def calculate_keyword_score(text: str, keywords: List[str]) -> float:
    """
    Calculate how well text matches keywords.

    Args:
        text: Text to score
        keywords: Keywords to match

    Returns:
        Score between 0.0 and 1.0
    """
    if not keywords:
        return 0.0

    text_lower = text.lower()
    text_norm = normalize_turkish(text)
    text_stems = set(stem_text(text))

    matches = 0

    for kw in keywords:
        kw_lower = kw.lower()
        kw_norm = normalize_turkish(kw)
        kw_stem = turkish_stem(kw)

        # Direct match (highest weight)
        if kw_lower in text_lower or kw_norm in text_norm:
            matches += 1.0
        # Stem match (medium weight)
        elif kw_stem in text_stems:
            matches += 0.7
        # Synonym match (medium weight)
        elif any(syn in text_lower or syn in text_norm for syn in get_synonyms(kw)):
            matches += 0.8

    return min(1.0, matches / len(keywords))


# =============================================================================
# CLI TEST
# =============================================================================

if __name__ == "__main__":
    print("=== TURKISH NLP MODULE TEST ===\n")

    # Test stemming
    test_words = ["ekonomik", "eleştiriler", "hükümetin", "belediyeler", "başarısızlık"]
    print("STEMMING:")
    for word in test_words:
        print(f"  {word} → {turkish_stem(word)}")

    print("\nSYNONYMS:")
    test_synonyms = ["hükümet", "ekonomi", "eleştiri"]
    for word in test_synonyms:
        syns = get_synonyms(word)
        print(f"  {word} → {syns}")

    print("\nKEYWORD EXPANSION:")
    keywords = ["ekonomi", "hükümet"]
    expanded = expand_keywords(keywords)
    print(f"  {keywords} → {expanded}")

    print("\nTEXT MATCHING:")
    text = "İktidarın ekonomik politikaları eleştirildi"
    keywords = ["hükümet", "ekonomi", "eleştiri"]
    print(f"  Text: {text}")
    print(f"  Keywords: {keywords}")
    print(f"  Contains any: {text_contains_any(text, keywords)}")
    print(f"  Score: {calculate_keyword_score(text, keywords):.2f}")
