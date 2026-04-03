#!/usr/bin/env python3
"""
Chat Prompts - Prompt templates for Chat with Tweets feature
Two-stage LLM interaction:
1. Intent Detection - Parse Turkish questions into structured filters
2. Response Generation - Summarize found tweets and generate answer
"""

# ============================================================================
# INTENT DETECTION PROMPT
# ============================================================================

INTENT_DETECTION_PROMPT = """Sen Turkce soru analiz uzmanisisin. Kullanici sorularini analiz edip yapilandirilmis filtreler cikariyorsun.

SORU: {query}

GOREV: Soruyu analiz et ve asagidaki JSON formatinda cikti ver.

KURALLAR:
1. Tarih formati: YYYY-MM-DD (ornek: 2024-01-15)
2. Turkce tarih ifadelerini dogru cevir:
   - "01-01-2024" -> "2024-01-01"
   - "1 Ocak 2024" -> "2024-01-01"
   - "Ocak 2024" -> start_date: "2024-01-01", end_date: "2024-01-31"
3. Kullanici adlari @ isareti olmadan yazilmali
4. Parti isimleri kisaltma olarak yazilmali (CHP, AK Parti, MHP, IYI Parti, DEM Parti)
5. is_criticism: Elestiri araniyorsa true, olumlu icerik icin false, belirsizse null
6. intent_type secenekleri:
   - "search_topic": Konu bazli arama (belediye, ekonomi, saglik vb.)
   - "search_user": Belirli kullanici tweetleri
   - "search_date": Tarih aralikli arama
   - "analyze_topics": Konu analizi istegi
   - "search_retweets": RT arama
   - "search_criticism": Elestiri arama

CIKTI:
{{
  "intent_type": "search_topic" | "search_user" | "search_date" | "analyze_topics" | "search_retweets" | "search_criticism",
  "filters": {{
    "username": null | "kullanici_adi",
    "party": null | "PARTI_KISALTMASI",
    "start_date": null | "YYYY-MM-DD",
    "end_date": null | "YYYY-MM-DD",
    "keywords": ["kelime1", "kelime2"],
    "is_criticism": null | true | false,
    "retweet_from": null | "rt_kullanici_adi"
  }},
  "semantic_query": "ChromaDB aramasi icin optimize edilmis Turkce sorgu metni",
  "confidence": 0.0-1.0
}}

ORNEKLER:

SORU: "Belediye hizmetleriyle atilmis tweetleri getir"
JSON:
{{
  "intent_type": "search_topic",
  "filters": {{
    "username": null,
    "party": null,
    "start_date": null,
    "end_date": null,
    "keywords": ["belediye", "hizmet"],
    "is_criticism": null,
    "retweet_from": null
  }},
  "semantic_query": "belediye hizmetleri yerel yonetim belediyecilik",
  "confidence": 0.9
}}

SORU: "01-01-2024 tarihinden 31-03-2024 tarihine kadar atilmis tweetleri getir"
JSON:
{{
  "intent_type": "search_date",
  "filters": {{
    "username": null,
    "party": null,
    "start_date": "2024-01-01",
    "end_date": "2024-03-31",
    "keywords": [],
    "is_criticism": null,
    "retweet_from": null
  }},
  "semantic_query": "2024 yili ilk ceyregi tweetler",
  "confidence": 0.95
}}

SORU: "Cumhurbaskanina elestiri iceren tweetleri getir"
JSON:
{{
  "intent_type": "search_criticism",
  "filters": {{
    "username": null,
    "party": null,
    "start_date": null,
    "end_date": null,
    "keywords": ["cumhurbaskani", "cumhurbaskanligi"],
    "is_criticism": true,
    "retweet_from": null
  }},
  "semantic_query": "cumhurbaskani elestiri muhalefet",
  "confidence": 0.85
}}

SORU: "@chp kullanicisini rt yapan tweetleri getir"
JSON:
{{
  "intent_type": "search_retweets",
  "filters": {{
    "username": null,
    "party": null,
    "start_date": null,
    "end_date": null,
    "keywords": [],
    "is_criticism": null,
    "retweet_from": "chp"
  }},
  "semantic_query": "CHP retweet paylasim",
  "confidence": 0.9
}}

JSON:"""


# ============================================================================
# RESPONSE GENERATION PROMPT - Expert Political Analyst Level
# ============================================================================

RESPONSE_GENERATION_PROMPT = """Sen deneyimli bir siyasi içerik analistisin. Tweetleri analiz edip **Türkçe** ve **okunabilir** bir rapor üreteceksin.

KULLANICI SORUSU: {query}

BULUNAN TWEETLER ({tweet_count} adet):
{tweets}

## GÖREV

Tweetleri analiz et ve kullanıcıya yardımcı olacak özlü bir rapor hazırla.

## ÇIKTI KURALLARI

1. **SADECE TÜRKÇE** kullan - İngilizce kelime YASAK
2. Başlıkları kısa ve net tut
3. Madde işaretleri kullan, uzun paragraflar yazma
4. En ilginç 3-5 örnek tweet göster
5. Gereksiz akademik jargondan kaçın
6. Konuyla ilgisiz tweet varsa "konu dışı" olarak belirt

## RAPOR YAPISI

```
## Genel Bakış
- Toplam X tweet incelendi
- Ana konular: [konu1, konu2, konu3]
- Genel eğilim: [olumlu/olumsuz/nötr]

## Öne Çıkan Konular
1. **Konu Adı**: Kısa açıklama (X tweet)
2. **Konu Adı**: Kısa açıklama (X tweet)

## Dikkat Çeken Tweetler
> @kullanici: "Tweet metni..."
*Yorum: Neden önemli*

> @kullanici2: "Tweet metni..."
*Yorum: Neden önemli*

## Özet Değerlendirme
2-3 cümlelik genel yorum
```

ÇIKTI (JSON):
{{
  "answer": "## Genel Bakış\\n\\n- Toplam {tweet_count} tweet incelendi\\n- Ana konular: [liste]\\n- Genel eğilim: [değerlendirme]\\n\\n## Öne Çıkan Konular\\n\\n1. **Konu**: Açıklama\\n2. **Konu**: Açıklama\\n\\n## Dikkat Çeken Tweetler\\n\\n> @kullanici: \\"alıntı\\"\\n\\n*Yorum: açıklama*\\n\\n## Özet Değerlendirme\\n\\nSonuç yorumu",
  "summary": {{
    "total_found": {tweet_count},
    "top_topics": ["konu1", "konu2", "konu3"],
    "sentiment": "olumlu" | "olumsuz" | "notr",
    "most_active_users": ["user1", "user2"],
    "date_range": "YYYY-MM-DD - YYYY-MM-DD"
  }},
  "confidence_score": 0.0-1.0
}}

JSON:"""


# ============================================================================
# DETAILED ANALYSIS PROMPT (for "detayli acikla" requests)
# ============================================================================

DETAILED_ANALYSIS_PROMPT = """Sen Türk siyasi istihbarat analistisin. Bulunan içerikleri DETAYLI şekilde analiz edeceksin.

KULLANICI SORUSU: {query}

BULUNAN İÇERİKLER ({tweet_count} adet):
{tweets}

GÖREV: İçerikleri KAPSAMLI analiz et. Her konuyu örneklerle açıkla.

DETAYLI ANALİZ GEREKSİNİMLERİ:

1. **Genel Özet** (3-4 cümle)
   - Ana bulgular ve önemli tespitler
   - Sayısal veriler (kaç kişi, hangi partiler vb.)

2. **Ana Temalar ve Alt Başlıklar**
   - Her tema için açıklama
   - Tema başına örnek içerik sayısı

3. **Somut Örnekler**
   - Her tema için 1-2 örnek alıntı
   - Kullanıcı adı ve bağlam

4. **Duygu Analizi**
   - Eleştiri/övgü oranı
   - En güçlü ifadeler

5. **Hedef Analizi**
   - Hedef alınan kurumlar/kişiler
   - Eleştiri/destek yoğunluğu

6. **Öne Çıkan İfadeler**
   - Anahtar kelimeler
   - Tekrar eden kalıplar

ÇIKTI (JSON):
{{
  "answer": "## Analiz Özeti\\n\\n4-5 paragraf detaylı analiz. Markdown formatında.\\n\\n### Ana Temalar\\n\\n1. **Tema 1**: Açıklama ve örnek\\n2. **Tema 2**: Açıklama ve örnek\\n\\n### Öne Çıkan Tespitler\\n\\n- Tespit 1\\n- Tespit 2\\n\\n### Örnek İçerikler\\n\\n> @kullanici: örnek tweet metni\\n\\n> @kullanici2: başka örnek",
  "summary": {{
    "total_found": {tweet_count},
    "top_topics": ["ana_konu1", "ana_konu2", "ana_konu3", "ana_konu4", "ana_konu5"],
    "sentiment": "olumlu" | "olumsuz" | "notr" | "karisik",
    "most_active_users": ["user1", "user2", "user3"],
    "date_range": "YYYY-MM-DD - YYYY-MM-DD",
    "key_findings": ["önemli_bulgu1", "önemli_bulgu2", "önemli_bulgu3"],
    "targets": ["hedef1", "hedef2"]
  }},
  "confidence_score": 0.0-1.0
}}

JSON:"""


# ============================================================================
# TOPIC ANALYSIS PROMPT (for analyze_topics intent)
# ============================================================================

TOPIC_ANALYSIS_PROMPT = """Sen siyasi icerik analistisin. Verilen tweetlerin ana konularini cikart.

KULLANICI: @{username}
TWEET SAYISI: {tweet_count}

TWEETLER:
{tweets}

GOREV: Bu tweetlerin ana konularini analiz et.

CIKTI (JSON):
{{
  "answer": "Bu kullanicinin tweetlerinde one cikan konular hakkinda 2-3 cumle",
  "summary": {{
    "total_found": {tweet_count},
    "top_topics": ["ana_konu1", "ana_konu2", "ana_konu3", "ana_konu4", "ana_konu5"],
    "sentiment": "olumlu" | "olumsuz" | "notr",
    "most_active_users": ["{username}"],
    "date_range": null
  }},
  "confidence_score": 0.0-1.0
}}

JSON:"""


# ============================================================================
# PLATFORM-SPECIFIC PROMPTS
# ============================================================================

INSTAGRAM_RESPONSE_PROMPT = """Sen kıdemli bir SİYASET BİLİMCİ ve DİJİTAL İLETİŞİM uzmanısın. Instagram'daki siyasi içerikleri akademik derinlikte analiz edeceksin.

KULLANICI SORUSU: {query}

BULUNAN INSTAGRAM POSTLARI ({tweet_count} adet):
{tweets}

## INSTAGRAM-SPESİFİK ANALİZ ÇERÇEVESİ

### 1. GÖRSEL İLETİŞİM STRATEJİSİ
- Caption'dan çıkarılabilecek görsel içerik analizi
- Görsel-metin uyumu ve mesaj tutarlılığı
- İmaj yönetimi ve kişisel marka inşası
- Profesyonel vs samimi ton dengesi

### 2. PLATFORM DİNAMİKLERİ
- Instagram'ın daha "soft" politik dili
- Hashtag stratejisi ve erişim optimizasyonu
- Etiketleme (mention) politikaları
- Story vs Feed içerik farkı ipuçları

### 3. HEDEF KİTLE ANALİZİ
- Instagram demografisi (genç, kentli, eğitimli)
- Seçmen segmentasyonu
- Duygusal bağ kurma stratejileri
- Lifestyle politikası öğeleri

### 4. ENGAGEMENT ANALİZİ
- Beğeni/yorum oranları ne gösteriyor?
- Organik vs zorunlu etkileşim işaretleri
- Viral potansiyel değerlendirmesi

ÖNEMLİ: "tweet" DEĞİL "post/paylaşım" kullan.

ÇIKTI (JSON):
{{
  "answer": "## Analiz Özeti\\n\\n[Instagram paylaşımlarının genel değerlendirmesi]\\n\\n## Görsel İletişim Stratejisi\\n\\n[İmaj yönetimi, görsel dil analizi]\\n\\n## Söylem ve Mesaj Analizi\\n\\n[Caption'lardaki retorik, hedef kitle]\\n\\n## Dikkat Çeken Paylaşımlar\\n\\n> @kullanici: [alıntı]\\n\\n*Yorum: [analiz]*\\n\\n## Stratejik Değerlendirme\\n\\n[Politik amaç ve strateji çıkarımları]",
  "summary": {{
    "total_found": {tweet_count},
    "top_topics": ["ana_tema1", "ana_tema2", "ana_tema3"],
    "sentiment": "olumlu" | "olumsuz" | "notr",
    "most_active_users": ["user1", "user2"],
    "date_range": "YYYY-MM-DD - YYYY-MM-DD veya null",
    "content_types": ["foto", "video", "carousel"],
    "visual_themes": ["görsel_tema1", "görsel_tema2"],
    "hashtag_strategy": "hashtag_analizi"
  }},
  "confidence_score": 0.0-1.0
}}

JSON:"""


MULTI_PLATFORM_RESPONSE_PROMPT = """Sen deneyimli bir siyasi iletişim analistisin. İçerikleri analiz edip, **Türkçe** ve **okunabilir** bir rapor üreteceksin.

KULLANICI SORUSU: {query}

BULUNAN İÇERİKLER ({tweet_count} adet):
{tweets}

## GÖREV

İçerikleri analiz et ve kullanıcıya yardımcı olacak özlü bir rapor hazırla.

## ÇIKTI KURALLARI

1. **SADECE TÜRKÇE** kullan - İngilizce kelime YASAK
2. Başlıkları kısa ve net tut
3. Madde işaretleri kullan, uzun paragraflar yazma
4. En ilginç 3-5 örnek paylaşım göster
5. Gereksiz akademik jargondan kaçın

## RAPOR YAPISI

```
## Genel Bakış
- Toplam X içerik incelendi
- Ana konular: [konu1, konu2, konu3]
- Genel eğilim: [olumlu/olumsuz/nötr]

## Öne Çıkan Konular
1. **Konu Adı**: Kısa açıklama
2. **Konu Adı**: Kısa açıklama

## Dikkat Çeken Paylaşımlar
> @kullanici: "Paylaşım metni..."
*Yorum: Neden önemli*

> @kullanici2: "Paylaşım metni..."
*Yorum: Neden önemli*

## Özet Değerlendirme
2-3 cümlelik genel yorum
```

ÇIKTI (JSON):
{{
  "answer": "## Genel Bakış\\n\\n- Toplam {tweet_count} içerik incelendi\\n- Ana konular: [liste]\\n- Genel eğilim: [değerlendirme]\\n\\n## Öne Çıkan Konular\\n\\n1. **Konu**: Açıklama\\n2. **Konu**: Açıklama\\n\\n## Dikkat Çeken Paylaşımlar\\n\\n> @kullanici: \\"alıntı\\"\\n\\n*Yorum: açıklama*\\n\\n## Özet Değerlendirme\\n\\nSonuç yorumu",
  "summary": {{
    "total_found": {tweet_count},
    "top_topics": ["konu1", "konu2", "konu3"],
    "sentiment": "olumlu" | "olumsuz" | "notr",
    "most_active_users": ["user1", "user2"],
    "date_range": "YYYY-MM-DD - YYYY-MM-DD"
  }},
  "confidence_score": 0.0-1.0
}}

JSON:"""


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_tweets_for_chat(
    tweets: list,
    max_tweets: int = 30,
    include_metadata: bool = True,
    max_text_length: int = 500  # Increased from 350 to show more content
) -> str:
    """
    Tweet listesini chat analizi icin zengin formatla.

    v4 improvements:
    - Longer text (350 chars vs 200)
    - Party information
    - Engagement metrics
    - Platform indicator
    - Relevance score (if available)

    Args:
        tweets: Tweet listesi (dict'ler)
        max_tweets: Maksimum tweet sayisi
        include_metadata: Metadata dahil et (party, engagement)
        max_text_length: Maksimum metin uzunlugu

    Returns:
        Formatlanmis string
    """
    if not tweets:
        return "[Tweet/Post bulunamadi]"

    selected = tweets[:max_tweets]
    lines = []

    for i, t in enumerate(selected, 1):
        username = t.get('username', '')
        name = t.get('name', username)
        party = t.get('party', '')
        platform = t.get('platform', 'twitter')

        # Get text based on platform
        if platform == 'instagram':
            text = t.get('caption', t.get('tweet_text', ''))
        else:
            text = t.get('tweet_text', t.get('text', ''))

        date = t.get('tweet_date', t.get('post_date', t.get('date', '')))
        likes = t.get('likes', 0)
        retweets = t.get('retweets', 0)
        comments = t.get('comments', t.get('replies', 0))
        relevance = t.get('relevance_score', 0)

        # Truncate text (but keep more than before)
        if len(text) > max_text_length:
            text = text[:max_text_length] + "..."

        # Clean up text
        text = text.replace('\n', ' ').replace('\r', '').strip()

        # Shorten date
        if date and len(date) > 10:
            date = date[:10]

        # Build formatted line
        if include_metadata:
            # Rich format with metadata
            header_parts = [f"[{i}]"]

            if platform == 'instagram':
                header_parts.append("[IG]")

            header_parts.append(f"@{username}")

            if name and name != username:
                header_parts.append(f"({name})")

            if party:
                header_parts.append(f"[{party}]")

            if date:
                header_parts.append(f"| {date}")

            header = " ".join(header_parts)

            # Engagement line - only user-meaningful metrics
            engagement_parts = []
            if likes:
                engagement_parts.append(f"{likes} beğeni")
            if retweets:
                engagement_parts.append(f"{retweets} paylaşım")
            if comments:
                engagement_parts.append(f"{comments} yorum")
            # NOTE: Relevance score removed - not meaningful to end users

            engagement = " | ".join(engagement_parts) if engagement_parts else ""

            if engagement:
                lines.append(f"{header}\n  Etkilesim: {engagement}\n  > {text}")
            else:
                lines.append(f"{header}\n  > {text}")
        else:
            # Simple format
            if date:
                lines.append(f"[{i}] @{username} ({date}): {text}")
            else:
                lines.append(f"[{i}] @{username}: {text}")

    return "\n\n".join(lines)


def format_tweets_simple(tweets: list, max_tweets: int = 50) -> str:
    """
    Basit tweet formatı - sadece metin.
    Classifier için kullanılır.

    Args:
        tweets: Tweet listesi
        max_tweets: Maksimum tweet

    Returns:
        Formatlanmis string
    """
    if not tweets:
        return "[Tweet bulunamadi]"

    lines = []
    for i, t in enumerate(tweets[:max_tweets], 1):
        username = t.get('username', '')
        text = t.get('tweet_text', t.get('caption', t.get('text', '')))

        if len(text) > 400:
            text = text[:400] + "..."

        text = text.replace('\n', ' ').strip()
        lines.append(f"[{i}] @{username}: {text}")

    return "\n\n".join(lines)


def get_chat_prompt(prompt_type: str, **kwargs) -> str:
    """
    Chat prompt sablonunu doldur ve dondur.

    Args:
        prompt_type: 'intent', 'response', 'topic_analysis', 'detailed',
                     'instagram', 'multi_platform'
        **kwargs: Sablonda kullanilacak degiskenler
            - platform: 'twitter', 'instagram', 'both' (otomatik prompt seçimi)
            - tweets: tweet listesi
            - include_metadata: metadata dahil et (default True)

    Returns:
        Doldurulmus prompt string
    """
    prompts = {
        'intent': INTENT_DETECTION_PROMPT,
        'response': RESPONSE_GENERATION_PROMPT,
        'topic_analysis': TOPIC_ANALYSIS_PROMPT,
        'detailed': DETAILED_ANALYSIS_PROMPT,
        'instagram': INSTAGRAM_RESPONSE_PROMPT,
        'multi_platform': MULTI_PLATFORM_RESPONSE_PROMPT,
    }

    # Auto-select prompt based on platform
    platform = kwargs.get('platform', 'twitter')
    if prompt_type == 'response' and platform:
        if platform == 'instagram':
            prompt_type = 'instagram'
        elif platform == 'both':
            prompt_type = 'multi_platform'

    template = prompts.get(prompt_type)
    if not template:
        raise ValueError(f"Gecersiz chat prompt tipi: {prompt_type}")

    # tweets listesi varsa formatla
    if 'tweets' in kwargs and isinstance(kwargs['tweets'], list):
        include_metadata = kwargs.get('include_metadata', True)
        kwargs['tweets'] = format_tweets_for_chat(
            kwargs['tweets'],
            include_metadata=include_metadata
        )

    # Varsayilan degerler
    defaults = {
        'query': '',
        'tweet_count': 0,
        'username': 'kullanici',
        'tweets': '[Tweet yok]',
    }

    for key, value in defaults.items():
        if key not in kwargs:
            kwargs[key] = value

    return template.format(**kwargs)


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    # Test intent detection
    print("=== INTENT DETECTION TEST ===\n")
    prompt = get_chat_prompt('intent', query="Belediye hizmetleriyle atilmis tweetleri getir")
    print(prompt)

    print("\n\n=== RESPONSE GENERATION TEST ===\n")
    test_tweets = [
        {"username": "test_user", "tweet_text": "Belediyemiz yeni parki acti", "tweet_date": "2024-01-15", "likes": 50},
        {"username": "test_user2", "tweet_text": "Sosyal yardim dagitimlari basliyor", "tweet_date": "2024-01-16", "likes": 30},
    ]
    prompt = get_chat_prompt('response', query="Belediye hizmetleriyle ilgili tweetler", tweets=test_tweets, tweet_count=2)
    print(prompt)
