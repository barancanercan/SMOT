#!/usr/bin/env python3
"""
Tweet Classifier v3 - Dynamic Classification with GPT-4o

2026 State-of-the-art approach:
1. GPT-4o for better Turkish understanding
2. Dynamic classification based on query intent (not hardcoded)
3. Party-aware classification (who criticizes whom)
4. Few-shot examples tailored to query type
"""

import json
import re
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger("TweetClassifier")


@dataclass
class ClassificationQuery:
    """Defines what we're looking for in tweets"""
    source_party: str | None  # Who is tweeting (e.g., "CHP", "AK Parti")
    target_party: str | None  # Who is being criticized (e.g., "hükümet", "CHP")
    topic: str | None  # What topic (e.g., "ekonomi", "eğitim")
    sentiment: str  # "criticism", "support", "neutral", "any"


# =============================================================================
# DYNAMIC FEW-SHOT PROMPT BUILDER
# =============================================================================

def build_classification_prompt(
    query: ClassificationQuery,
    original_question: str
) -> str:
    """
    Build a dynamic prompt based on what we're looking for.
    """

    # Determine classification type
    if query.target_party and query.sentiment == "criticism":
        return _build_criticism_prompt(query, original_question)
    elif query.topic:
        return _build_topic_prompt(query, original_question)
    else:
        return _build_general_prompt(query, original_question)


def _build_criticism_prompt(query: ClassificationQuery, original_question: str) -> str:
    """Build prompt for criticism detection."""

    target = query.target_party or "hükümet"

    # Dynamic examples based on target
    if target.lower() in ["hükümet", "iktidar", "akp", "ak parti", "erdoğan"]:
        examples = """
### ✅ HÜKÜMET/İKTİDAR ELEŞTİRİSİDİR:

Tweet: "AKP'nin ekonomi politikaları ülkeyi batırdı. Enflasyon yüzde 80'i aştı!"
→ ELEŞTİRİ: Evet | KONU: Ekonomi | HEDEF: AKP/Hükümet

Tweet: "Hükümetin eğitim politikası tam bir fiyasko. Öğretmenler aç!"
→ ELEŞTİRİ: Evet | KONU: Eğitim | HEDEF: Hükümet

Tweet: "Saray'ın israfı devam ediyor. Halk açken milyonlar harcanıyor."
→ ELEŞTİRİ: Evet | KONU: İsraf | HEDEF: Cumhurbaşkanlığı

Tweet: "İktidarın yargı baskısı kabul edilemez. Yargı bağımsızlığı yok!"
→ ELEŞTİRİ: Evet | KONU: Yargı | HEDEF: İktidar

Tweet: "Erdoğan'ın dış politikası Türkiye'yi yalnızlaştırdı."
→ ELEŞTİRİ: Evet | KONU: Dış politika | HEDEF: Cumhurbaşkanı

### ❌ HÜKÜMET ELEŞTİRİSİ DEĞİLDİR:

Tweet: "CHP kurultayımızı başarıyla tamamladık!"
→ ELEŞTİRİ: Hayır | NEDEN: Parti haberi

Tweet: "Atatürk'ü saygıyla anıyoruz."
→ ELEŞTİRİ: Hayır | NEDEN: Anma mesajı

Tweet: "Belediyemiz yeni parkı açtı."
→ ELEŞTİRİ: Hayır | NEDEN: Belediye hizmeti

Tweet: "Genel Başkanımızın liderliğinde ilerliyoruz."
→ ELEŞTİRİ: Hayır | NEDEN: Parti övgüsü

Tweet: "Futbol maçında hakem skandalı!"
→ ELEŞTİRİ: Hayır | NEDEN: Spor haberi, siyasi değil

Tweet: "TFF'ye soruşturma açılmalı, emek hırsızlığı!"
→ ELEŞTİRİ: Hayır | NEDEN: Futbol federasyonu eleştirisi, hükümet değil
"""
    elif target.lower() in ["chp", "muhalefet"]:
        examples = """
### ✅ CHP/MUHALEFET ELEŞTİRİSİDİR:

Tweet: "CHP'li belediyeler hizmette sınıfta kaldı. 6 yılda ne yaptılar?"
→ ELEŞTİRİ: Evet | KONU: Belediye hizmetleri | HEDEF: CHP

Tweet: "Mansur Yavaş Ankara'yı berbat etti. Metro yok, trafik felç!"
→ ELEŞTİRİ: Evet | KONU: Ulaşım | HEDEF: CHP/Ankara Belediyesi

Tweet: "İmamoğlu'nun vaatleri havada kaldı. İstanbul battı!"
→ ELEŞTİRİ: Evet | KONU: Vaatler | HEDEF: CHP/İstanbul Belediyesi

Tweet: "CHP'nin ekonomi politikası yok, sadece eleştiri var."
→ ELEŞTİRİ: Evet | KONU: Politika eksikliği | HEDEF: CHP

Tweet: "Muhalefet birlik olamıyor, kendi içinde kavga!"
→ ELEŞTİRİ: Evet | KONU: Birlik | HEDEF: Muhalefet

### ❌ CHP ELEŞTİRİSİ DEĞİLDİR:

Tweet: "AK Parti olarak millete hizmet ediyoruz."
→ ELEŞTİRİ: Hayır | NEDEN: Parti övgüsü

Tweet: "Cumhurbaşkanımızla görüştük."
→ ELEŞTİRİ: Hayır | NEDEN: Haber

Tweet: "Ankara'da yeni yol açıldı."
→ ELEŞTİRİ: Hayır | NEDEN: Genel haber

Tweet: "Ekonomide toparlanma başladı."
→ ELEŞTİRİ: Hayır | NEDEN: Olumlu haber
"""
    else:
        examples = """
### ✅ SİYASİ ELEŞTİRİDİR:

Tweet: "X partisinin politikaları ülkeye zarar veriyor."
→ ELEŞTİRİ: Evet | KONU: Genel politika

Tweet: "Bu yönetim başarısız, değişim şart!"
→ ELEŞTİRİ: Evet | KONU: Yönetim

### ❌ SİYASİ ELEŞTİRİ DEĞİLDİR:

Tweet: "Parti toplantımız başarıyla bitti."
→ ELEŞTİRİ: Hayır | NEDEN: Parti haberi

Tweet: "Bayramınız kutlu olsun."
→ ELEŞTİRİ: Hayır | NEDEN: Kutlama
"""

    return f"""Sen Türk siyasi içerik uzmanısın. Tweetleri analiz edip {target.upper()} ELEŞTİRİSİ içerip içermediğini belirle.

## KULLANICI SORUSU:
"{original_question}"

## {target.upper()} ELEŞTİRİSİ NEDİR?

Bir tweet'in "{target} eleştirisi" sayılması için:
1. {target}'ı DOĞRUDAN hedef almalı (isim veya kurum olarak)
2. Eleştiri, suçlama veya olumsuz değerlendirme İÇERMELİ
3. Belirli bir politika, karar veya eylem eleştirilmeli

## ÖNEMLİ: BUNLAR ELEŞTİRİ SAYILMAZ!
- Kendi parti/belediye haberleri
- Anma ve kutlama mesajları
- Spor haberleri (futbol, hakem, TFF vb.)
- Genel etkinlik duyuruları
- Başka kurumlara yönelik eleştiriler ({target} değilse)

## ÖRNEKLER:
{examples}

## ŞİMDİ BU TWEETLERİ SINIFLANDIR:

{{tweets}}

## ÇIKTI (JSON):

```json
{{{{
  "results": [
    {{{{
      "index": 1,
      "is_criticism": true/false,
      "target": "{target} eleştirisi" veya "yok",
      "topic": "eleştiri konusu",
      "explanation": "kısa açıklama",
      "confidence": 0.0-1.0
    }}}}
  ],
  "summary": {{{{
    "criticism_count": 0,
    "main_topics": ["konu1", "konu2"]
  }}}}
}}}}
```

JSON:"""


def _build_topic_prompt(query: ClassificationQuery, original_question: str) -> str:
    """Build prompt for topic-based search."""
    topic = query.topic or "genel"

    return f"""Sen Türk siyasi içerik uzmanısın. Tweetleri analiz edip "{topic.upper()}" KONUSUYLA ilgili olanları bul.

## KULLANICI SORUSU:
"{original_question}"

## "{topic.upper()}" KONUSU NEDİR?

Tweet'in bu konuyla ilgili sayılması için:
1. Konuyu DOĞRUDAN ele almalı
2. Sadece kelime geçmesi yetmez, KONU olmali

## ŞİMDİ BU TWEETLERİ SINIFLANDIR:

{{tweets}}

## ÇIKTI (JSON):

```json
{{{{
  "results": [
    {{{{"index": 1, "is_match": true/false, "topic": "...", "explanation": "..."}}}}
  ]
}}}}
```

JSON:"""


def _build_general_prompt(query: ClassificationQuery, original_question: str) -> str:
    """Build prompt for general search."""
    return f"""Sen Türk siyasi içerik uzmanısın. Kullanıcının sorusuna göre ilgili tweetleri bul.

## KULLANICI SORUSU:
"{original_question}"

## ŞİMDİ BU TWEETLERİ SINIFLANDIR:

{{tweets}}

## ÇIKTI (JSON):

```json
{{{{
  "results": [
    {{{{"index": 1, "is_match": true/false, "topic": "...", "explanation": "..."}}}}
  ]
}}}}
```

JSON:"""


class TweetClassifier:
    """
    Tweet classifier using GPT-4o with dynamic prompts.

    Key features:
    1. Uses GPT-4o for better Turkish understanding
    2. Dynamic prompts based on query intent
    3. Party-aware classification
    """

    BATCH_SIZE = 15

    def __init__(self):
        """Initialize the classifier with GPT-4o."""
        self.client = None
        self.llm_available = False
        self.model = settings.openai_chat_model  # gpt-4o

        if settings.openai_api_key:
            try:
                self.client = OpenAI(api_key=settings.openai_api_key)
                self.llm_available = True
                logger.info(f"TweetClassifier v3 initialized with {self.model}")
            except Exception as e:
                logger.warning(f"OpenAI client init failed: {e}")
        else:
            logger.warning("OpenAI API key not set")

    def classify_tweets(
        self,
        tweets: list[dict],
        original_question: str,
        source_party: str | None = None,
        target_party: str | None = None,
        topic: str | None = None,
        sentiment: str = "criticism"
    ) -> dict[str, Any]:
        """
        Classify tweets based on dynamic query parameters.

        Args:
            tweets: List of tweet dicts
            original_question: User's original question
            source_party: Party of tweet authors (filter)
            target_party: Party being criticized/discussed
            topic: Topic to search for
            sentiment: "criticism", "support", "neutral", "any"

        Returns:
            Dict with matches and analysis
        """
        if not tweets:
            return {"matches": [], "total_analyzed": 0, "summary": {}}

        if not self.llm_available:
            logger.warning("GPT-4o not available, using regex fallback")
            return self._regex_fallback(tweets, target_party)

        # Build classification query
        query = ClassificationQuery(
            source_party=source_party,
            target_party=target_party,
            topic=topic,
            sentiment=sentiment
        )

        # Build dynamic prompt
        prompt_template = build_classification_prompt(query, original_question)

        all_matches = []
        all_topics = []

        # Process in batches
        for i in range(0, len(tweets), self.BATCH_SIZE):
            batch = tweets[i:i + self.BATCH_SIZE]
            batch_num = i // self.BATCH_SIZE + 1
            logger.info(f"Classifying batch {batch_num} ({len(batch)} tweets) with {self.model}")

            try:
                batch_result = self._classify_batch(batch, prompt_template)
                all_matches.extend(batch_result.get("matches", []))
                all_topics.extend(batch_result.get("topics", []))
            except Exception as e:
                logger.error(f"Batch {batch_num} error: {e}")
                continue

        unique_topics = list(dict.fromkeys(all_topics))[:10]

        return {
            "matches": all_matches,
            "total_analyzed": len(tweets),
            "total_matches": len(all_matches),
            "main_topics": unique_topics,
            "summary": {
                "total_found": len(all_matches),
                "top_topics": unique_topics[:5],
                "sentiment": "olumsuz" if sentiment == "criticism" and all_matches else "notr"
            }
        }

    def _classify_batch(self, tweets: list[dict], prompt_template: str) -> dict[str, Any]:
        """Classify a batch using GPT-4o."""

        # Format tweets
        tweet_lines = []
        for i, t in enumerate(tweets, 1):
            text = t.get('tweet_text', t.get('text', ''))
            username = t.get('username', '')

            if len(text) > 400:
                text = text[:400] + "..."

            tweet_lines.append(f"[{i}] @{username}: {text}")

        tweets_text = "\n\n".join(tweet_lines)
        prompt = prompt_template.format(tweets=tweets_text)

        # Call GPT-4o with JSON response format
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Sen Türk siyasi içerik analistisin. Yanıtını yalnızca geçerli JSON formatında ver, başka açıklama ekleme."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            response_text = response.choices[0].message.content
            logger.debug(f"GPT-4o response (first 200 chars): {response_text[:200] if response_text else 'empty'}")
        except Exception as api_error:
            logger.error(f"OpenAI API error: {type(api_error).__name__}: {api_error}")
            return {"matches": [], "topics": []}

        # Parse response
        try:
            cleaned_response = self._clean_json_response(response_text)
            data = json.loads(cleaned_response)

            # Handle different response formats
            if not isinstance(data, dict):
                logger.warning(f"Unexpected response format: {type(data)}")
                return {"matches": [], "topics": []}

            results = data.get("results", data.get("matches", []))
            matches = []
            topics = []

            for r in results:
                idx = r.get("index", 0) - 1
                is_match = r.get("is_criticism", r.get("is_match", False))
                confidence = r.get("confidence", 0.8)

                if is_match and confidence >= 0.7 and 0 <= idx < len(tweets):
                    tweet = tweets[idx].copy()
                    tweet["_classification"] = {
                        "category": r.get("target", "eleştiri"),
                        "topic": r.get("topic", ""),
                        "confidence": confidence,
                        "explanation": r.get("explanation", "")
                    }
                    matches.append(tweet)

                    if r.get("topic"):
                        topics.append(r.get("topic"))

            return {"matches": matches, "topics": topics, "summary": data.get("summary", {})}

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.debug(f"Raw response: {response_text[:500] if response_text else 'empty'}")
            return {"matches": [], "topics": []}
        except Exception as e:
            logger.error(f"Classification parse error: {type(e).__name__}: {e}")
            return {"matches": [], "topics": []}

    def _clean_json_response(self, response: str) -> str:
        """Extract JSON from response."""
        response = response.strip()

        if "```json" in response:
            match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                return match.group(1)

        if "```" in response:
            match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                return match.group(1)

        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return match.group(0)

        return response

    def _regex_fallback(self, tweets: list[dict], target: str | None) -> dict[str, Any]:
        """Fallback regex matching."""
        target = target or "hükümet"

        if target.lower() in ["hükümet", "iktidar", "akp", "ak parti"]:
            target_patterns = [r'\b(akp|ak\s*parti|hükümet|iktidar|erdoğan|saray)\b']
        elif target.lower() in ["chp", "muhalefet"]:
            target_patterns = [r'\b(chp|muhalefet|mansur|imamoğlu)\b']
        else:
            target_patterns = [rf'\b({target})\b']

        criticism_patterns = [
            r'\b(eleştir|kına|protesto)\w*',
            r'\b(skandal|rezalet|fiyasko|başarısız)\b',
            r'\b(berbat|kötü|yetersiz|beceriksiz)\b',
        ]

        matches = []
        for tweet in tweets:
            text = tweet.get('tweet_text', '').lower()

            has_target = any(re.search(p, text, re.IGNORECASE) for p in target_patterns)
            has_criticism = any(re.search(p, text, re.IGNORECASE) for p in criticism_patterns)

            if has_target and has_criticism:
                tweet_copy = tweet.copy()
                tweet_copy["_classification"] = {
                    "category": f"{target} eleştirisi",
                    "topic": "Genel",
                    "confidence": 0.6,
                    "explanation": "Regex ile tespit"
                }
                matches.append(tweet_copy)

        return {
            "matches": matches,
            "total_analyzed": len(tweets),
            "total_matches": len(matches),
            "main_topics": [],
            "summary": {"total_found": len(matches)}
        }

    # Backward compatibility
    def classify_for_criticism(self, tweets: list[dict], target: str = "hükümet") -> dict[str, Any]:
        """Legacy method for backward compatibility."""
        return self.classify_tweets(
            tweets=tweets,
            original_question=f"{target} eleştirisi içeren tweetleri bul",
            target_party=target,
            sentiment="criticism"
        )
