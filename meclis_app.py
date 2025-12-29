#!/usr/bin/env python3
"""
🏛️ Meclis İstihbarat Sistemi
CSV → X Scraping → Database → LLM Analysis → Report
"""

import os
import sys
import sqlite3
import time
from typing import List, Dict
from pathlib import Path

import gradio as gr
import pandas as pd
import ollama
from x_scraper import XTwitterScraper

# ============================================================================
# CONFIG
# ============================================================================

DB_PATH = "meclis.db"
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b-instruct-q4_K_M"

QUESTIONS = [
    "Bu üyenin ana gündemleri neler?",
    "Hangi konularda en çok tweet atıyor?",
    "Son ayda ne hakkında konuşmaya başladı?",
]


# ============================================================================
# DATABASE
# ============================================================================

def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tweets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            tweet_text TEXT NOT NULL,
            tweet_date TEXT,
            is_retweet BOOLEAN DEFAULT 0,
            retweet_from TEXT,
            likes INTEGER DEFAULT 0,
            replies INTEGER DEFAULT 0,
            retweets INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS councilors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT,
            party TEXT,
            district TEXT
        )
    """)

    conn.commit()
    conn.close()


def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def save_tweets(username: str, tweets: List, name: str = "", party: str = "", district: str = ""):
    """Save tweets to database (handles both strings and dicts)"""
    if not tweets:
        return

    conn = get_connection()
    cursor = conn.cursor()

    # Insert or update councilor
    cursor.execute(
        "INSERT OR REPLACE INTO councilors (username, name, party, district) VALUES (?, ?, ?, ?)",
        (username, name, party, district)
    )

    # Clear old tweets and insert new ones
    cursor.execute("DELETE FROM tweets WHERE username = ?", (username,))

    for tweet in tweets:
        # Handle both dict and string formats
        if isinstance(tweet, dict):
            text = tweet.get("text", "")[:500]
            tweet_date = tweet.get("timestamp")
            is_rt = tweet.get("is_retweet", False)
            rt_from = tweet.get("retweet_from")
            likes = tweet.get("likes", 0)
            replies = tweet.get("replies", 0)
            retweets = tweet.get("retweets", 0)
        else:
            text = str(tweet)[:500]
            tweet_date = None
            is_rt = text.strip().startswith("RT @")
            rt_from = None
            likes = 0
            replies = 0
            retweets = 0
            if is_rt:
                try:
                    rt_from = text.split(":")[0].replace("RT", "").replace("@", "").strip()
                except:
                    pass

        if text:
            cursor.execute(
                "INSERT INTO tweets (username, tweet_text, tweet_date, is_retweet, retweet_from, likes, replies, retweets) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (username, text, tweet_date, is_rt, rt_from, likes, replies, retweets)
            )

    conn.commit()
    conn.close()


def get_tweets(username: str) -> List[Dict]:
    """Get tweets for username with full metadata"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            tweet_text, 
            tweet_date, 
            is_retweet, 
            retweet_from,
            likes,
            replies,
            retweets
        FROM tweets 
        WHERE username = ? 
        ORDER BY tweet_date DESC
        LIMIT 50
    """, (username,))
    results = cursor.fetchall()
    conn.close()

    tweets_list = []
    for row in results:
        tweets_list.append({
            "text": row[0],
            "date": row[1],
            "is_retweet": row[2],
            "retweet_from": row[3],
            "likes": row[4],
            "replies": row[5],
            "retweets": row[6],
        })
    return tweets_list


def get_all_users() -> List[str]:
    """Get all usernames from database"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT username FROM councilors ORDER BY username")
    results = cursor.fetchall()
    conn.close()
    return [row[0] for row in results]


# ============================================================================
# LLM ANALYZER
# ============================================================================

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


# ============================================================================
# CSV PROCESSING
# ============================================================================

def parse_csv(csv_file) -> List[str]:
    """Parse CSV and extract usernames"""
    try:
        df = pd.read_csv(csv_file.name)
        usernames = []

        # Try username column
        if "username" in df.columns:
            for _, row in df.iterrows():
                u = str(row["username"]).replace("@", "").strip()
                if u and u != "nan":
                    usernames.append(u)

        # Try link column
        elif "link" in df.columns:
            for _, row in df.iterrows():
                link = str(row["link"]).strip()
                if link and ("x.com/" in link or "twitter.com/" in link):
                    u = link.split("/")[-1].replace("@", "").strip()
                    if u:
                        usernames.append(u)

        else:
            return []

        return list(set(usernames))  # Remove duplicates

    except Exception as e:
        print(f"❌ CSV Error: {e}")
        return []


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def scrape_and_analyze(csv_file) -> str:
    """
    Main pipeline:
    1. Parse CSV → get usernames
    2. Scrape tweets from X
    3. Save to database
    4. Analyze with LLM
    5. Generate report
    """

    if csv_file is None:
        return "❌ CSV dosyası seçin"

    # Step 1: Parse CSV
    print("\n" + "=" * 60)
    print("📊 MECLIS İSTİHBARAT SİSTEMİ")
    print("=" * 60)

    print("\n[1/4] CSV PARSING...")
    usernames = parse_csv(csv_file)

    if not usernames:
        return "❌ CSV'de username veya link bulunamadı"

    print(f"✅ {len(usernames)} üye bulundu")
    print(f"   {', '.join(usernames[:5])}")
    if len(usernames) > 5:
        print(f"   +{len(usernames) - 5} üye daha")

    # Step 2: Scrape tweets
    print("\n[2/4] X'TEN TWEETS FETCH EDILIYOR...")
    scraped_data = {}

    try:
        scraper = XTwitterScraper(
            headless=False,  # Browser görünsün
            username="yereldeetk",
            password="yereldeetkilesiyoruz.1"
        )
        results = scraper.scrape_multiple(usernames, max_tweets=60)
        scraper.close()
        scraped_data = results
    except Exception as e:
        print(f"⚠️  Scraping hatası: {str(e)[:80]}")
        print("   Fallback sample tweets modu")

    # Step 3: Save to database
    print("\n[3/4] DATABASE'YE KAYDEDILIYOR...")
    for username in usernames:
        tweets_data = scraped_data.get(username, [])
        # Handle both dict and string formats
        tweet_texts = []
        for t in tweets_data:
            if isinstance(t, dict):
                tweet_texts.append(t.get("text", ""))
            else:
                tweet_texts.append(str(t))

        save_tweets(username, tweet_texts)

    print(f"✅ {len(usernames)} üye kaydedildi")
    total_tweets = sum(len(scraped_data.get(u, [])) for u in usernames)
    print(f"   {total_tweets} tweet toplandı")

    # Step 4: Analyze with LLM
    print("\n[4/4] ANALIZ VE RAPOR OLUŞTURULUYOR...")
    analyzer = Analyzer()

    report = "# 📊 Ankara Meclis Üyeleri Analiz Raporu\n\n"

    for idx, username in enumerate(usernames, 1):
        tweets = get_tweets(username)

        if not tweets:
            continue

        print(f"\n[{idx}/{len(usernames)}] @{username} analiz ediliyor...")

        report += f"## 👤 @{username}\n\n"

        for q_idx, question in enumerate(QUESTIONS, 1):
            print(f"  ├─ Soru {q_idx}/3: {question[:35]}...", end=" ", flush=True)

            answer = analyzer.analyze(tweets, username, question)

            print("✅")

            report += f"### Q{q_idx}: {question}\n\n"
            report += f"{answer}\n\n"

        report += "---\n\n"

    print("\n" + "=" * 60)
    print("✅ RAPOR TAMAMLANDI!")
    print("=" * 60 + "\n")

    return report


# ============================================================================
# GRADIO UI
# ============================================================================

with gr.Blocks(title="🏛️ Meclis İstihbarat") as demo:
    gr.Markdown("# 🏛️ Ankara Meclis İstihbarat Sistemi")
    gr.Markdown("*CSV → X Scraping → LLM Analysis → Report*")

    with gr.Column():
        # File upload
        csv_input = gr.File(
            label="📁 Meclis Üyeleri CSV'si",
            file_types=[".csv"],
            file_count="single"
        )

        # Process button
        process_btn = gr.Button("🚀 BAŞLAT: Scrape & Analyze", variant="primary", size="lg")

        # Report output
        report_output = gr.Markdown(label="📊 Rapor")

        # Event handler (blocks içinde olmalı!)
        process_btn.click(scrape_and_analyze, csv_input, report_output)

# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    print("🏛️ Meclis İstihbarat Sistemi")
    init_database()
    print("✅ Database ready")
    print("🌐 UI açılıyor: http://127.0.0.1:7860\n")

    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        show_error=True,
        share=False
    )