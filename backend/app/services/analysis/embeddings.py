#!/usr/bin/env python3
"""
Embeddings v1.0 - Tweet Embedding Olusturma
- sentence-transformers ile embedding
- all-MiniLM-L6-v2 modeli (hizli, CPU uyumlu)
"""

from typing import List, Optional


# Lazy loading - model sadece gerektiginde yuklenir
_model = None
_model_name = "all-MiniLM-L6-v2"


def get_model():
    """Embedding modelini yukle (lazy loading)"""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            print(f"Embedding modeli yukleniyor: {_model_name}")
            _model = SentenceTransformer(_model_name)
            print(f"Model yuklendi: {_model_name}")
        except ImportError:
            raise ImportError("sentence-transformers yuklu degil: pip install sentence-transformers")
    return _model


def create_embedding(text: str) -> List[float]:
    """
    Tek bir metin icin embedding olustur

    Args:
        text: Embed edilecek metin

    Returns:
        384 boyutlu embedding vektoru
    """
    model = get_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


def create_embeddings_batch(texts: List[str], batch_size: int = 32, show_progress: bool = True) -> List[List[float]]:
    """
    Birden fazla metin icin embedding olustur (batch processing)

    Args:
        texts: Embed edilecek metinler
        batch_size: Batch boyutu
        show_progress: Progress bar goster

    Returns:
        Embedding vektorleri listesi
    """
    model = get_model()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        convert_to_numpy=True
    )
    return [emb.tolist() for emb in embeddings]


def get_embedding_dimension() -> int:
    """Embedding boyutunu dondur (384 for all-MiniLM-L6-v2)"""
    return 384


def preprocess_tweet(text: str) -> str:
    """
    Tweet metnini embedding icin hazirla

    - URL'leri kaldir
    - Mention'lari temizle
    - Fazla bosluklari kaldir
    """
    import re

    # URL kaldir
    text = re.sub(r'https?://\S+', '', text)

    # t.co linklerini kaldir
    text = re.sub(r't\.co/\S+', '', text)

    # Fazla bosluklari temizle
    text = ' '.join(text.split())

    return text.strip()


def embed_tweets_from_db(username: Optional[str] = None, limit: Optional[int] = None) -> List[dict]:
    """
    Database'deki tweetleri embed et

    Args:
        username: Belirli kullanici (None = tum kullanicilar)
        limit: Maksimum tweet sayisi

    Returns:
        [{'id': int, 'username': str, 'text': str, 'embedding': List[float]}, ...]
    """
    import sqlite3
    from app.core.config import DB_PATH

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = "SELECT id, username, tweet_text FROM tweets WHERE is_retweet = 0"
    from typing import Any
    params: List[Any] = []

    if username:
        query += " AND username = ?"
        params.append(username)

    if limit:
        query += " LIMIT ?"
        params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("Embed edilecek tweet bulunamadi")
        return []

    print(f"{len(rows)} tweet embed ediliyor...")

    # Metinleri hazirla
    texts = [preprocess_tweet(row[2]) for row in rows]

    # Batch embedding
    embeddings = create_embeddings_batch(texts)

    # Sonuclari birlestir
    results = []
    for i, row in enumerate(rows):
        results.append({
            'id': row[0],
            'username': row[1],
            'text': row[2],
            'processed_text': texts[i],
            'embedding': embeddings[i]
        })

    print(f"{len(results)} tweet embed edildi")
    return results


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Tweet Embedding")
    parser.add_argument("--test", action="store_true", help="Test embedding")
    parser.add_argument("--user", help="Belirli kullanici")
    parser.add_argument("--limit", type=int, help="Maksimum tweet")

    args = parser.parse_args()

    if args.test:
        # Test embedding
        test_text = "Bu bir test tweettir. Turkiye'de siyaset hakkinda konusuyoruz."
        print(f"Test metni: {test_text}")
        emb = create_embedding(test_text)
        print(f"Embedding boyutu: {len(emb)}")
        print(f"Ilk 5 deger: {emb[:5]}")
    else:
        # Database'den embed et
        results = embed_tweets_from_db(args.user, args.limit)
        if results:
            print("\nOrnek embedding:")
            print(f"  Tweet: {results[0]['text'][:100]}...")
            print(f"  Boyut: {len(results[0]['embedding'])}")