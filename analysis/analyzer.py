#!/usr/bin/env python3
"""
Analyzer v1.0 - Ollama LLM Entegrasyonu

- Ollama API baglantisi (HTTP)
- Tweet analizi (3 soru)
- Response parsing
"""

import sys
import os
from typing import Dict, List, Optional
import time
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .prompts import SYSTEM_PROMPT, get_prompt

# Default model
DEFAULT_MODEL = "qwen2.5:7b"
FALLBACK_MODEL = "qwen2.5:3b"
OLLAMA_URL = "http://127.0.0.1:11434"


class TweetAnalyzer:
    """Ollama ile tweet analizi (HTTP API)"""

    def __init__(self, model: str = None):
        """
        Args:
            model: Ollama model adi (default: qwen2.5:7b)
        """
        self.model = model or DEFAULT_MODEL
        self.base_url = OLLAMA_URL
        self._check_connection()

    def _check_connection(self):
        """Ollama baglantisini kontrol et"""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                models = data.get('models', [])
                model_names = [m.get('name', '') for m in models]
                if self.model not in model_names and f"{self.model}:latest" not in model_names:
                    print(f"Model '{self.model}' bulunamadi. Mevcut: {model_names}")
        except Exception as e:
            print(f"Ollama baglanti kontrolu: {e}")

    def _call_llm(self, prompt: str, max_retries: int = 2) -> str:
        """
        LLM'e istek gonder (HTTP API)

        Args:
            prompt: Kullanici promptu
            max_retries: Hata durumunda tekrar deneme

        Returns:
            LLM yaniti
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "options": {
                "temperature": 0.3,
                "num_predict": 1024
            },
            "stream": False
        }

        for attempt in range(max_retries + 1):
            try:
                resp = requests.post(url, json=payload, timeout=120)
                resp.raise_for_status()
                data = resp.json()
                return data.get('message', {}).get('content', '')

            except Exception as e:
                if attempt < max_retries:
                    print(f"  LLM hatasi, tekrar deneniyor ({attempt + 1}/{max_retries})...")
                    time.sleep(2)
                else:
                    raise Exception(f"LLM hatasi: {e}")

    def analyze_main_topics(self, tweets: List[Dict]) -> Dict:
        """
        Soru 1: Ana konulari analiz et

        Args:
            tweets: Tweet listesi

        Returns:
            {'raw_response': str, 'topics': List[str]}
        """
        prompt = get_prompt('main_topics', tweets=tweets)

        print("  Ana konular analiz ediliyor...")
        start = time.time()
        response = self._call_llm(prompt)
        elapsed = time.time() - start
        print(f"  Tamamlandi ({elapsed:.1f}s)")

        return {
            'raw_response': response,
            'topics': self._parse_topics(response),
            'elapsed_seconds': elapsed
        }

    def analyze_party_defense(self, tweets: List[Dict]) -> Dict:
        """
        Soru 2: Parti/lider savunusu analizi

        Args:
            tweets: Tweet listesi

        Returns:
            {'raw_response': str, 'defended': str, 'intensity': str}
        """
        prompt = get_prompt('party_defense', tweets=tweets)

        print("  Parti savunusu analiz ediliyor...")
        start = time.time()
        response = self._call_llm(prompt)
        elapsed = time.time() - start
        print(f"  Tamamlandi ({elapsed:.1f}s)")

        return {
            'raw_response': response,
            'defended': self._parse_defended(response),
            'intensity': self._parse_intensity(response, 'savunma'),
            'elapsed_seconds': elapsed
        }

    def analyze_opposition_criticism(self, tweets: List[Dict]) -> Dict:
        """
        Soru 3: Muhalefet elestirisi analizi

        Args:
            tweets: Tweet listesi

        Returns:
            {'raw_response': str, 'criticized': str, 'intensity': str}
        """
        prompt = get_prompt('opposition', tweets=tweets)

        print("  Muhalefet elestirisi analiz ediliyor...")
        start = time.time()
        response = self._call_llm(prompt)
        elapsed = time.time() - start
        print(f"  Tamamlandi ({elapsed:.1f}s)")

        return {
            'raw_response': response,
            'criticized': self._parse_criticized(response),
            'intensity': self._parse_intensity(response, 'elestiri'),
            'elapsed_seconds': elapsed
        }

    def analyze_full(self, tweets: List[Dict], username: str, period: str = None, party: str = None) -> Dict:
        """
        Tam analiz (3 soru birden)

        Args:
            tweets: Tweet listesi
            username: Kullanici adi
            period: Analiz donemi
            party: Meclis uyesinin partisi

        Returns:
            Tam analiz sonucu
        """
        prompt = get_prompt(
            'full',
            tweets=tweets,
            username=username,
            party=party or "Bilinmiyor",
            tweet_count=len(tweets),
            period=period or "Tum zamanlar"
        )

        print(f"  @{username} ({party or 'Parti?'}) tam analiz yapiliyor...")
        start = time.time()
        response = self._call_llm(prompt)
        elapsed = time.time() - start
        print(f"  Tamamlandi ({elapsed:.1f}s)")

        return {
            'username': username,
            'party': party,
            'tweet_count': len(tweets),
            'period': period,
            'raw_response': response,
            'elapsed_seconds': elapsed
        }

    # =========================================================================
    # RESPONSE PARSING
    # =========================================================================

    def _parse_topics(self, response: str) -> List[str]:
        """Ana konulari parse et"""
        topics = []
        lines = response.split('\n')

        for line in lines:
            line = line.strip()
            # "1. **Konu**" veya "- Konu:" formatini yakala
            if line and (line[0].isdigit() or line.startswith('-')):
                # ** isaretlerini temizle
                topic = line.lstrip('0123456789.-) ').strip()
                topic = topic.replace('**', '').strip()
                if topic and len(topic) > 2:
                    # Ilk kelimeyi veya : oncesini al
                    if ':' in topic:
                        topic = topic.split(':')[0].strip()
                    topics.append(topic)

        return topics[:5]  # En fazla 5 konu

    def _parse_defended(self, response: str) -> str:
        """Savunulan parti/lideri parse et"""
        keywords = ['savunulan', 'parti/lider', 'savunulan parti']

        for line in response.split('\n'):
            line_lower = line.lower()
            for kw in keywords:
                if kw in line_lower:
                    # : sonrasini al
                    if ':' in line:
                        value = line.split(':', 1)[1].strip()
                        value = value.replace('**', '').strip()
                        if value and value.lower() not in ['yok', 'belirgin savunma yok', '-']:
                            return value
        return "Belirgin savunma yok"

    def _parse_criticized(self, response: str) -> str:
        """Elestirilen parti/kisileri parse et"""
        keywords = ['elestirilen', 'elestirilen parti']

        for line in response.split('\n'):
            line_lower = line.lower()
            for kw in keywords:
                if kw in line_lower:
                    if ':' in line:
                        value = line.split(':', 1)[1].strip()
                        value = value.replace('**', '').strip()
                        if value and value.lower() not in ['yok', 'belirgin elestiri yok', '-']:
                            return value
        return "Belirgin elestiri yok"

    def _parse_intensity(self, response: str, type_: str) -> str:
        """Siddet seviyesini parse et (Guclu/Orta/Zayif/Yok veya Sert/Orta/Hafif/Yok)"""
        keywords = ['siddet', 'siddeti']

        for line in response.split('\n'):
            line_lower = line.lower()
            for kw in keywords:
                if kw in line_lower:
                    if ':' in line:
                        value = line.split(':', 1)[1].strip()
                        value = value.replace('**', '').strip()
                        # Bilinen degerlerden birini bul
                        for level in ['Guclu', 'Sert', 'Orta', 'Zayif', 'Hafif', 'Yok']:
                            if level.lower() in value.lower():
                                return level
        return "Belirsiz"


# ============================================================================
# YARDIMCI FONKSIYONLAR
# ============================================================================

def analyze_user(username: str, limit: int = 30) -> Dict:
    """
    Kullanici icin tam analiz yap

    Args:
        username: Twitter kullanici adi
        limit: Analiz edilecek tweet sayisi

    Returns:
        Analiz sonucu
    """
    import sqlite3
    from config import DB_PATH

    # Tweetleri al
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT tweet_text, tweet_date, likes, replies, retweets
        FROM tweets
        WHERE username = ? AND is_retweet = 0
        ORDER BY tweet_date DESC
        LIMIT ?
    """, (username, limit))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {'error': f'@{username} icin tweet bulunamadi'}

    tweets = [
        {
            'text': row[0],
            'date': row[1],
            'likes': row[2],
            'replies': row[3],
            'retweets': row[4]
        }
        for row in rows
    ]

    # Tarih araligi
    dates = [t['date'] for t in tweets if t['date']]
    period = f"{min(dates)} - {max(dates)}" if dates else "Bilinmiyor"

    # Analiz
    analyzer = TweetAnalyzer()
    result = analyzer.analyze_full(tweets, username, period)

    return result


def analyze_user_with_vector_search(username: str, query: str, limit: int = 20) -> Dict:
    """
    Vector search ile ilgili tweetleri bulup analiz et

    Args:
        username: Kullanici adi
        query: Arama sorgusu (ornegin "ekonomi politikasi")
        limit: Kac tweet analiz edilecek

    Returns:
        Analiz sonucu
    """
    from .vector_db import search_similar

    # Ilgili tweetleri bul
    results = search_similar(query, n_results=limit, username=username)

    if not results:
        return {'error': f'@{username} icin "{query}" ile ilgili tweet bulunamadi'}

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

    parser = argparse.ArgumentParser(description="Tweet Analiz (Ollama LLM)")
    parser.add_argument("--user", help="Kullanici adi")
    parser.add_argument("--query", help="Vector search sorgusu")
    parser.add_argument("--limit", type=int, default=30, help="Tweet limiti")
    parser.add_argument("--model", help="Ollama model (default: qwen2.5:7b)")
    parser.add_argument("--test", action="store_true", help="Baglanti testi")

    args = parser.parse_args()

    if args.test:
        print("Ollama baglanti testi...")
        try:
            analyzer = TweetAnalyzer(args.model)
            print(f"Model: {analyzer.model}")
            print("Baglanti OK!")
        except Exception as e:
            print(f"Hata: {e}")

    elif args.user:
        if args.query:
            result = analyze_user_with_vector_search(args.user, args.query, args.limit)
        else:
            result = analyze_user(args.user, args.limit)

        if 'error' in result:
            print(f"Hata: {result['error']}")
        else:
            print(f"\n{'='*60}")
            print(f"@{result['username']} ANALIZ SONUCU")
            print(f"{'='*60}")
            print(f"Tweet sayisi: {result['tweet_count']}")
            print(f"Donem: {result['period']}")
            print(f"Sure: {result['elapsed_seconds']:.1f}s")
            print(f"{'='*60}")
            print(result['raw_response'])
            print(f"{'='*60}")

    else:
        print("Kullanim:")
        print("  python analyzer.py --test")
        print("  python analyzer.py --user username")
        print("  python analyzer.py --user username --query 'ekonomi'")
        print("  python analyzer.py --user username --model qwen2.5:3b")