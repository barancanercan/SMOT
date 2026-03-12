#!/usr/bin/env python3
"""
Analyzer v2.0 - Structured JSON Output
Migrated from regex parsing to Pydantic-validated JSON responses
"""

from typing import Dict, List, Optional
import time
import requests
import json
from pydantic import ValidationError

from app.services.analysis.prompts import SYSTEM_PROMPT, get_prompt
from app.services.analysis.schemas import (
    TopicAnalysis,
    PartyDefenseAnalysis,
    OppositionCriticismAnalysis,
    FullAnalysis,
    IntelligenceAnalysis
)
from app.utils.logger import get_logger

logger = get_logger("Analyzer")

# Default model - qwen3:14b for quality Turkish analysis
DEFAULT_MODEL = "qwen3:14b"
FALLBACK_MODEL = "qwen2.5:3b"
OLLAMA_URL = "http://127.0.0.1:11434"


class TweetAnalyzer:
    """Ollama ile tweet analizi (JSON Structured Output)"""

    def __init__(self, model: Optional[str] = None):
        """
        Args:
            model: Ollama model adı (default: qwen2.5:3b)
        """
        self.model = model or DEFAULT_MODEL
        self.base_url = OLLAMA_URL
        self._check_connection()

    def _check_connection(self):
        """Ollama bağlantısını kontrol et"""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                models = data.get('models', [])
                model_names = [m.get('name', '') for m in models]
                if self.model not in model_names and f"{self.model}:latest" not in model_names:
                    logger.warning(f"Model '{self.model}' bulunamadi. Mevcut: {model_names}")
        except Exception as e:
            logger.error(f"Ollama baglanti kontrolu: {e}")

    def _call_llm(self, prompt: str, max_retries: int = 2) -> str:
        """
        LLM'e istek gönder (JSON mode)

        Args:
            prompt: Kullanıcı promptu
            max_retries: Hata durumunda tekrar deneme

        Returns:
            LLM yanıtı (JSON string)
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "format": "json",  # Force JSON output
            "options": {
                "temperature": 0.3,  # Biraz yaraticilik
                "num_predict": 4096,  # Uzun yanitlar icin
                "num_ctx": 8192,  # Genis context window
                "top_p": 0.9,
                "repeat_penalty": 1.1  # Tekrari onle
            },
            "stream": False
        }

        for attempt in range(max_retries + 1):
            try:
                resp = requests.post(url, json=payload, timeout=300)
                resp.raise_for_status()
                data = resp.json()
                content = data.get('message', {}).get('content', '')
                # Debug: ham yaniti logla (ilk 500 karakter)
                logger.debug(f"LLM ham yanit: {content[:500]}...")
                return content

            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"LLM hatasi, tekrar deneniyor ({attempt + 1}/{max_retries})...")
                    time.sleep(2)
                else:
                    raise Exception(f"LLM hatasi: {e}")
        return ""

    def _clean_json_response(self, data: dict) -> dict:
        """
        JSON-LD ve schema.org meta verilerini temizle

        Args:
            data: Parse edilmis JSON dict

        Returns:
            Temizlenmis dict
        """
        # Silinecek JSON-LD anahtar kelimeleri
        ld_keys = ['@context', '@type', '@id', '@graph', '@vocab', 'schema', 'schema.org']

        cleaned = {}
        for key, value in data.items():
            # JSON-LD anahtarlarini atla
            if key in ld_keys or key.startswith('@'):
                continue

            # schema.org URL'lerini atla
            if isinstance(value, str) and ('schema.org' in value or 'json-ld' in value.lower()):
                continue

            # Nested dict ise recursive temizle
            if isinstance(value, dict):
                cleaned[key] = self._clean_json_response(value)
            elif isinstance(value, list):
                # Liste ise her elemani kontrol et
                cleaned_list = []
                for item in value:
                    if isinstance(item, dict):
                        cleaned_list.append(self._clean_json_response(item))
                    elif isinstance(item, str) and 'schema.org' not in item:
                        cleaned_list.append(item)
                    elif not isinstance(item, str):
                        cleaned_list.append(item)
                cleaned[key] = cleaned_list
            else:
                cleaned[key] = value

        return cleaned

    def _parse_json_response(self, response: str, schema_class):
        """
        JSON yanıtını parse et ve Pydantic ile doğrula

        Args:
            response: LLM'den gelen JSON string
            schema_class: Pydantic model class

        Returns:
            Validated model instance or None
        """
        try:
            # JSON parse
            data = json.loads(response)

            # Debug: Gelen veriyi logla
            logger.info(f"LLM JSON anahtarlari: {list(data.keys())}")

            # JSON-LD temizleme
            if '@context' in data or '@type' in data:
                logger.warning("JSON-LD format algilandi, temizleniyor...")
                data = self._clean_json_response(data)
                logger.info(f"Temizlenmis anahtarlar: {list(data.keys())}")

            # Eger 'tweets' anahtari varsa, model tweet verilerini geri dondurmus
            if 'tweets' in data and 'executive_summary' not in data:
                logger.error("Model tweet verilerini geri dondurdu, analiz yapmadi!")
                return None

            # Pydantic validation
            validated = schema_class(**data)
            return validated
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.debug(f"Response: {response[:200]}")
            return None
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            logger.debug(f"Raw data keys: {list(data.keys()) if 'data' in dir() else 'N/A'}")

            # Son caba: beklenen alanlari elle cikarmaya calis
            if 'data' in dir() and isinstance(data, dict):
                logger.info("Manuel alan cikarma deneniyor...")
                try:
                    # IntelligenceAnalysis icin zorunlu alanlar
                    if schema_class.__name__ == 'IntelligenceAnalysis':
                        fallback = {
                            'executive_summary': data.get('executive_summary', data.get('summary', 'Analiz yapilamadi')),
                            'green_summary': data.get('green_summary', data.get('party_support', 'Veri yok')),
                            'loyalty_level': data.get('loyalty_level', 'Orta'),
                            'red_summary': data.get('red_summary', data.get('opposition', 'Veri yok')),
                            'criticism_level': data.get('criticism_level', 'Orta'),
                            'grey_summary': data.get('grey_summary', data.get('independent', 'Veri yok')),
                            'independent_topics': data.get('independent_topics', data.get('topics', []))
                        }
                        validated = schema_class(**fallback)
                        logger.info("Manuel alan cikarma basarili")
                        return validated
                except Exception as fallback_error:
                    logger.error(f"Manuel cikarma da basarisiz: {fallback_error}")

            return None

    def analyze_main_topics(self, tweets: List[Dict]) -> Dict:
        """
        Soru 1: Ana konuları analiz et (JSON)

        Args:
            tweets: Tweet listesi

        Returns:
            {'raw_response': str, 'topics': List[str], 'validated': bool}
        """
        prompt = get_prompt('main_topics', tweets=tweets)

        logger.info("Ana konular analiz ediliyor...")
        start = time.time()
        response = self._call_llm(prompt)
        elapsed = time.time() - start
        logger.info(f"Tamamlandi ({elapsed:.1f}s)")

        # Parse and validate
        validated_data = self._parse_json_response(response, TopicAnalysis)

        if validated_data:
            return {
                'raw_response': response,
                'topics': validated_data.topics,
                'elapsed_seconds': elapsed,
                'validated': True
            }
        else:
            # Fallback to empty
            logger.warning("JSON validation failed, returning empty topics")
            return {
                'raw_response': response,
                'topics': [],
                'elapsed_seconds': elapsed,
                'validated': False
            }

    def analyze_party_defense(self, tweets: List[Dict]) -> Dict:
        """
        Soru 2: Parti/lider savunusu analizi (JSON)

        Args:
            tweets: Tweet listesi

        Returns:
            {'raw_response': str, 'defended': str, 'intensity': str, 'validated': bool}
        """
        prompt = get_prompt('party_defense', tweets=tweets)

        logger.info("Parti savunusu analiz ediliyor...")
        start = time.time()
        response = self._call_llm(prompt)
        elapsed = time.time() - start
        logger.info(f"Tamamlandi ({elapsed:.1f}s)")

        # Parse and validate
        validated_data = self._parse_json_response(response, PartyDefenseAnalysis)

        if validated_data:
            return {
                'raw_response': response,
                'defended': validated_data.defended_party,
                'intensity': validated_data.intensity,
                'elapsed_seconds': elapsed,
                'validated': True
            }
        else:
            logger.warning("JSON validation failed, returning defaults")
            return {
                'raw_response': response,
                'defended': "Belirsiz",
                'intensity': "Belirsiz",
                'elapsed_seconds': elapsed,
                'validated': False
            }

    def analyze_opposition_criticism(self, tweets: List[Dict]) -> Dict:
        """
        Soru 3: Muhalefet eleştirisi analizi (JSON)

        Args:
            tweets: Tweet listesi

        Returns:
            {'raw_response': str, 'criticized': str, 'intensity': str, 'validated': bool}
        """
        prompt = get_prompt('opposition', tweets=tweets)

        logger.info("Muhalefet elestirisi analiz ediliyor...")
        start = time.time()
        response = self._call_llm(prompt)
        elapsed = time.time() - start
        logger.info(f"Tamamlandi ({elapsed:.1f}s)")

        # Parse and validate
        validated_data = self._parse_json_response(response, OppositionCriticismAnalysis)

        if validated_data:
            return {
                'raw_response': response,
                'criticized': validated_data.criticized_party,
                'intensity': validated_data.intensity,
                'elapsed_seconds': elapsed,
                'validated': True
            }
        else:
            logger.warning("JSON validation failed, returning defaults")
            return {
                'raw_response': response,
                'criticized': "Belirsiz",
                'intensity': "Belirsiz",
                'elapsed_seconds': elapsed,
                'validated': False
            }

    def analyze_full(self, tweets: List[Dict], username: str, period: Optional[str] = None,
                     party: Optional[str] = None) -> Dict:
        """
        Backward compatibility wrapper for analyze_intelligence

        Args:
            tweets: Tweet listesi
            username: Kullanıcı adı
            period: Analiz dönemi
            party: Meclis üyesinin partisi

        Returns:
            Analiz sonucu dict
        """
        result = self.analyze_intelligence(tweets, username, period, party)

        # Eski formata dönüştür (FullAnalysis uyumlu)
        if result.get('validated') and result.get('analysis'):
            analysis = result['analysis']
            return {
                'username': username,
                'party': party,
                'tweet_count': len(tweets),
                'period': period,
                'main_topics': analysis.independent_topics,
                'defended_party': party or "Bilinmiyor",
                'defense_intensity': analysis.loyalty_level,
                'criticized_party': "Muhalefet",
                'criticism_intensity': analysis.criticism_level,
                'summary': analysis.executive_summary,
                'elapsed_seconds': result.get('elapsed_seconds', 0),
                'validated': True
            }
        else:
            return {
                'username': username,
                'party': party,
                'tweet_count': len(tweets),
                'period': period,
                'raw_response': result.get('raw_response', ''),
                'elapsed_seconds': result.get('elapsed_seconds', 0),
                'validated': False
            }

    def analyze_intelligence(self, tweets: List[Dict], username: str, period: Optional[str] = None,
                             party: Optional[str] = None) -> Dict:
        """
        Üç aşamalı (Yeşil, Kırmızı, Gri) profesyonel istihbarat analizi

        Args:
            tweets: Tweet listesi
            username: Kullanıcı adı
            period: Analiz dönemi
            party: Meclis üyesinin partisi

        Returns:
            IntelligenceAnalysis objesi kapsayan sözlük
        """
        prompt = get_prompt(
            'intelligence',
            tweets=tweets,
            username=username,
            party=party or "Bilinmiyor",
            tweet_count=len(tweets),
            period=period or "Tüm zamanlar"
        )

        logger.info(f"@{username} için profesyonel istihbarat analizi yapiliyor...")
        start = time.time()
        response = self._call_llm(prompt)
        elapsed = time.time() - start
        logger.info(f"Tamamlandi ({elapsed:.1f}s)")

        # Parse and validate
        validated_data = self._parse_json_response(response, IntelligenceAnalysis)

        if validated_data:
            return {
                'username': username,
                'party': party,
                'tweet_count': len(tweets),
                'period': period,
                'raw_response': response,
                'analysis': validated_data,
                'elapsed_seconds': elapsed,
                'validated': True
            }
        else:
            logger.warning("JSON validation failed for IntelligenceAnalysis")
            return {
                'username': username,
                'party': party,
                'tweet_count': len(tweets),
                'period': period,
                'raw_response': response,
                'elapsed_seconds': elapsed,
                'validated': False
            }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def analyze_user(username: str) -> Dict:
    """
    Kullanıcı için tam analiz yap (tüm tweetler)

    Args:
        username: Twitter kullanıcı adı

    Returns:
        Analiz sonucu
    """
    from app.core.db_config import session_scope
    from app.core.models import Tweet

    # Tweetleri al (ORM)
    try:
        with session_scope() as session:
            tweets_query = session.query(Tweet.tweet_text, Tweet.tweet_date, Tweet.likes,
                                          Tweet.replies, Tweet.retweets).filter(
                Tweet.username == username,
                ~Tweet.is_retweet
            ).order_by(Tweet.tweet_date.desc()).all()

            if not tweets_query:
                return {'error': f'@{username} için tweet bulunamadı'}

            tweets = [
                {
                    'text': row[0],
                    'date': row[1],
                    'likes': row[2],
                    'replies': row[3],
                    'retweets': row[4]
                }
                for row in tweets_query
            ]
    except Exception as e:
        logger.error(f"Database error: {e}")
        return {'error': f'Database error: {e}'}

    # Tarih aralığı
    dates = [t['date'] for t in tweets if t['date']]
    period = f"{min(dates)} - {max(dates)}" if dates else "Bilinmiyor"

    # Analiz
    analyzer = TweetAnalyzer()
    result = analyzer.analyze_full(tweets, username, period)

    return result


def analyze_user_with_vector_search(username: str, query: str, n_results: int = 50) -> Dict:
    """
    Vector search ile ilgili tweetleri bulup analiz et

    Args:
        username: Kullanıcı adı
        query: Arama sorgusu (örneğin "ekonomi politikası")
        n_results: Arama sonucu sayısı (default: 50)

    Returns:
        Analiz sonucu
    """
    from .vector_db import search_similar

    # İlgili tweetleri bul
    results = search_similar(query, n_results=n_results, username=username)

    if not results:
        return {'error': f'@{username} için "{query}" ile ilgili tweet bulunamadı'}

    tweets = [{'text': r['text'], 'date': ''} for r in results]

    # Analiz
    analyzer = TweetAnalyzer()
    result = analyzer.analyze_full(tweets, username, f"Konu: {query}")
    result['search_query'] = query
    result['search_results_count'] = len(results)

    return result


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Tweet Analiz (Ollama LLM - JSON)")
    parser.add_argument("--user", help="Kullanıcı adı")
    parser.add_argument("--query", help="Vector search sorgusu")
    parser.add_argument("--model", help="Ollama model (default: qwen2.5:3b)")
    parser.add_argument("--test", action="store_true", help="Bağlantı testi")

    args = parser.parse_args()

    if args.test:
        logger.info("Ollama baglanti testi...")
        try:
            analyzer = TweetAnalyzer(args.model)
            logger.info(f"Model: {analyzer.model}")
            logger.info("Baglanti OK!")
        except Exception as e:
            logger.error(f"Hata: {e}")

    elif args.user:
        if args.query:
            result = analyze_user_with_vector_search(args.user, args.query)
        else:
            result = analyze_user(args.user)

        if 'error' in result:
            logger.error(f"Hata: {result['error']}")
        else:
            print(f"\n{'='*60}")
            print(f"@{result['username']} ANALIZ SONUCU")
            print(f"{'='*60}")
            print(f"Tweet sayısı: {result['tweet_count']}")
            print(f"Dönem: {result['period']}")
            print(f"Süre: {result['elapsed_seconds']:.1f}s")
            print(f"Validated: {result.get('validated', False)}")
            print(f"{'='*60}")
            if result.get('validated'):
                print(f"Ana Konular: {result.get('main_topics', [])}")
                print(f"Savunulan: {result.get('defended_party', 'N/A')}")
                print(f"Eleştirilen: {result.get('criticized_party', 'N/A')}")
                print(f"Özet: {result.get('summary', 'N/A')}")
            print(f"{'='*60}")

    else:
        print("Kullanım:")
        print("  python analyzer.py --test")
        print("  python analyzer.py --user username")
        print("  python analyzer.py --user username --query 'ekonomi'")
        print("  python analyzer.py --user username --model qwen2.5:3b")