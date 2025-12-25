# 🏛️ Meclis İstihbarat Sistemi

Ankara Belediyesi meclis üyelerinin X/Twitter aktivitesini Qwen2.5 LLM ile analiz sistemi.

## Quick Start
```bash
# 1. Ollama (ayrı terminal)
OLLAMA_NUM_THREADS=6 ollama serve

# 2. Model
ollama pull qwen2.5:7b-instruct-q4_K_M

# 3. Dependency
pip install -r requirements.txt

# 4. Run
python meclis_app.py
```

## CSV Format
```
username,name,party,district
ahmet,Ahmet,AKP,Çankaya
```

---

Made with ❤️ for Ankara
