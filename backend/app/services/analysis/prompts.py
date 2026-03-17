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
# HELPER FUNCTIONS
# ============================================================================

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
        prompt_type: 'intelligence', 'full', 'main_topics', 'party_defense', 'opposition'
        **kwargs: Şablonda kullanılacak değişkenler
            - tweets: Orijinal tweet listesi
            - retweets: Retweet listesi (intelligence prompt için)

    Returns:
        Doldurulmuş prompt string
    """
    prompts = {
        'intelligence': PROMPT_INTELLIGENCE_ANALYSIS_JSON,
        'full': PROMPT_FULL_ANALYSIS_JSON,
        'main_topics': PROMPT_MAIN_TOPICS_JSON,
        'party_defense': PROMPT_PARTY_DEFENSE_JSON,
        'opposition': PROMPT_OPPOSITION_CRITICISM_JSON
    }

    template = prompts.get(prompt_type)
    if not template:
        raise ValueError(f"Geçersiz prompt tipi: {prompt_type}")

    # tweets listesi varsa formatla
    if 'tweets' in kwargs and isinstance(kwargs['tweets'], list):
        kwargs['tweets'] = format_tweets_for_prompt(kwargs['tweets'])

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
        'period': 'Tüm zamanlar'
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
