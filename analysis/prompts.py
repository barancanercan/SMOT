#!/usr/bin/env python3
"""
Prompts v2.0 - Profesyonel Turkce LLM Prompt Sablonlari

Analiz Kategorileri:
1. Tematik Analiz (Ana konular)
2. Siyasi Pozisyon Analizi (Parti/lider savunusu)
3. Elestiri Analizi (Muhalefet elestirisi)
"""

# ============================================================================
# SISTEM PROMPTU
# ============================================================================

SYSTEM_PROMPT = """Sen deneyimli bir siyasi iletisim ve sosyal medya analistisin.
Gorev: Turkiye Buyuk Millet Meclisi uyelerinin Twitter/X paylasimlari uzerinden siyasi iletisim stratejilerini analiz etmek.

Analiz Ilkeleri:
- Sadece verilen tweet verileriyle sinirli kal, disaridan bilgi ekleme
- Objektif ve tarafsiz bir dil kullan
- Somut orneklerle destekle
- Akademik ve profesyonel bir uslup benimse
- Spekulasyondan kacin, dogrudan gozlemlere dayan
- Turkce terminoloji kullan

Cikti Formati: Yapilandirilmis markdown formatinda, basliklar ve maddeler halinde."""


# ============================================================================
# SORU 1: TEMATIK ANALIZ
# ============================================================================

PROMPT_MAIN_TOPICS = """## Tematik Icerik Analizi

Asagidaki tweet arsivini inceleyerek kullanicinin iletisim stratejisindeki ana temalari belirle.

**Tweet Arsivi:**
{tweets}

**Analiz Gereksinimleri:**
1. En sik islenen 5 ana temayi tespit et
2. Her tema icin frekans ve ornek tweet belirt
3. Genel iletisim stratejisi hakkinda degerlendirme yap

**Beklenen Cikti Formati:**

### Ana Temalar

1. **[Tema Adi]** (X tweet)
   - Aciklama: [Temanin nasil islendigi]
   - Ornek: "[Tweet alintisi]"

2. **[Tema Adi]** (X tweet)
   - Aciklama: [Temanin nasil islendigi]
   - Ornek: "[Tweet alintisi]"

[Diger temalar...]

### Iletisim Stratejisi Degerlendirmesi
[Kullanicinin genel iletisim yaklasimi hakkinda 2-3 cumlelik profesyonel degerlendirme]"""


# ============================================================================
# SORU 2: SIYASI POZISYON ANALIZI
# ============================================================================

PROMPT_PARTY_DEFENSE = """## Siyasi Pozisyon Analizi

Asagidaki tweet arsivini inceleyerek kullanicinin parti/lider destegi baglamindaki pozisyonunu analiz et.

**Tweet Arsivi:**
{tweets}

**Analiz Gereksinimleri:**
1. Desteklenen parti veya siyasi lider(ler)i tespit et
2. Destek ifadelerinin yogunlugunu degerlendir
3. Somut ornek tweetler sun

**Beklenen Cikti Formati:**

### Siyasi Destek Analizi

**Desteklenen Parti/Lider:** [Tespit edilen isim(ler) veya "Belirgin destek ifadesi yok"]

**Destek Yogunlugu:** [Yuksek / Orta / Dusuk / Belirsiz]

**Kanitlayici Ornekler:**
1. "[Tweet alintisi]" - [Kisa yorum]
2. "[Tweet alintisi]" - [Kisa yorum]

### Degerlendirme
[Siyasi pozisyon hakkinda objektif, 2-3 cumlelik analiz]"""


# ============================================================================
# SORU 3: ELESTIRI ANALIZI
# ============================================================================

PROMPT_OPPOSITION_CRITICISM = """## Siyasi Elestiri Analizi

Asagidaki tweet arsivini inceleyerek kullanicinin muhalefet partileri/siyasetcilere yonelik elestirel tutumunu analiz et.

**Tweet Arsivi:**
{tweets}

**Analiz Gereksinimleri:**
1. Elestiri yoneltilen parti veya siyasetcileri tespit et
2. Elestiri tonunu ve yogunlugunu degerlendir
3. Somut ornek tweetler sun

**Beklenen Cikti Formati:**

### Elestiri Analizi

**Elestirilen Taraf(lar):** [Tespit edilen isim(ler) veya "Belirgin elestiri yok"]

**Elestiri Tonu:** [Sert / Olculu / Hafif / Belirsiz]

**Kanitlayici Ornekler:**
1. "[Tweet alintisi]" - [Kisa yorum]
2. "[Tweet alintisi]" - [Kisa yorum]

### Degerlendirme
[Elestirel tutum hakkinda objektif, 2-3 cumlelik analiz]"""


# ============================================================================
# KAPSAMLI ANALIZ (TUM KATEGORILER)
# ============================================================================

PROMPT_FULL_ANALYSIS = """## Kapsamli Siyasi Iletisim Analizi

**Meclis Uyesi:** @{username}
**Parti:** {party}
**Analiz Edilen Tweet Sayisi:** {tweet_count}
**Analiz Donemi:** {period}

---

**Tweet Arsivi:**
{tweets}

---

**Analiz Gereksinimleri:**

Asagidaki uc kategoriyi ayrintili sekilde analiz et:

### 1. TEMATIK ANALIZ
- En sik islenen konulari tespit et (en az 3, en fazla 5)
- Her konu icin somut tweet ornegi ver

### 2. SIYASI POZISYON
- Parti veya lider destegi var mi? Kim(ler)?
- Destek yogunlugunu degerlendir (Yuksek/Orta/Dusuk/Yok)
- Ornek tweet(ler) sun

### 3. ELESTIRI ANALIZI
- Hangi parti veya siyasetcilere elestiri var?
- Elestiri tonunu degerlendir (Sert/Olculu/Hafif/Yok)
- Ornek tweet(ler) sun

---

**Beklenen Cikti Formati:**

## 1. Tematik Analiz

| Tema | Aciklama |
|------|----------|
| [Tema 1] | [Kisa aciklama] |
| [Tema 2] | [Kisa aciklama] |
| [Tema 3] | [Kisa aciklama] |

**Ornek Tweetler:**
- "[Tweet alintisi]"

## 2. Siyasi Pozisyon

**Desteklenen:** [Parti/Lider veya "Belirgin destek yok"]
**Yogunluk:** [Yuksek/Orta/Dusuk/Yok]
**Ornek:** "[Tweet alintisi]"

## 3. Elestiri Analizi

**Elestirilen:** [Parti/Kisi veya "Belirgin elestiri yok"]
**Ton:** [Sert/Olculu/Hafif/Yok]
**Ornek:** "[Tweet alintisi]"

## Genel Degerlendirme

[Meclis uyesinin siyasi iletisim stratejisi hakkinda 3-4 cumlelik profesyonel ve objektif bir ozet. Parti aidiyeti ({party}) baglaminda tutarlilik degerlendirmesi de dahil edilebilir.]"""


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
        return "[Tweet verisi bulunamadi]"

    # En fazla max_tweets kadar al
    tweets = tweets[:max_tweets]

    lines = []
    for i, t in enumerate(tweets, 1):
        text = t.get('text', t.get('tweet_text', ''))
        date = t.get('date', t.get('tweet_date', ''))

        # Tarihi formatla
        if date:
            # ISO formatindan sadece tarihi al
            date_short = str(date)[:10] if len(str(date)) > 10 else date
            lines.append(f"[{i}] ({date_short}) {text}")
        else:
            lines.append(f"[{i}] {text}")

    return "\n\n".join(lines)


def get_prompt(prompt_type: str, **kwargs) -> str:
    """
    Prompt sablonunu doldur

    Args:
        prompt_type: 'main_topics', 'party_defense', 'opposition', 'full'
        **kwargs: Sablon degiskenleri (tweets, username, party, etc.)

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

    # Varsayilan degerler
    if 'party' not in kwargs:
        kwargs['party'] = 'Bilinmiyor'

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
                        party="AKP",
                        tweet_count=3,
                        period="2024-01-01 - 2024-01-03")
    print("FULL ANALYSIS PROMPT:")
    print(prompt)
