#!/usr/bin/env python3
"""
Analyzer v3.1 - Multi-Provider LLM (OpenAI + Ollama)
- OpenAI GPT-3.5-turbo support (FAST & CHEAP)
- Ollama fallback support
- Async HTTP calls with httpx
- LLM metrics collection
- Multi-shot learning support
- Confidence scoring
"""

from typing import Dict, List, Optional
import time
import asyncio
import requests
import json
import httpx
from pydantic import ValidationError

from app.services.analysis.prompts import SYSTEM_PROMPT, get_prompt
from app.services.analysis.schemas import (
    TopicAnalysis,
    PartyDefenseAnalysis,
    OppositionCriticismAnalysis,
    FullAnalysis,
    IntelligenceAnalysis
)
from app.services.analysis.metrics import LLMCallTimer, metrics_collector
from app.core.constants import normalize_party_name
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger("Analyzer")

# Async client configuration
ASYNC_TIMEOUT = httpx.Timeout(300.0, connect=10.0)  # 5 min read, 10s connect


class TweetAnalyzer:
    """Multi-provider LLM tweet analizi (OpenAI + Ollama)"""

    def __init__(self, model: Optional[str] = None, provider: Optional[str] = None):
        """
        Args:
            model: Model adı (provider'a göre farklı)
            provider: LLM provider ("openai" veya "ollama", default: settings.llm_provider)
        """
        self.provider = provider or settings.llm_provider

        if self.provider == "openai":
            # OpenAI setup
            self.model = model or settings.openai_model
            self.api_key = settings.openai_api_key
            if not self.api_key:
                logger.warning("OPENAI_API_KEY bulunamadi! Ollama'ya geciliyor...")
                self.provider = "ollama"
                self.model = settings.ollama_model
                self.base_url = settings.ollama_url
                self._check_connection()
            else:
                logger.info(f"OpenAI provider aktif - Model: {self.model}")
        else:
            # Ollama setup (fallback)
            self.model = model or settings.ollama_model
            self.base_url = settings.ollama_url
            self._check_connection()
            logger.info(f"Ollama provider aktif - Model: {self.model}")

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

    def _get_openai_payload(self, prompt: str) -> dict:
        """Build OpenAI request payload"""
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,  # Low for consistency
            "max_tokens": 2048,
            "response_format": {"type": "json_object"}  # Force JSON mode
        }

    def _get_llm_payload(self, prompt: str) -> dict:
        """Build LLM request payload"""
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "format": "json",  # Force JSON output
            "options": {
                "temperature": 0.2,  # Lower for more consistency
                "num_predict": 2048,  # Reduced from 4096
                "num_ctx": 4096,  # Reduced from 8192 for faster processing
                "top_p": 0.9,
                "repeat_penalty": 1.15  # Increased to prevent repetition
            },
            "stream": False
        }

    def _call_llm(self, prompt: str, max_retries: int = 2) -> str:
        """
        LLM'e senkron istek gönder (JSON mode)

        Args:
            prompt: Kullanıcı promptu
            max_retries: Hata durumunda tekrar deneme

        Returns:
            LLM yanıtı (JSON string)
        """
        if self.provider == "openai":
            return self._call_openai(prompt, max_retries)
        else:
            return self._call_ollama(prompt, max_retries)

    def _call_openai(self, prompt: str, max_retries: int = 2) -> str:
        """
        OpenAI API'ye senkron istek gönder

        Args:
            prompt: Kullanıcı promptu
            max_retries: Hata durumunda tekrar deneme

        Returns:
            LLM yanıtı (JSON string)
        """
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = self._get_openai_payload(prompt)

        for attempt in range(max_retries + 1):
            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=settings.openai_timeout)
                resp.raise_for_status()
                data = resp.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                logger.debug(f"OpenAI ham yanit: {content[:500]}...")
                return content

            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"OpenAI hatasi, tekrar deneniyor ({attempt + 1}/{max_retries}): {e}")
                    time.sleep(2)
                else:
                    raise Exception(f"OpenAI API hatasi: {e}")
        return ""

    def _call_ollama(self, prompt: str, max_retries: int = 2) -> str:
        """
        Ollama'ya senkron istek gönder

        Args:
            prompt: Kullanıcı promptu
            max_retries: Hata durumunda tekrar deneme

        Returns:
            LLM yanıtı (JSON string)
        """
        url = f"{self.base_url}/api/chat"
        payload = self._get_llm_payload(prompt)

        for attempt in range(max_retries + 1):
            try:
                resp = requests.post(url, json=payload, timeout=settings.ollama_timeout)
                resp.raise_for_status()
                data = resp.json()
                content = data.get('message', {}).get('content', '')
                logger.debug(f"Ollama ham yanit: {content[:500]}...")
                return content

            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Ollama hatasi, tekrar deneniyor ({attempt + 1}/{max_retries})...")
                    time.sleep(2)
                else:
                    raise Exception(f"Ollama hatasi: {e}")
        return ""

    async def _call_llm_async(self, prompt: str, max_retries: int = 2) -> str:
        """
        LLM'e asenkron istek gönder (httpx ile)

        Args:
            prompt: Kullanıcı promptu
            max_retries: Hata durumunda tekrar deneme

        Returns:
            LLM yanıtı (JSON string)
        """
        if self.provider == "openai":
            return await self._call_openai_async(prompt, max_retries)
        else:
            return await self._call_ollama_async(prompt, max_retries)

    async def _call_openai_async(self, prompt: str, max_retries: int = 2) -> str:
        """
        OpenAI API'ye asenkron istek gönder

        Args:
            prompt: Kullanıcı promptu
            max_retries: Hata durumunda tekrar deneme

        Returns:
            LLM yanıtı (JSON string)
        """
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = self._get_openai_payload(prompt)

        async_timeout = httpx.Timeout(float(settings.openai_timeout), connect=10.0)
        async with httpx.AsyncClient(timeout=async_timeout) as client:
            for attempt in range(max_retries + 1):
                try:
                    resp = await client.post(url, json=payload, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                    content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                    logger.debug(f"OpenAI async ham yanit: {content[:500]}...")
                    return content

                except httpx.TimeoutException as e:
                    if attempt < max_retries:
                        logger.warning(f"OpenAI timeout, tekrar deneniyor ({attempt + 1}/{max_retries})...")
                        await asyncio.sleep(2)
                    else:
                        raise Exception(f"OpenAI timeout hatasi: {e}")
                except Exception as e:
                    if attempt < max_retries:
                        logger.warning(f"OpenAI hatasi, tekrar deneniyor ({attempt + 1}/{max_retries}): {e}")
                        await asyncio.sleep(2)
                    else:
                        raise Exception(f"OpenAI API hatasi: {e}")
        return ""

    async def _call_ollama_async(self, prompt: str, max_retries: int = 2) -> str:
        """
        Ollama'ya asenkron istek gönder

        Args:
            prompt: Kullanıcı promptu
            max_retries: Hata durumunda tekrar deneme

        Returns:
            LLM yanıtı (JSON string)
        """
        url = f"{self.base_url}/api/chat"
        payload = self._get_llm_payload(prompt)

        async with httpx.AsyncClient(timeout=ASYNC_TIMEOUT) as client:
            for attempt in range(max_retries + 1):
                try:
                    resp = await client.post(url, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    content = data.get('message', {}).get('content', '')
                    logger.debug(f"Ollama async ham yanit: {content[:500]}...")
                    return content

                except httpx.TimeoutException as e:
                    if attempt < max_retries:
                        logger.warning(f"Ollama timeout, tekrar deneniyor ({attempt + 1}/{max_retries})...")
                        await asyncio.sleep(2)
                    else:
                        raise Exception(f"Ollama timeout hatasi: {e}")
                except Exception as e:
                    if attempt < max_retries:
                        logger.warning(f"Ollama hatasi, tekrar deneniyor ({attempt + 1}/{max_retries})...")
                        await asyncio.sleep(2)
                    else:
                        raise Exception(f"Ollama hatasi: {e}")
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
                            'independent_topics': data.get('independent_topics', data.get('topics', [])),
                            'retweet_summary': data.get('retweet_summary', ''),
                            'retweet_sources': data.get('retweet_sources', []),
                            'confidence_score': data.get('confidence_score', 0.5)  # Lower confidence for fallback
                        }
                        validated = schema_class(**fallback)
                        logger.info("Manuel alan cikarma basarili (confidence=0.5)")
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
                             party: Optional[str] = None, retweets: Optional[List[Dict]] = None) -> Dict:
        """
        Üç aşamalı (Yeşil, Kırmızı, Gri) profesyonel istihbarat analizi (senkron)

        Args:
            tweets: Orijinal tweet listesi
            username: Kullanıcı adı
            period: Analiz dönemi
            party: Meclis üyesinin partisi
            retweets: Retweet listesi (opsiyonel)

        Returns:
            IntelligenceAnalysis objesi kapsayan sözlük
        """
        # CHUNKED ANALYSIS: Eğer tweet sayısı çok fazlaysa, ilk 25 tweet ile analiz yap
        MAX_TWEETS = 25
        MAX_RETWEETS = 20

        if len(tweets) > MAX_TWEETS:
            logger.warning(f"Tweet sayısı ({len(tweets)}) maksimum limitin ({MAX_TWEETS}) üzerinde. İlk {MAX_TWEETS} tweet analiz edilecek.")
            tweets = tweets[:MAX_TWEETS]

        if retweets and len(retweets) > MAX_RETWEETS:
            logger.warning(f"Retweet sayısı ({len(retweets)}) maksimum limitin ({MAX_RETWEETS}) üzerinde. İlk {MAX_RETWEETS} retweet analiz edilecek.")
            retweets = retweets[:MAX_RETWEETS]

        total_count = len(tweets) + (len(retweets) if retweets else 0)
        prompt = get_prompt(
            'intelligence',
            tweets=tweets,
            retweets=retweets or [],
            username=username,
            party=party or "Bilinmiyor",
            tweet_count=total_count,
            period=period or "Tüm zamanlar"
        )

        logger.info(f"@{username} için profesyonel istihbarat analizi yapiliyor...")

        # Use metrics timer
        with LLMCallTimer(
            model=self.model,
            prompt_type="intelligence",
            username=username,
            tweet_count=len(tweets)
        ) as timer:
            try:
                response = self._call_llm(prompt)
            except Exception as e:
                timer.record_failure(str(e))
                return {
                    'username': username,
                    'party': party,
                    'tweet_count': len(tweets),
                    'period': period,
                    'error': str(e),
                    'elapsed_seconds': timer.latency_ms / 1000,
                    'validated': False
                }

        elapsed = timer.latency_ms / 1000
        logger.info(f"Tamamlandi ({elapsed:.1f}s)")

        # Parse and validate
        validated_data = self._parse_json_response(response, IntelligenceAnalysis)

        if validated_data:
            confidence = validated_data.confidence_score
            timer.record_success(validated=True, confidence_score=confidence)
            return {
                'username': username,
                'party': party,
                'tweet_count': len(tweets),
                'period': period,
                'raw_response': response,
                'analysis': validated_data,
                'elapsed_seconds': elapsed,
                'confidence_score': confidence,
                'validated': True
            }
        else:
            timer.record_success(validated=False)
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

    async def analyze_intelligence_async(self, tweets: List[Dict], username: str,
                                          period: Optional[str] = None,
                                          party: Optional[str] = None,
                                          retweets: Optional[List[Dict]] = None) -> Dict:
        """
        Üç aşamalı profesyonel istihbarat analizi (asenkron)

        Non-blocking LLM call - suitable for API endpoints.

        Args:
            tweets: Orijinal tweet listesi
            username: Kullanıcı adı
            period: Analiz dönemi
            party: Meclis üyesinin partisi
            retweets: Retweet listesi (opsiyonel)

        Returns:
            IntelligenceAnalysis objesi kapsayan sözlük
        """
        # CHUNKED ANALYSIS: Eğer tweet sayısı çok fazlaysa, ilk 25 tweet ile analiz yap
        MAX_TWEETS = 25
        MAX_RETWEETS = 20

        if len(tweets) > MAX_TWEETS:
            logger.warning(f"Tweet sayısı ({len(tweets)}) maksimum limitin ({MAX_TWEETS}) üzerinde. İlk {MAX_TWEETS} tweet analiz edilecek.")
            tweets = tweets[:MAX_TWEETS]

        if retweets and len(retweets) > MAX_RETWEETS:
            logger.warning(f"Retweet sayısı ({len(retweets)}) maksimum limitin ({MAX_RETWEETS}) üzerinde. İlk {MAX_RETWEETS} retweet analiz edilecek.")
            retweets = retweets[:MAX_RETWEETS]

        total_count = len(tweets) + (len(retweets) if retweets else 0)
        prompt = get_prompt(
            'intelligence',
            tweets=tweets,
            retweets=retweets or [],
            username=username,
            party=party or "Bilinmiyor",
            tweet_count=total_count,
            period=period or "Tüm zamanlar"
        )

        logger.info(f"@{username} için async istihbarat analizi yapiliyor...")

        # Use metrics timer
        with LLMCallTimer(
            model=self.model,
            prompt_type="intelligence_async",
            username=username,
            tweet_count=len(tweets)
        ) as timer:
            try:
                response = await self._call_llm_async(prompt)
            except Exception as e:
                timer.record_failure(str(e))
                return {
                    'username': username,
                    'party': party,
                    'tweet_count': len(tweets),
                    'period': period,
                    'error': str(e),
                    'elapsed_seconds': timer.latency_ms / 1000,
                    'validated': False
                }

        elapsed = timer.latency_ms / 1000
        logger.info(f"Async analiz tamamlandi ({elapsed:.1f}s)")

        # Parse and validate
        validated_data = self._parse_json_response(response, IntelligenceAnalysis)

        if validated_data:
            confidence = validated_data.confidence_score
            timer.record_success(validated=True, confidence_score=confidence)
            return {
                'username': username,
                'party': party,
                'tweet_count': len(tweets),
                'period': period,
                'raw_response': response,
                'analysis': validated_data,
                'elapsed_seconds': elapsed,
                'confidence_score': confidence,
                'validated': True
            }
        else:
            timer.record_success(validated=False)
            logger.warning("JSON validation failed for async IntelligenceAnalysis")
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
    Kullanıcı için tam analiz yap (tüm tweetler + retweetler)

    Args:
        username: Twitter kullanıcı adı

    Returns:
        Analiz sonucu
    """
    from app.core.db_config import session_scope
    from app.core.models import Tweet, Councilor

    # Tweetleri ve retweetleri al (ORM)
    try:
        with session_scope() as session:
            # Parti bilgisi - normalize et
            councilor = session.query(Councilor).filter(Councilor.username == username).first()
            party = normalize_party_name(councilor.party) if councilor else None

            # Orijinal tweetler
            tweets_query = session.query(
                Tweet.tweet_text, Tweet.tweet_date, Tweet.likes,
                Tweet.replies, Tweet.retweets, Tweet.views
            ).filter(
                Tweet.username == username,
                ~Tweet.is_retweet
            ).order_by(Tweet.tweet_date.desc()).all()

            # Retweetler
            retweets_query = session.query(
                Tweet.tweet_text, Tweet.tweet_date, Tweet.retweet_from
            ).filter(
                Tweet.username == username,
                Tweet.is_retweet == True
            ).order_by(Tweet.tweet_date.desc()).all()

            if not tweets_query and not retweets_query:
                return {'error': f'@{username} için tweet bulunamadı'}

            tweets = [
                {
                    'text': row[0],
                    'date': row[1],
                    'likes': row[2],
                    'replies': row[3],
                    'retweets': row[4],
                    'views': row[5] or 0
                }
                for row in tweets_query
            ]

            retweets = [
                {
                    'text': row[0],
                    'date': row[1],
                    'retweet_from': row[2] or 'bilinmiyor'
                }
                for row in retweets_query
            ]
    except Exception as e:
        logger.error(f"Database error: {e}")
        return {'error': f'Database error: {e}'}

    # Tarih aralığı
    all_dates = [t['date'] for t in tweets if t['date']] + [t['date'] for t in retweets if t['date']]
    period = f"{min(all_dates)} - {max(all_dates)}" if all_dates else "Bilinmiyor"

    # Analiz
    analyzer = TweetAnalyzer()
    result = analyzer.analyze_intelligence(tweets, username, period, party, retweets)

    return result


async def analyze_user_async(username: str) -> Dict:
    """
    Kullanıcı için async tam analiz yap (tüm tweetler + retweetler)

    Args:
        username: Twitter kullanıcı adı

    Returns:
        Analiz sonucu
    """
    from app.core.db_config import session_scope
    from app.core.models import Tweet, Councilor

    # Tweetleri, retweetleri ve parti bilgisini al
    try:
        with session_scope() as session:
            # Parti bilgisi - normalize et
            councilor = session.query(Councilor).filter(Councilor.username == username).first()
            party = normalize_party_name(councilor.party) if councilor else None

            # Orijinal tweetler
            tweets_query = session.query(
                Tweet.tweet_text, Tweet.tweet_date, Tweet.likes,
                Tweet.replies, Tweet.retweets, Tweet.views
            ).filter(
                Tweet.username == username,
                ~Tweet.is_retweet
            ).order_by(Tweet.tweet_date.desc()).all()

            # Retweetler
            retweets_query = session.query(
                Tweet.tweet_text, Tweet.tweet_date, Tweet.retweet_from
            ).filter(
                Tweet.username == username,
                Tweet.is_retweet == True
            ).order_by(Tweet.tweet_date.desc()).all()

            if not tweets_query and not retweets_query:
                return {'error': f'@{username} için tweet bulunamadı'}

            tweets = [
                {
                    'text': row[0],
                    'date': row[1],
                    'likes': row[2],
                    'replies': row[3],
                    'retweets': row[4],
                    'views': row[5] or 0
                }
                for row in tweets_query
            ]

            retweets = [
                {
                    'text': row[0],
                    'date': row[1],
                    'retweet_from': row[2] or 'bilinmiyor'
                }
                for row in retweets_query
            ]
    except Exception as e:
        logger.error(f"Database error: {e}")
        return {'error': f'Database error: {e}'}

    # Tarih aralığı
    all_dates = [t['date'] for t in tweets if t['date']] + [t['date'] for t in retweets if t['date']]
    period = f"{min(all_dates)} - {max(all_dates)}" if all_dates else "Bilinmiyor"

    # Async analiz
    analyzer = TweetAnalyzer()
    result = await analyzer.analyze_intelligence_async(tweets, username, period, party, retweets)

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