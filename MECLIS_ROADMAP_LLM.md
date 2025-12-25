# 🏛️ Meclis İstihbarat Sistemi - LLM-Centric Roadmap

## 📊 Sistem Vizyonu (Revize)

**Amaç:** Ankara Belediyesi meclis üyelerinin X/Twitter aktivitesini LLM-powered RAG sistemi ile analiz eden basit, ücretsiz, açık kaynak platform.

**Temel Felsefe:**
- ✅ **LLM-First:** Qwen2.5-7B (local via Ollama) tüm analiz işleri yapar
- ✅ **Super MVP:** 150 satır kod ile başla
- ✅ **No Over-engineering:** Sadece çalışan sistem
- ✅ **Local & Private:** Ollama → no API keys, no cloud
- ✅ **RAG-based:** Councilor tweets → vector store → LLM answers questions

---

## 🔍 Benzer Uygulamalar (Araştırma Özeti)

### Existing X Analytics Tools
- **Sprout Social, Hootsuite:** Enterprise tools, expensive
- **Twitonomy, Followerwonk:** Limited by API, basic metrics only
- **Minter.io, Dash Social:** Simple dashboards, generic insights

### 🎯 Key Insight
Hiçbiri **LLM-powered deep insight** sunmuyor. Sadece metrics:
- "Bu kişi kaç takipçi kazandı?" ← Metrics
- "Bu kişi ne hakkında konuşuyor gerçekten?" ← LLM lazım
- "Sentiment değişimleri neler?" ← LLM analizi

**Bizim Farkımız:**
```
Existing: Tweets → Extract metrics → Dashboard
         (Meaningless numbers without context)

Our System: Tweets → Vector Store → Qwen2.5 LLM
           "Bu üye hakkında ne söyleyebilirsin?"
           ↓
           Detailed Turkish insight + sources
```

---

## 🏗️ System Architecture (Minimal)

```
INPUT: CSV ile meclis üyesi @handles
           ↓
COLLECT: Selenium X scraper → son 100 tweet
           ↓
STORE: SQLite (tweet text + metadata)
           ↓
EMBED: Ollama embeddings (nomic-embed-text)
           ↓
INDEX: Vector store (Chroma)
           ↓
QUERY: "Bu kişi hakkında ne söyleyebilirsin?"
           ↓
ANSWER: Qwen2.5-7B LLM (context-aware, Turkish)
           ↓
OUTPUT: Gradio web interface
```

---

## 📱 MVP - Faz 1 (1 Hafta)

**Deliverable:** Gradio interface + Local LLM = "Ask Questions"

### 1.1 Tech Stack

| Layer | Tool | Why |
|-------|------|-----|
| **Scraping** | Selenium (x_scrapper) | Already have working code |
| **LLM** | Qwen2.5-7B (via Ollama) | Turkish-native, local, free |
| **Vector DB** | SQLite (simple) | No dependencies, works everywhere |
| **Interface** | Gradio | Fast web UI |
| **Orchestration** | Simple Python script | MVP = no frameworks |

### 1.2 Setup

```bash
# 1. Install Ollama
# Download from https://ollama.com (free)

# 2. Pull Qwen model (one-liner)
ollama pull qwen2.5:7b  # ~4.7GB (one time)

# 3. Python dependencies
pip install selenium webdriver-manager gradio pandas ollama sqlalchemy

# 4. Test LLM is running
ollama list  # Should show qwen2.5:7b
```

### 1.3 MVP Code Structure

**app.py (Main application - ~250 lines total)**

```python
import gradio as gr
import ollama
import pandas as pd
import sqlite3
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time

# ============ CONFIG ============
OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_HOST = "http://localhost:11434"
DB_FILE = "councilors.db"

# ============ DATABASE ============
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tweets (
            id INTEGER PRIMARY KEY,
            username TEXT,
            tweet_text TEXT,
            tweet_date TEXT,
            likes INTEGER,
            retweets INTEGER,
            url TEXT
        )
    ''')
    conn.commit()
    return conn

# ============ SCRAPER ============
def fetch_tweets(username, max_count=100):
    """Fetch recent tweets from a councilor"""
    # Simple Selenium scraper (adapt from x_scrapper)
    tweets = []
    
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(options=options)
        
        # X profile URL
        driver.get(f"https://x.com/{username}")
        time.sleep(3)
        
        # Scroll and collect tweets
        for _ in range(5):  # 5 scrolls = ~25 tweets
            articles = driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
            
            for article in articles[:max_count]:
                try:
                    text = article.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]').text
                    tweets.append({
                        'username': username,
                        'text': text[:500],  # Limit to 500 chars
                        'date': None,  # Optional: extract with better parsing
                        'url': None
                    })
                except:
                    pass
            
            if len(tweets) >= max_count:
                break
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        driver.quit()
        
    except Exception as e:
        print(f"Scraping error: {e}")
    
    return tweets

# ============ STORAGE ============
def save_tweets(conn, tweets):
    """Save tweets to SQLite"""
    cursor = conn.cursor()
    for tweet in tweets:
        cursor.execute('''
            INSERT OR REPLACE INTO tweets 
            (username, tweet_text, tweet_date, likes, retweets, url)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            tweet['username'],
            tweet['text'],
            tweet.get('date'),
            tweet.get('likes', 0),
            tweet.get('retweets', 0),
            tweet.get('url', '')
        ))
    conn.commit()

def get_council_tweets(conn, username):
    """Get all stored tweets for a councilor"""
    cursor = conn.cursor()
    cursor.execute('SELECT tweet_text FROM tweets WHERE username = ?', (username,))
    results = cursor.fetchall()
    return [row[0] for row in results]

# ============ LLM ANALYSIS ============
def ask_qwen(question, context_tweets, username):
    """Ask Qwen2.5 a question about the councilor"""
    
    # Prepare context
    tweets_context = "\n".join([f"- {t}" for t in context_tweets[:20]])  # Last 20 tweets
    
    system_prompt = """Sen Ankara Belediyesi meclis üyelerinin Twitter aktivitesini analiz eden bir asistan.
Verilen tweetlere bakarak sorular yanıtla. Cevaplarını kısa ve tutarlı tut. Türkçe konuş."""
    
    user_prompt = f"""
Meclis üyesi: {username}

Son tweetleri:
{tweets_context}

Soru: {question}

Cevap (kısa ve açık):"""
    
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        response = client.generate(
            model=OLLAMA_MODEL,
            prompt=user_prompt,
            system=system_prompt,
            stream=False,
            num_predict=200  # Max 200 tokens response
        )
        return response['response']
    except Exception as e:
        return f"❌ LLM error: {e}"

# ============ GRADIO INTERFACE ============

def upload_csv(csv_file):
    """Upload CSV and fetch tweets"""
    if csv_file is None:
        return "❌ Lütfen CSV dosyası yükleyin", []
    
    try:
        df = pd.read_csv(csv_file.name)
        conn = init_db()
        
        results = []
        for _, row in df.iterrows():
            username = row['username'].replace('@', '').strip()
            
            # Fetch tweets
            tweets = fetch_tweets(username, max_count=100)
            if tweets:
                save_tweets(conn, tweets)
                results.append(f"✅ {username}: {len(tweets)} tweet toplandı")
            else:
                results.append(f"⚠️ {username}: Tweet bulunamadı")
        
        status_msg = "\n".join(results)
        usernames = [row['username'].replace('@', '') for _, row in df.iterrows()]
        
        return f"✅ Tamamlandı!\n\n{status_msg}", usernames
        
    except Exception as e:
        return f"❌ Error: {e}", []

def ask_question(username, question):
    """Ask a question about a councilor"""
    if not username or not question:
        return "❌ Lütfen üye seçin ve soru yazın"
    
    conn = sqlite3.connect(DB_FILE)
    tweets = get_council_tweets(conn, username)
    
    if not tweets:
        return f"❌ {username} için tweet bulunamadı. Lütfen önce tweet toplayın."
    
    answer = ask_qwen(question, tweets, username)
    return answer

# ============ MAIN INTERFACE ============

with gr.Blocks(title="🏛️ Meclis İstihbarat Sistemi", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🏛️ Meclis İstihbarat Sistemi")
    gr.Markdown("*Ankara Belediyesi meclis üyeleri X/Twitter aktiviteleri - LLM powered*")
    
    with gr.Column():
        # Section 1: Upload & Fetch
        gr.Markdown("## 📥 Faz 1: Tweet Topla")
        
        with gr.Row():
            csv_input = gr.File(label="📄 CSV Dosyası (username, name, party)", type="filepath")
            fetch_btn = gr.Button("🚀 Tweet Topla", scale=1, variant="primary")
        
        fetch_status = gr.Textbox(label="Durum", interactive=False, lines=4)
        
        # Section 2: Ask Questions
        gr.Markdown("## ❓ Faz 2: Soru Sor")
        
        with gr.Row():
            username_dropdown = gr.Dropdown(label="👤 Üye Seçin", choices=[])
            question_input = gr.Textbox(
                label="❓ Soru",
                placeholder="Örn: Bu üyenin ana gündemleri neler?",
                lines=2
            )
        
        ask_btn = gr.Button("🤖 Sor", variant="primary")
        answer_output = gr.Textbox(label="💡 Qwen2.5 Cevabı", lines=6, interactive=False)
    
    # Event handlers
    fetch_btn.click(
        upload_csv,
        inputs=csv_input,
        outputs=[fetch_status, username_dropdown]
    )
    
    ask_btn.click(
        ask_question,
        inputs=[username_dropdown, question_input],
        outputs=answer_output
    )

if __name__ == "__main__":
    init_db()
    print("🚀 Starting Meclis Intelligence System...")
    print("ℹ️ Make sure Ollama is running: ollama serve")
    demo.launch()
```

### 1.4 Example Questions (Turkish)

```
"Bu üye ne hakkında en çok tweeti atıyor?"
"Katılımcılar hangi tweetlerine en çok tepki verdi?"
"Son 30 gün aktivitesi nasıl?"
"En popüler konuları neler?"
"Partisi içinde ne kadar aktif?"
"Günü gün konuştuğu konular neler?"
```

### 1.5 Files

```
meclis_llm/
├── app.py                      # Main application (250 lines)
├── requirements.txt            # pip packages
├── councilors_example.csv      # Example input
├── README.md                   # Installation guide
└── .gitignore
```

### 1.6 Checklist

- [ ] Ollama installed & running (`ollama serve`)
- [ ] Qwen2.5-7B pulled (`ollama pull qwen2.5:7b`)
- [ ] Python 3.10+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Test LLM: `ollama run qwen2.5:7b "Merhaba"`
- [ ] Test app: `python app.py`
- [ ] Upload example CSV
- [ ] Ask a question → Get Turkish answer

---

## 🔄 Faz 2: RAG + Vector Store (1-2 hafta)

**Upgrade:** Better context retrieval, persistent vector DB

```python
# src/rag.py
from langchain.vectorstores import Chroma
from langchain.embeddings.ollama import OllamaEmbeddings
from langchain.text_splitters import RecursiveCharacterTextSplitter

class CouncilorRAG:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        self.vectorstore = Chroma(embedding_function=self.embeddings)
    
    def add_tweets(self, username, tweets):
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        splits = splitter.split_text("\n".join(tweets))
        self.vectorstore.add_texts(splits, metadatas=[{"username": username}] * len(splits))
    
    def query(self, question, username):
        docs = self.vectorstore.similarity_search(question, k=5)
        context = "\n".join([d.page_content for d in docs])
        return ask_qwen(question, context, username)
```

---

## 📊 Faz 3: Automated Insights (2 hafta)

**LLM-powered daily reports:**
```python
# "Bu haftanın ana konuları neler?"
# "En aktif 3 üye"
# "Trend konular"
# "Sentiment: Pozitif/Negatif ratio"
```

---

## 💾 Faz 4: Historical + Scheduler (1 hafta)

```python
# APScheduler → Günde 1x tweet çek
# Weekly report generation
# Trend tracking over time
```

---

## 🎯 What Makes This Different from Old Roadmap

| Old Approach | New Approach |
|---|---|
| Complex metrics calculation | LLM does all thinking |
| Multiple NLP tools (zeyrek, etc.) | Single Qwen2.5-7B model |
| 5 separate dashboards | 1 Q&A interface |
| Over-engineered database | Simple SQLite |
| 8-10 weeks | 4-5 weeks total |
| 500+ lines core | 250 lines MVP |

---

## ⏱️ Timeline

| Phase | Duration | Output |
|-------|----------|--------|
| **MVP (Faz 1)** | 1 week | Working Q&A system |
| **RAG (Faz 2)** | 1-2 weeks | Better context retrieval |
| **Analytics (Faz 3)** | 2 weeks | Automated reports |
| **Production (Faz 4)** | 1 week | Scheduler + Polish |
| **TOTAL** | ~5 weeks | Full system |

---

## 🚀 Getting Started

### Step 1: Install Ollama
```bash
# Download from https://ollama.com
# Run: ollama serve  # Keep running in background
```

### Step 2: Pull Model
```bash
ollama pull qwen2.5:7b
# Wait ~5 minutes (4.7 GB download)
```

### Step 3: Clone & Setup
```bash
git clone <repo>
cd meclis_llm
pip install -r requirements.txt
```

### Step 4: Run
```bash
python app.py
# Opens at http://localhost:7860
```

### Step 5: Use
1. Prepare `councilors.csv`:
   ```csv
   username,name,party,district
   ahmet_sahin,Ahmet Şahin,AKP,Çankaya
   fatma_yilmaz,Fatma Yılmaz,CHP,Keçiören
   ```
2. Upload CSV → Fetch tweets
3. Select councilor → Ask question
4. Get Turkish insight from Qwen2.5

---

## 💾 Requirements

```
# requirements.txt
selenium>=4.15.0
webdriver-manager>=4.0.1
gradio>=4.0.0
pandas>=2.0.0
ollama>=0.1.0
langchain>=0.1.0
chromadb>=0.4.0
```

---

## 📝 Why This Works

1. **LLM-Native:** No custom metrics, just ask questions
2. **Turkish-First:** Qwen2.5 = 18T tokens Turkish data
3. **Local:** Ollama = no cloud, no API keys, 100% private
4. **Simple:** 250 lines MVP vs 500+ lines complex system
5. **Extensible:** Easy to add features as RAG + agents

---

## Next Steps

1. **This evening:** Setup Ollama + test Qwen2.5
2. **Tomorrow:** Write MVP app.py
3. **This week:** Full MVP working + GitHub push
4. **Next week:** Add RAG layer

---

## Questions?

- **How much disk space?** 10GB (Qwen2.5-7B)
- **How much RAM?** 8GB minimum (LLM in memory)
- **GPU needed?** Optional (CPU works, slower)
- **Turkish support?** Yes, Qwen2.5 is multilingual (Turkish excellent)

---

Ready to build this? Let's ship the MVP first. 🚀
