#!/usr/bin/env python3
"""
Prompts v4.0 - Advanced Prompt Engineering
Chain-of-thought, few-shot learning, role-based prompting
"""

# ============================================================================
# SYSTEM PROMPT - Role Definition
# ============================================================================

SYSTEM_PROMPT = """Türkiye siyaseti uzmanı istihbarat analistisin. Twitter analizleri yapıyorsun.

GÖREV: Politikacı tweetlerini analiz et - parti sadakati, muhalefet eleştirisi, bağımsız gündemler.

YÖNTEM:
1. Tweetleri oku, bağlamı anla
2. Orijinal tweet ve RT'leri ayır
3. Siyasi mesajları tespit et
4. Temaları ve kalıpları belirle
5. Somut örnekler ver
6. Sayısal veri kullan (yüzde, adet)

ÇIKTI: Sadece JSON."""


# ============================================================================
# INTELLIGENCE ANALYSIS PROMPT - Chain of Thought + Few-Shot
# ============================================================================

PROMPT_INTELLIGENCE_ANALYSIS_JSON = """Siyasi istihbarat analisti olarak @{username} hesabını analiz et.

HESAP: @{username} | Parti: {party} | Tweet: {tweet_count} | Dönem: {period}

GÖREV: Tweetleri okuyup 3 kategoride (Yeşil/Kırmızı/Gri) detaylı analiz yap.

ÖRNEK ANALİZ:
{{
  "executive_summary": "CHP meclis üyesi 117 paylaşımla analiz edildi. Parti sadakati yüksek, Cumhuriyet değerleri vurgusu öne çıkıyor. Muhalefet eleştirisi dolaylı ve yapıcı.",
  "green_summary": "85 tweetin %27'si parti etkinlikleri içeriyor. '29 Ekim coşkuyla kutlandı' (2,340 beğeni) ve 'Genel Başkan ziyareti' gibi paylaşımlar var. CHP belediye başkanlarıyla dayanışma mesajları düzenli.",
  "loyalty_level": "Yüksek",
  "red_summary": "Eleştiri ölçülü ve yapıcı. 85 tweetin sadece %9'u eleştirel. 'Market fiyatları yüksek' ve 'Altyapı yetersiz' gibi dolaylı eleştiriler var.",
  "criticism_level": "Düşük",
  "grey_summary": "Tweetlerin %41'i belediye hizmetleri. Park açılışları, sosyal yardım, kültürel etkinlikler öne çıkıyor. Spor kulüpleri ve taziye mesajları da mevcut.",
  "independent_topics": ["belediye hizmetleri", "sosyal yardım", "spor", "kültür-sanat"],
  "retweet_summary": "32 RT'nin %65'i CHP hesaplarından. CHP Genel Merkezi 8 RT ile en çok paylaşılan. %20 haber kaynakları, %15 sivil toplum.",
  "retweet_sources": ["@chp", "@chpizmir", "@izmirbbld"],
  "confidence_score": 0.88
}}

ORİJİNAL TWEETLER:
{tweets}

RETWEET İÇERİKLER:
{retweets}

ÇIKTI (JSON):"""


# ============================================================================
# SIMPLIFIED PROMPTS FOR OTHER TASKS
# ============================================================================

PROMPT_MAIN_TOPICS_JSON = """Aşağıdaki tweetleri oku ve en önemli 3-5 ana temayı belirle.

Tweetler:
{tweets}

JSON formatında yanıt ver:
{{"topics": ["tema1", "tema2", "tema3"]}}

JSON:"""


PROMPT_PARTY_DEFENSE_JSON = """Aşağıdaki tweetleri analiz et.

Soru: Bu kişi hangi partiyi/lideri destekliyor ve ne kadar güçlü destekliyor?

Tweetler:
{tweets}

JSON formatında yanıt ver:
{{"defended_party": "parti adı veya Yok", "intensity": "Güçlü/Orta/Zayıf/Yok"}}

JSON:"""


PROMPT_OPPOSITION_CRITICISM_JSON = """Aşağıdaki tweetleri analiz et.

Soru: Bu kişi hangi partiyi/kişiyi eleştiriyor ve eleştiri ne kadar sert?

Tweetler:
{tweets}

JSON formatında yanıt ver:
{{"criticized_party": "parti/kişi adı veya Yok", "intensity": "Sert/Orta/Hafif/Yok"}}

JSON:"""


PROMPT_FULL_ANALYSIS_JSON = """## Siyasi İletişim Analizi

**Hesap:** @{username}
**Parti:** {party}
**Tweet Sayısı:** {tweet_count}
**Dönem:** {period}

Aşağıdaki tweetleri analiz et ve JSON formatında yanıt ver.

Tweetler:
{tweets}

JSON:
{{
  "main_topics": ["en önemli 3-5 konu"],
  "defended_party": "desteklenen parti/lider veya Yok",
  "defense_intensity": "Güçlü/Orta/Zayıf/Yok",
  "criticized_party": "eleştirilen parti/kişi veya Yok",
  "criticism_intensity": "Sert/Orta/Hafif/Yok",
  "summary": "2-3 cümlelik genel değerlendirme"
}}

JSON yanıtı:"""


# ============================================================================
# COMPARISON PROMPT - For comparing 2 users
# ============================================================================

PROMPT_COMPARISON_JSON = """Siyasi istihbarat analisti olarak 2 meclis üyesini karşılaştır.

KULLANICI 1: @{username1} | Parti: {party1}
KULLANICI 2: @{username2} | Parti: {party2}

GÖREV: İki politikacının sosyal medya aktivitelerini karşılaştır ve farklılıkları/benzerlikleri belirle.

@{username1} TWEETLERİ:
{tweets1}

@{username2} TWEETLERİ:
{tweets2}

ÇIKTI (JSON):
{{
  "comparison_summary": "Genel karşılaştırma özeti (2-3 cümle)",
  "user1_profile": {{
    "username": "@{username1}",
    "dominant_theme": "En baskın tema",
    "political_stance": "Siyasi duruş özeti",
    "activity_level": "Yüksek/Orta/Düşük"
  }},
  "user2_profile": {{
    "username": "@{username2}",
    "dominant_theme": "En baskın tema",
    "political_stance": "Siyasi duruş özeti",
    "activity_level": "Yüksek/Orta/Düşük"
  }},
  "similarities": ["Ortak özellik 1", "Ortak özellik 2"],
  "differences": ["Fark 1", "Fark 2", "Fark 3"],
  "common_topics": ["Ortak konu 1", "Ortak konu 2"],
  "recommendation": "Karşılaştırma bazlı öneri/yorum",
  "confidence_score": 0.85
}}

JSON:"""


# ============================================================================
# MULTI-PLATFORM PROMPT
# ============================================================================

PROMPT_MULTI_PLATFORM_JSON = """Siyasi istihbarat analisti olarak @{username} hesabını analiz et.

HESAP: @{username} | Parti: {party} | Platformlar: {platforms}

GÖREV: Hem Twitter hem Instagram paylaşımlarını okuyup karşılaştırmalı analiz yap.

TWITTER PAYLAŞIMLARI:
{tweets}

INSTAGRAM PAYLAŞIMLARI:
{instagram_posts}

ANALIZ TALEPLERI:
1. Her platformdaki mesaj tutarlılığı
2. Platform-spesifik stratejiler (görsel vs metin ağırlıklı)
3. Kitle farklılıkları ve hedefleme
4. Parti sadakati ve muhalefet tutumu

ÇIKTI (JSON):
{{
  "executive_summary": "2-3 cümlelik genel değerlendirme",
  "platform_comparison": {{
    "consistency": "Tutarlı/Kısmen Tutarlı/Farklı",
    "twitter_focus": "Twitter'daki ana tema",
    "instagram_focus": "Instagram'daki ana tema",
    "audience_difference": "Kitle farkı analizi"
  }},
  "green_summary": "Parti sadakati analizi (her iki platform)",
  "loyalty_level": "Yüksek/Orta/Düşük",
  "red_summary": "Muhalefet eleştirisi analizi (her iki platform)",
  "criticism_level": "Yüksek/Orta/Düşük",
  "grey_summary": "Bağımsız gündemler (her iki platform)",
  "independent_topics": ["konu1", "konu2", "konu3"],
  "recommendation": "Platform stratejisi önerisi",
  "confidence_score": 0.85
}}

JSON:"""


# ============================================================================
# INSTAGRAM-ONLY PROMPT
# ============================================================================

PROMPT_INSTAGRAM_ANALYSIS_JSON = """Siyasi istihbarat analisti olarak @{username} Instagram hesabını analiz et.

HESAP: @{username} | Parti: {party} | Post Sayısı: {post_count}

GÖREV: Instagram paylaşımlarını okuyup 3 kategoride (Yeşil/Kırmızı/Gri) analiz yap.

INSTAGRAM PAYLAŞIMLARI:
{instagram_posts}

ÇIKTI (JSON):
{{
  "executive_summary": "2-3 cümlelik genel değerlendirme",
  "green_summary": "Parti sadakati içeren paylaşımlar analizi",
  "loyalty_level": "Yüksek/Orta/Düşük",
  "red_summary": "Eleştirel paylaşımlar analizi",
  "criticism_level": "Yüksek/Orta/Düşük",
  "grey_summary": "Apolitik/kişisel paylaşımlar",
  "independent_topics": ["konu1", "konu2", "konu3"],
  "visual_strategy": "Görsel içerik stratejisi (foto/video kullanımı)",
  "engagement_pattern": "Etkileşim kalıbı analizi",
  "confidence_score": 0.85
}}

JSON:"""


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_instagram_for_prompt(posts: list, max_posts: int = 25) -> str:
    """
    Instagram post listesini analiz için formatla.

    Args:
        posts: Instagram post listesi
        max_posts: Maksimum post sayısı (default: 25)
    """
    if not posts:
        return "[Instagram verisi yok]"

    selected = posts[:max_posts]

    lines = []
    for i, p in enumerate(selected, 1):
        caption = p.get('caption', p.get('text', ''))
        if caption and len(caption) > 200:
            caption = caption[:200] + "..."

        date = p.get('post_date', p.get('date', ''))
        if date and len(date) > 10:
            date = date[:10]

        media_type = "Video" if p.get('is_video') else "Foto"
        likes = p.get('likes', 0)
        comments = p.get('comments', 0)

        if date:
            lines.append(f"[{i}] {media_type} ({date}) [{likes} like, {comments} yorum] {caption}")
        else:
            lines.append(f"[{i}] {media_type} [{likes} like, {comments} yorum] {caption}")

    return "\n".join(lines)


def format_tweets_for_prompt(tweets: list, max_tweets: int = 25, include_metrics: bool = False) -> str:
    """
    Tweet listesini analiz için formatla.
    Her tweet numaralı ve temiz şekilde sunulur.

    Args:
        tweets: Tweet listesi
        max_tweets: Maksimum tweet sayısı (default: 25)
        include_metrics: Metrik bilgilerini ekle (default: False, token tasarrufu)
    """
    if not tweets:
        return "[Tweet yok]"

    # En fazla max_tweets tweet al
    selected = tweets[:max_tweets]

    lines = []
    for i, t in enumerate(selected, 1):
        text = t.get('text', t.get('tweet_text', ''))
        date = t.get('date', t.get('tweet_date', ''))

        # Tweet metnini 200 karakterle sınırla
        if len(text) > 200:
            text = text[:200] + "..."

        # Tarihi kısalt
        if date and len(date) > 10:
            date = date[:10]

        # Basit format (token tasarrufu)
        if date:
            lines.append(f"[{i}] ({date}) {text}")
        else:
            lines.append(f"[{i}] {text}")

    return "\n".join(lines)


def format_retweets_for_prompt(retweets: list, max_tweets: int = 20) -> str:
    """
    Retweet listesini analiz için formatla.
    Retweet kaynağını ve içeriği gösterir.
    """
    if not retweets:
        return "[RT yok]"

    # En fazla max_tweets retweet al
    selected = retweets[:max_tweets]

    lines = []
    for i, t in enumerate(selected, 1):
        text = t.get('text', t.get('tweet_text', ''))
        date = t.get('date', t.get('tweet_date', ''))
        retweet_from = t.get('retweet_from', 'bilinmiyor')

        # Tweet metnini 200 karakterle sınırla
        if len(text) > 200:
            text = text[:200] + "..."

        # Tarihi kısalt
        if date and len(date) > 10:
            date = date[:10]

        # Basit format
        if date:
            lines.append(f"[{i}] RT @{retweet_from} ({date}): {text}")
        else:
            lines.append(f"[{i}] RT @{retweet_from}: {text}")

    return "\n".join(lines)


def get_prompt(prompt_type: str, **kwargs) -> str:
    """
    Prompt şablonunu doldur ve döndür.

    Args:
        prompt_type: 'intelligence', 'full', 'main_topics', 'party_defense', 'opposition',
                     'comparison', 'multi_platform', 'instagram'
        **kwargs: Şablonda kullanılacak değişkenler
            - tweets: Orijinal tweet listesi
            - retweets: Retweet listesi (intelligence prompt için)
            - tweets1, tweets2: Karşılaştırma için tweet listeleri
            - instagram_posts: Instagram post listesi (multi_platform/instagram için)

    Returns:
        Doldurulmuş prompt string
    """
    prompts = {
        'intelligence': PROMPT_INTELLIGENCE_ANALYSIS_JSON,
        'full': PROMPT_FULL_ANALYSIS_JSON,
        'main_topics': PROMPT_MAIN_TOPICS_JSON,
        'party_defense': PROMPT_PARTY_DEFENSE_JSON,
        'opposition': PROMPT_OPPOSITION_CRITICISM_JSON,
        'comparison': PROMPT_COMPARISON_JSON,
        'multi_platform': PROMPT_MULTI_PLATFORM_JSON,
        'instagram': PROMPT_INSTAGRAM_ANALYSIS_JSON
    }

    template = prompts.get(prompt_type)
    if not template:
        raise ValueError(f"Geçersiz prompt tipi: {prompt_type}")

    # tweets listesi varsa formatla
    if 'tweets' in kwargs and isinstance(kwargs['tweets'], list):
        kwargs['tweets'] = format_tweets_for_prompt(kwargs['tweets'])

    # Karşılaştırma için tweets1 ve tweets2
    if 'tweets1' in kwargs and isinstance(kwargs['tweets1'], list):
        kwargs['tweets1'] = format_tweets_for_prompt(kwargs['tweets1'])
    if 'tweets2' in kwargs and isinstance(kwargs['tweets2'], list):
        kwargs['tweets2'] = format_tweets_for_prompt(kwargs['tweets2'])

    # instagram_posts listesi varsa formatla
    if 'instagram_posts' in kwargs and isinstance(kwargs['instagram_posts'], list):
        kwargs['instagram_posts'] = format_instagram_for_prompt(kwargs['instagram_posts'])
    elif 'instagram_posts' not in kwargs:
        kwargs['instagram_posts'] = "[Instagram verisi mevcut değil]"

    # retweets listesi varsa formatla (intelligence prompt için)
    if 'retweets' in kwargs and isinstance(kwargs['retweets'], list):
        kwargs['retweets'] = format_retweets_for_prompt(kwargs['retweets'])
    elif 'retweets' not in kwargs:
        kwargs['retweets'] = "[Retweet verisi mevcut değil]"

    # Varsayılan değerler
    defaults = {
        'party': 'Bilinmiyor',
        'username': 'kullanici',
        'tweet_count': 0,
        'post_count': 0,
        'period': 'Tüm zamanlar',
        'platforms': 'twitter',
        'username1': 'kullanici1',
        'username2': 'kullanici2',
        'party1': 'Bilinmiyor',
        'party2': 'Bilinmiyor'
    }

    for key, value in defaults.items():
        if key not in kwargs:
            kwargs[key] = value

    return template.format(**kwargs)


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    test_tweets = [
        {"tweet_text": "Cumhuriyetimizin 100. yılında Atatürk'ü saygıyla anıyoruz.", "tweet_date": "2024-10-29"},
        {"tweet_text": "Belediyemiz yeni parkları hizmete açtı. Hemşehrilerimize hayırlı olsun!", "tweet_date": "2024-10-25"},
        {"tweet_text": "AKP'nin ekonomi politikaları halkı mağdur ediyor.", "tweet_date": "2024-10-20"},
        {"tweet_text": "Genel Başkanımız Özgür Özel'in yanındayız.", "tweet_date": "2024-10-15"},
    ]

    print("=== INTELLIGENCE PROMPT TEST ===\n")
    prompt = get_prompt('intelligence',
                        tweets=test_tweets,
                        username="test_meclis_uyesi",
                        party="CHP",
                        tweet_count=4)
    print(prompt)
