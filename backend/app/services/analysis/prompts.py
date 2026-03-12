#!/usr/bin/env python3
"""
Prompts v4.0 - Advanced Prompt Engineering
Chain-of-thought, few-shot learning, role-based prompting
"""

# ============================================================================
# SYSTEM PROMPT - Role Definition
# ============================================================================

SYSTEM_PROMPT = """Sen Türkiye siyaseti konusunda uzman bir istihbarat analistisin.

GÖREVIN:
- Politikacıların Twitter paylaşımlarını derinlemesine analiz etmek
- Parti sadakati, muhalefet eleştirisi ve bağımsız gündemleri tespit etmek
- Kanıta dayalı, objektif değerlendirmeler yapmak

ANALIZ YAKLAŞIMIN:
1. Her tweeti dikkatlice oku
2. Siyasi mesajları, ima edilen anlamları ve alt metinleri tespit et
3. Tekrar eden temaları ve kalıpları belirle
4. Somut örneklerle destekle

ÇIKTI FORMATI: Sadece JSON. Açıklama veya ek metin yok."""


# ============================================================================
# INTELLIGENCE ANALYSIS PROMPT - Chain of Thought + Few-Shot
# ============================================================================

PROMPT_INTELLIGENCE_ANALYSIS_JSON = """Bir siyasi istihbarat analisti olarak aşağıdaki Twitter hesabını analiz et.

## HESAP BİLGİLERİ
- Kullanıcı: @{username}
- Parti: {party}
- Analiz edilen tweet sayısı: {tweet_count}

## ÖRNEK ANALİZ (Referans için)

Örnek hesap: @ornek_chp_uyesi (CHP, 45 tweet)

Örnek JSON çıktısı:
{{
  "executive_summary": "CHP'li belediye başkanı olarak yerel hizmetlere odaklanan, parti çizgisine sadık bir profil. Atatürk ve Cumhuriyet vurgusu güçlü. Doğrudan muhalefet eleştirisi yapmaktan kaçınıyor, yapıcı bir dil kullanıyor.",
  "green_summary": "Parti liderliğine açık destek veriyor, CHP'li diğer belediye başkanlarıyla dayanışma içinde. Cumhuriyet değerlerini ve Atatürk ilkelerini sıkça vurguluyor. Parti etkinliklerine aktif katılım gösteriyor.",
  "loyalty_level": "Yüksek",
  "red_summary": "Doğrudan isim vererek eleştiri yapmıyor. Ekonomik sıkıntılar ve hizmet aksaklıkları üzerinden dolaylı eleştiriler mevcut. Genel olarak yapıcı muhalefet anlayışı sergiliyor.",
  "criticism_level": "Düşük",
  "grey_summary": "Belediye hizmetleri, altyapı projeleri ve yerel etkinlikler ağırlıklı. Spor kulüpleri ve kültürel faaliyetlere de yer veriyor. Hemşehrilerine yönelik taziye ve kutlama mesajları paylaşıyor.",
  "independent_topics": ["belediye hizmetleri", "yerel projeler", "spor", "kültür-sanat", "anma günleri"]
}}

## ŞİMDİ ANALİZ ET

Aşağıdaki tweetleri dikkatlice oku ve @{username} için benzer kalitede bir analiz yap.

### TWEETLER:
{tweets}

### ANALİZ (JSON formatında):"""


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

def format_tweets_for_prompt(tweets: list, max_tweets: int = 50) -> str:
    """
    Tweet listesini analiz için formatla.
    Her tweet numaralı ve temiz şekilde sunulur.
    """
    if not tweets:
        return "[Analiz edilecek tweet bulunamadı]"

    # En fazla max_tweets tweet al (en yeniler önce)
    selected = tweets[:max_tweets]

    lines = []
    for i, t in enumerate(selected, 1):
        text = t.get('text', t.get('tweet_text', ''))
        date = t.get('date', t.get('tweet_date', ''))

        # Tarihi kısalt (sadece gün)
        if date and len(date) > 10:
            date = date[:10]

        # Tweet formatı
        if date:
            lines.append(f"[{i}] ({date}) {text}")
        else:
            lines.append(f"[{i}] {text}")

    return "\n\n".join(lines)


def get_prompt(prompt_type: str, **kwargs) -> str:
    """
    Prompt şablonunu doldur ve döndür.

    Args:
        prompt_type: 'intelligence', 'full', 'main_topics', 'party_defense', 'opposition'
        **kwargs: Şablonda kullanılacak değişkenler

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
