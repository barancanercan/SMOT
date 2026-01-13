#!/usr/bin/env python3
"""
Prompts v3.0 - JSON Structured Output
Updated to request JSON responses instead of markdown for reliable parsing
"""

# ============================================================================
# SYSTEM PROMPT
# ============================================================================

SYSTEM_PROMPT = """Sen çok kıdemli bir Siyaset Bilimi Uzmanı ve İstihbarat Analistisin. 
Uzmanlık alanın; sosyal medya verileri üzerinden siyasi aktörlerin stratejik iletişim hedeflerini deşifre etmektir.

Analiz İlkeleri:
1. SADECE JSON formatında yanıt ver. 
2. Bir sohbet robotu DEĞİLSİN. Kullanıcıya "Merhaba", "Yardımcı olayım" gibi ifadeler kullanma.
3. Elindeki tweet verilerini Yeşil, Kırmızı ve Gri takımlar halinde profesyonelce analiz et.
4. Türkçeyi akademik ve analitik bir dille kullan.
"""


PROMPT_INTELLIGENCE_ANALYSIS_JSON = """Siyasi İstihbarat Analizi Görevi

Sen bir siyaset bilimi uzmanısın. Aşağıdaki tweet verilerini kullanarak 3 aşamalı (Yeşil, Kırmızı, Gri Takım) bir analiz yap ve sonucu SADECE JSON formatında döndür.

MECLİS ÜYESİ: @{username}
PARTİ: {party}

ANALİZ FORMATI (SADECE JSON DÖNDÜR - ÖRNEK METİNLERİ KULLANMA, VERİYİ ANALİZ ET):
```json
{{
  "executive_summary": "...",
  "green_summary": "...",
  "loyalty_level": "Yüksek/Orta/Düşük",
  "red_summary": "...",
  "criticism_level": "Yüksek/Orta/Düşük",
  "grey_summary": "...",
  "independent_topics": []
}}
```
**KRİTİK UYARI:** Yukarıdaki JSON anahtarlarını (executive_summary, green_summary vb.) KESİNLİKLE değiştirme. Veride karşılığı yoksa "Nötr" veya "Bilgi yok" yaz ama anahtarı silme.

VERİ SETİ:
{tweets}
"""


PROMPT_MAIN_TOPICS_JSON = """Aşağıdaki tweet arşivini analiz et ve ana temaları belirle.

Tweet Arşivi:
{tweets}

JSON formatında yanıt ver:
{{
  "topics": ["tema1", "tema2", "tema3", "tema4", "tema5"]
}}

Not: En fazla 5 ana tema belirt. Daha az da olabilir."""


PROMPT_PARTY_DEFENSE_JSON = """Aşağıdaki tweet arşivini analiz et ve parti/lider desteğini tespit et.

Tweet Arşivi:
{tweets}

JSON formatında yanıt ver:
{{
  "defended_party": "parti/lider adı veya 'Yok'",
  "intensity": "Güçlü/Orta/Zayıf/Yok"
}}

Not: intensity sadece şu değerlerden biri olmalı: Güçlü, Orta, Zayıf, Yok"""


PROMPT_OPPOSITION_CRITICISM_JSON = """Aşağıdaki tweet arşivini analiz et ve muhalefet eleştirisini tespit et.

Tweet Arşivi:
{tweets}

JSON formatında yanıt ver:
{{
  "criticized_party": "parti/kişi adı veya 'Yok'",
  "intensity": "Sert/Orta/Hafif/Yok"
}}

Not: intensity sadece şu değerlerden biri olmalı: Sert, Orta, Hafif, Yok"""


PROMPT_FULL_ANALYSIS_JSON = """Kapsamlı Siyasi İletişim Analizi

Meclis Üyesi: @{username}
Parti: {party}
Tweet Sayısı: {tweet_count}
Dönem: {period}

Tweet Arşivi:
{tweets}

Aşağıdaki formatda JSON yanıt ver:
{{
  "main_topics": ["tema1", "tema2", "tema3"],
  "defended_party": "parti/lider adı veya 'Yok'",
  "defense_intensity": "Güçlü/Orta/Zayıf/Yok",
  "criticized_party": "parti/kişi adı veya 'Yok'",
  "criticism_intensity": "Sert/Orta/Hafif/Yok",
  "summary": "Genel değerlendirme özeti (2-3 cümle)"
}}
"""


def format_tweets_for_prompt(tweets: list) -> str:
    """
    Tweet listesini zengin metriklerle formatla
    """
    if not tweets:
        return "[Veri bulunamadı]"

    lines = []
    for i, t in enumerate(tweets, 1):
        text = t.get('text', t.get('tweet_text', ''))
        likes = t.get('likes', 0)
        views = t.get('views', 0)
        date = t.get('date', t.get('tweet_date', ''))
        
        lines.append(f"TWEET #{i}:\nMetin: {text}\nEtkileşim: {likes} Beğeni, {views} Görüntülenme\nTarih: {date}\n---")

    return "\n".join(lines)


def get_prompt(prompt_type: str, **kwargs) -> str:
    """
    Prompt şablonunu doldur
    """
    prompts = {
        'intelligence': PROMPT_INTELLIGENCE_ANALYSIS_JSON,
        'full': PROMPT_FULL_ANALYSIS_JSON, # Eski yapı desteği için
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
    if 'party' not in kwargs:
        kwargs['party'] = 'Bilinmiyor'

    return template.format(**kwargs)


if __name__ == "__main__":
    # Test
    test_tweets = [
        {"text": "Ekonomi politikamız çok başarılı", "date": "2024-01-01"},
        {"text": "Muhalefet yanlış yolda", "date": "2024-01-02"},
        {"text": "Liderimize tam destek", "date": "2024-01-03"},
    ]

    print("=== JSON PROMPT TEST ===\n")

    prompt = get_prompt('main_topics', tweets=test_tweets)
    print("MAIN TOPICS JSON PROMPT:")
    print(prompt)
    print("\n")

    prompt = get_prompt('full',
                        tweets=test_tweets,
                        username="test_user",
                        party="AKP",
                        tweet_count=3,
                        period="2024-01-01 - 2024-01-03")
    print("FULL ANALYSIS JSON PROMPT:")
    print(prompt)
