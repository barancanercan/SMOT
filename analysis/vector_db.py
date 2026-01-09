#!/usr/bin/env python3
"""
Vector Database v1.0 - ChromaDB Islemleri
- Tweet embedding saklama
- Similarity search
- Semantic arama
"""

import sys
import os
from typing import List, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ChromaDB path
CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db")

# Global client
_client = None
_collection = None


def get_client():
    """ChromaDB client'i al veya olustur"""
    global _client
    if _client is None:
        try:
            import chromadb
            from chromadb.config import Settings

            _client = chromadb.PersistentClient(
                path=CHROMA_PATH,
                settings=Settings(anonymized_telemetry=False)
            )
            print(f"ChromaDB baglantisi kuruldu: {CHROMA_PATH}")
        except ImportError:
            raise ImportError("chromadb yuklu degil: pip install chromadb")
    return _client


def get_collection(name: str = "tweets"):
    """Tweet collection'i al veya olustur"""
    global _collection
    if _collection is None or _collection.name != name:
        client = get_client()
        _collection = client.get_or_create_collection(
            name=name,
            metadata={"description": "Meclis uyeleri tweet embeddings"}
        )
        print(f"Collection: {name} ({_collection.count()} kayit)")
    return _collection


def add_tweet(
    tweet_id: int,
    username: str,
    text: str,
    embedding: List[float],
    metadata: Dict = None
):
    """
    Tek bir tweet ekle

    Args:
        tweet_id: Tweet ID (database'den)
        username: Kullanici adi
        text: Tweet metni
        embedding: Embedding vektoru
        metadata: Ek bilgiler (tarih, likes vs)
    """
    collection = get_collection()

    doc_id = f"tweet_{tweet_id}"

    meta = {
        "username": username,
        "tweet_id": tweet_id,
    }
    if metadata:
        meta.update(metadata)

    collection.upsert(
        ids=[doc_id],
        embeddings=[embedding],
        documents=[text],
        metadatas=[meta]
    )


def add_tweets_batch(tweets: List[Dict]):
    """
    Birden fazla tweet ekle (batch)

    Args:
        tweets: [{'id': int, 'username': str, 'text': str, 'embedding': List[float]}, ...]
    """
    if not tweets:
        return 0

    collection = get_collection()

    ids = [f"tweet_{t['id']}" for t in tweets]
    embeddings = [t['embedding'] for t in tweets]
    documents = [t['text'] for t in tweets]
    metadatas = [{"username": t['username'], "tweet_id": t['id']} for t in tweets]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )

    print(f"{len(tweets)} tweet ChromaDB'ye eklendi")
    return len(tweets)


def search_similar(
    query: str,
    n_results: int = 10,
    username: str = None
) -> List[Dict]:
    """
    Benzer tweetleri bul (semantic search)

    Args:
        query: Arama sorgusu
        n_results: Kac sonuc
        username: Belirli kullanici filtresi

    Returns:
        [{'text': str, 'username': str, 'distance': float, 'tweet_id': int}, ...]
    """
    from .embeddings import create_embedding

    collection = get_collection()

    # Query embedding
    query_embedding = create_embedding(query)

    # Filtre
    where_filter = None
    if username:
        where_filter = {"username": username}

    # Search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where_filter,
        include=["documents", "metadatas", "distances"]
    )

    # Format results
    formatted = []
    if results and results['ids'] and results['ids'][0]:
        for i in range(len(results['ids'][0])):
            formatted.append({
                'text': results['documents'][0][i],
                'username': results['metadatas'][0][i].get('username', ''),
                'tweet_id': results['metadatas'][0][i].get('tweet_id', 0),
                'distance': results['distances'][0][i] if results['distances'] else 0
            })

    return formatted


def search_by_embedding(
    embedding: List[float],
    n_results: int = 10,
    username: str = None
) -> List[Dict]:
    """
    Embedding vektoruyle benzer tweetleri bul

    Args:
        embedding: Arama embedding'i
        n_results: Kac sonuc
        username: Kullanici filtresi
    """
    collection = get_collection()

    where_filter = None
    if username:
        where_filter = {"username": username}

    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        where=where_filter,
        include=["documents", "metadatas", "distances"]
    )

    formatted = []
    if results and results['ids'] and results['ids'][0]:
        for i in range(len(results['ids'][0])):
            formatted.append({
                'text': results['documents'][0][i],
                'username': results['metadatas'][0][i].get('username', ''),
                'tweet_id': results['metadatas'][0][i].get('tweet_id', 0),
                'distance': results['distances'][0][i] if results['distances'] else 0
            })

    return formatted


def get_user_tweets(username: str, limit: int = 100) -> List[Dict]:
    """Kullanicinin tum tweetlerini getir"""
    collection = get_collection()

    results = collection.get(
        where={"username": username},
        limit=limit,
        include=["documents", "metadatas"]
    )

    formatted = []
    if results and results['ids']:
        for i in range(len(results['ids'])):
            formatted.append({
                'text': results['documents'][i],
                'username': results['metadatas'][i].get('username', ''),
                'tweet_id': results['metadatas'][i].get('tweet_id', 0)
            })

    return formatted


def get_stats() -> Dict:
    """ChromaDB istatistikleri"""
    collection = get_collection()

    return {
        'total_tweets': collection.count(),
        'collection_name': collection.name,
        'path': CHROMA_PATH
    }


def delete_user_tweets(username: str) -> int:
    """Kullanicinin tum tweetlerini sil"""
    collection = get_collection()

    # Kullanicinin tweet ID'lerini bul
    results = collection.get(
        where={"username": username},
        include=[]
    )

    if results and results['ids']:
        collection.delete(ids=results['ids'])
        return len(results['ids'])

    return 0


def rebuild_index(username: str = None):
    """
    Index'i yeniden olustur (database'den)

    Args:
        username: Belirli kullanici (None = tum kullanicilar)
    """
    from .embeddings import embed_tweets_from_db

    print("Index yeniden olusturuluyor...")

    # Mevcut verileri sil
    if username:
        deleted = delete_user_tweets(username)
        print(f"  {deleted} eski kayit silindi (@{username})")
    else:
        # Tum collection'i sil ve yeniden olustur
        client = get_client()
        try:
            client.delete_collection("tweets")
        except:
            pass
        global _collection
        _collection = None
        print("  Collection sifirlandi")

    # Yeni embeddingler olustur
    tweets = embed_tweets_from_db(username)

    if tweets:
        add_tweets_batch(tweets)
        print(f"  {len(tweets)} tweet indexlendi")

    return len(tweets)


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ChromaDB Vector Database")
    parser.add_argument("--search", help="Semantic arama")
    parser.add_argument("--user", help="Kullanici filtresi")
    parser.add_argument("--rebuild", action="store_true", help="Index yeniden olustur")
    parser.add_argument("--stats", action="store_true", help="Istatistikler")
    parser.add_argument("-n", type=int, default=5, help="Sonuc sayisi")

    args = parser.parse_args()

    if args.stats:
        stats = get_stats()
        print(f"\nChromaDB Istatistikleri:")
        for k, v in stats.items():
            print(f"  {k}: {v}")

    elif args.rebuild:
        count = rebuild_index(args.user)
        print(f"\nIndex olusturuldu: {count} tweet")

    elif args.search:
        print(f"\nArama: '{args.search}'")
        if args.user:
            print(f"Filtre: @{args.user}")

        results = search_similar(args.search, n_results=args.n, username=args.user)

        print(f"\nSonuclar ({len(results)}):")
        for i, r in enumerate(results, 1):
            print(f"\n{i}. @{r['username']} (distance: {r['distance']:.4f})")
            print(f"   {r['text'][:150]}...")

    else:
        print("Kullanim:")
        print("  python vector_db.py --stats")
        print("  python vector_db.py --rebuild")
        print("  python vector_db.py --rebuild --user username")
        print("  python vector_db.py --search 'ekonomi politikasi' -n 10")
        print("  python vector_db.py --search 'muhalefet' --user username")