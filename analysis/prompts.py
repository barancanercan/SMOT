#!/usr/bin/env python3
"""
Prompts v1.0 - Turkce LLM Prompt Sablonlari

3 Analiz Sorusu:
1. Ana konular nedir?
2. Parti/lider savunusu
3. Muhalefet elestirisi
"""

# ============================================================================
# SISTEM PROMPTLARI
# ============================================================================

SYSTEM_PROMPT = """Sen bir siyasi analiz uzmanısin. Twitter/X paylasimlari uzerinden milletvekillerinin siyasi durusunu analiz ediyorsun.

Kurallar:
- Sadece verilen tweetlere dayanarak analiz yap
- Tarafsiz ve objektif ol
- Turkce yanit ver
- Kisa ve oz yanıtlar ver
- Spekülasyon yapma, sadece tweetlerdeki acik ifadeleri kullan"""


# ============================================================================
# SORU 1: ANA KONULAR
# ============================================================================

PROMPT_MAIN_TOPICS = """Asagidaki tweetleri analiz et ve bu kisinin en cok hangi konularda paylasim yaptigini belirle.

TWEETLER:
{tweets}

GOREV:
1. En cok vurgulanan 5 ana konuyu listele
2. Her konu icin kac tweet oldugunu belirt
3. Kisaca ozeti yaz

FORMAT:
## Ana Konular

1. **[Konu Adi]** (X tweet)
   - Kisa aciklama

2. **[Konu Adi]** (X tweet)
   - Kisa aciklama

...

## Ozet
[1-2 cumlelik genel degerlendirme]"""


# ============================================================================
# SORU 2: PARTI/LIDER SAVUNUSU
# ============================================================================

PROMPT_PARTY_DEFENSE = """Asagidaki tweetleri analiz et ve bu kisinin parti/lider savunusu yapip yapmadigini belirle.

TWEETLER:
{tweets}

GOREV:
1. Hangi parti veya lideri savundugunu belirle
2. Savunma iceren tweet ornekleri ver (en fazla 3)
3. Savunma siddeti: Guclu / Orta / Zayif / Yok

FORMAT:
## Parti/Lider Savunusu Analizi

**Savunulan Parti/Lider:** [Isim veya "Belirgin savunma yok"]

**Savunma Siddeti:** [Guclu/Orta/Zayif/Yok]

**Ornek Tweetler:**
1. "[Tweet metni]"
2. "[Tweet metni]"

**Degerlendirme:**
[1-2 cumlelik analiz]"""


# ============================================================================
# SORU 3: MUHALEFET ELESTIRISI
# ============================================================================

PROMPT_OPPOSITION_CRITICISM = """Asagidaki tweetleri analiz et ve bu kisinin muhalefete yonelik elestirileri belirle.

TWEETLER:
{tweets}

GOREV:
1. Hangi parti veya kisileri elestirdigini belirle
2. Elestiri iceren tweet ornekleri ver (en fazla 3)
3. Elestiri siddeti: Sert / Orta / Hafif / Yok

FORMAT:
## Muhalefet Elestirisi Analizi

**Elestirilen Parti/Kisiler:** [Isimler veya "Belirgin elestiri yok"]

**Elestiri Siddeti:** [Sert/Orta/Hafif/Yok]

**Ornek Tweetler:**
1. "[Tweet metni]"
2. "[Tweet metni]"

**Degerlendirme:**
[1-2 cumlelik analiz]"""


# ============================================================================
# GENEL ANALIZ (TUM SORULAR BIR ARADA)
# ============================================================================

PROMPT_FULL_ANALYSIS = """Asagidaki tweetleri detayli analiz et.

KULLANICI: @{username}
TWEET SAYISI: {tweet_count}
DONEM: {period}

TWEETLER:
{tweets}

GOREV:
Asagidaki 3 soruyu yanitla:

1. ANA KONULAR: Bu kisi en cok hangi konularda paylasim yapiyor? (En az 3, en fazla 5 konu)

2. PARTI SAVUNUSU: Hangi parti veya lideri savunuyor? Ornekler ver.

3. MUHALEFET ELESTIRISI: Kimleri elestiriyor? Ornekler ver.

FORMAT:
## 1. Ana Konular
- [Konu 1]: [Kisa aciklama]
- [Konu 2]: [Kisa aciklama]
- [Konu 3]: [Kisa aciklama]

## 2. Parti/Lider Savunusu
**Savunulan:** [Parti/Lider adi veya "Yok"]
**Ornek:** "[Tweet]"
**Siddet:** [Guclu/Orta/Zayif/Yok]

## 3. Muhalefet Elestirisi
**Elestirilen:** [Parti/Kisi adi veya "Yok"]
**Ornek:** "[Tweet]"
**Siddet:** [Sert/Orta/Hafif/Yok]

## Genel Degerlendirme
[2-3 cumlelik ozet]"""


# ============================================================================
# YARDIMCI FONKSIYONLAR
# ============================================================================

def format_tweets_for_prompt(tweets: list, max_tweets: int = 30) -> str:
    """
    Tweet listesini prompt icin formatla

    Args:
        tweets: Tweet listesi [{'text': str, 'date': str, ...}, ...]
        max_tweets: Maksimum tweet sayisi

    Returns:
        Formatli tweet metni
    """
    if not tweets:
        return "[Tweet bulunamadi]"

    # En fazla max_tweets kadar al
    tweets = tweets[:max_tweets]

    lines = []
    for i, t in enumerate(tweets, 1):
        text = t.get('text', t.get('tweet_text', ''))
        date = t.get('date', t.get('tweet_date', ''))

        if date:
            lines.append(f"{i}. [{date}] {text}")
        else:
            lines.append(f"{i}. {text}")

    return "\n".join(lines)


def get_prompt(prompt_type: str, **kwargs) -> str:
    """
    Prompt sablonunu doldur

    Args:
        prompt_type: 'main_topics', 'party_defense', 'opposition', 'full'
        **kwargs: Sablon degiskenleri (tweets, username, etc.)

    Returns:
        Doldurulmus prompt
    """
    prompts = {
        'main_topics': PROMPT_MAIN_TOPICS,
        'party_defense': PROMPT_PARTY_DEFENSE,
        'opposition': PROMPT_OPPOSITION_CRITICISM,
        'full': PROMPT_FULL_ANALYSIS
    }

    template = prompts.get(prompt_type)
    if not template:
        raise ValueError(f"Gecersiz prompt tipi: {prompt_type}")

    # tweets listesi varsa formatla
    if 'tweets' in kwargs and isinstance(kwargs['tweets'], list):
        kwargs['tweets'] = format_tweets_for_prompt(kwargs['tweets'])

    return template.format(**kwargs)


# ============================================================================
# CLI TEST
# ============================================================================

if __name__ == "__main__":
    # Test
    test_tweets = [
        {"text": "Ekonomi politikamiz cok basarili", "date": "2024-01-01"},
        {"text": "Muhalefet yanlis yolda", "date": "2024-01-02"},
        {"text": "Liderimize tam destek", "date": "2024-01-03"},
    ]

    print("=== PROMPT TEST ===\n")

    prompt = get_prompt('main_topics', tweets=test_tweets)
    print("MAIN TOPICS PROMPT:")
    print(prompt[:500])
    print("...\n")

    prompt = get_prompt('full',
                        tweets=test_tweets,
                        username="test_user",
                        tweet_count=3,
                        period="2024-01-01 - 2024-01-03")
    print("FULL ANALYSIS PROMPT:")
    print(prompt[:500])
    print("...")