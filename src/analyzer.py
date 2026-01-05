"""LLM-based tweet analyzer"""

import sys
import ollama
from typing import List, Dict
from config import OLLAMA_HOST, OLLAMA_MODEL


class Analyzer:
    """LLM-based tweet analyzer"""

    def __init__(self):
        self.client = ollama.Client(host=OLLAMA_HOST)
        self._test()

    def _test(self):
        """Test Ollama connection"""
        try:
            self.client.list()
            print("✅ Ollama connected")
        except Exception as e:
            print(f"❌ Ollama error: {e}")
            sys.exit(1)

    def analyze(self, tweets: List[Dict], username: str, question: str) -> str:
        """Analyze tweets and answer question"""
        if not tweets:
            return "⚠️ Tweet yok"

        # Format tweets with metadata
        tweets_formatted = []
        for i, tweet in enumerate(tweets[:15], 1):
            text = tweet.get("text", "")[:100]
            date = tweet.get("date", "N/A")
            is_rt = tweet.get("is_retweet", False)
            rt_from = tweet.get("retweet_from")
            likes = tweet.get("likes", 0)
            replies = tweet.get("replies", 0)
            retweets = tweet.get("retweets", 0)

            # Format tweet with metadata
            rt_label = f" [RT from @{rt_from}]" if is_rt else ""
            metrics = f" | ❤️{likes} 💬{replies} 🔄{retweets}"

            tweets_formatted.append(f"{i}. {text}{rt_label}{metrics}\n   📅 {date}")

        tweets_text = "\n\n".join(tweets_formatted)

        # Advanced prompt
        prompt = f"""[ROLE] 
Ankara Belediyesi meclis üyelerinin X/Twitter aktivitesini analiz eden siyaset bilimi uzmanı.

[ÜYENIN TWITTER ADRESÍ]
@{username}

[TWEETLER - METADATA İLE]
{tweets_text}

[SORU]
{question}

[TALİMATLAR]
- Sadece verilen tweetlerdeki kanıtları kullan
- Cevap NET, KISASPERİFİK olmalı (max 150 kelime)
- Tweet numaralarına referans ver (ör: Tweet 3'te gösterildiği gibi)
- Genel konuşmaktan kaçın
- Eğer tweetlerde yeterli bilgi yoksa "Verilen tweetlerde bu konuda bilgi bulunmuyor" de

[BAŞLA]
Cevap:"""

        try:
            response_text = ""
            for chunk in self.client.generate(
                    model=OLLAMA_MODEL,
                    prompt=prompt,
                    stream=True,
                    options={
                        "num_predict": 120,
                        "temperature": 0.3,
                        "top_p": 0.8,
                    }
            ):
                response_text += chunk.get("response", "")

            return response_text.strip()
        except Exception as e:
            return f"❌ Hata: {str(e)[:50]}"
