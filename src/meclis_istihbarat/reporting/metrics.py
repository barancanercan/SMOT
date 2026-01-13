#!/usr/bin/env python3
"""
Metrics v1.0 - Tweet Metrik Hesaplama
- Etkilesim hesaplama (engagement)
- Tarih arasi karsilastirma
- En iyi tweetleri bulma
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from meclis_istihbarat.core.config import DB_PATH


def calculate_engagement(likes: int, replies: int, retweets: int, views: int = 0) -> Dict:
    """
    Tweet icin etkilesim metriklerini hesapla

    Returns:
        {
            'total_engagement': int (likes + replies + retweets),
            'engagement_rate': float (engagement / views * 100 if views > 0)
        }
    """
    total = likes + replies + retweets
    rate = (total / views * 100) if views > 0 else 0.0

    return {
        'total_engagement': total,
        'engagement_rate': round(rate, 4)
    }


def get_user_engagement_stats(username: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
    """
    Kullanici icin toplam etkilesim istatistikleri

    Args:
        username: Twitter kullanici adi
        start_date: Baslangic tarihi (YYYY-MM-DD)
        end_date: Bitis tarihi (YYYY-MM-DD)

    Returns:
        {
            'username': str,
            'tweet_count': int,
            'total_likes': int,
            'total_replies': int,
            'total_retweets': int,
            'total_views': int,
            'total_engagement': int,
            'avg_engagement_per_tweet': float,
            'avg_engagement_rate': float,
            'period': {'start': str, 'end': str}
        }
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
        SELECT
            COUNT(*) as tweet_count,
            COALESCE(SUM(likes), 0) as total_likes,
            COALESCE(SUM(replies), 0) as total_replies,
            COALESCE(SUM(retweets), 0) as total_retweets,
            COALESCE(SUM(views), 0) as total_views
        FROM tweets
        WHERE username = ? AND is_retweet = 0
    """
    params = [username]

    if start_date:
        query += " AND tweet_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND tweet_date <= ?"
        params.append(end_date)

    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()

    if not row or row[0] == 0:
        return {
            'username': username,
            'tweet_count': 0,
            'total_likes': 0,
            'total_replies': 0,
            'total_retweets': 0,
            'total_views': 0,
            'total_engagement': 0,
            'avg_engagement_per_tweet': 0.0,
            'avg_engagement_rate': 0.0,
            'period': {'start': start_date, 'end': end_date}
        }

    tweet_count, total_likes, total_replies, total_retweets, total_views = row
    total_engagement = total_likes + total_replies + total_retweets
    avg_per_tweet = total_engagement / tweet_count if tweet_count > 0 else 0
    avg_rate = (total_engagement / total_views * 100) if total_views > 0 else 0

    return {
        'username': username,
        'tweet_count': tweet_count,
        'total_likes': total_likes,
        'total_replies': total_replies,
        'total_retweets': total_retweets,
        'total_views': total_views,
        'total_engagement': total_engagement,
        'avg_engagement_per_tweet': round(avg_per_tweet, 2),
        'avg_engagement_rate': round(avg_rate, 4),
        'period': {'start': start_date, 'end': end_date}
    }


def compare_periods(
    username: str,
    period1_start: str,
    period1_end: str,
    period2_start: str,
    period2_end: str
) -> Dict:
    """
    Iki donem arasindaki etkilesim degisimini karsilastir

    Returns:
        {
            'username': str,
            'period1': {...},
            'period2': {...},
            'changes': {
                'tweet_count_change': int,
                'engagement_change': int,
                'engagement_change_pct': float,
                'avg_engagement_change': float
            }
        }
    """
    period1 = get_user_engagement_stats(username, period1_start, period1_end)
    period2 = get_user_engagement_stats(username, period2_start, period2_end)

    engagement_change = period2['total_engagement'] - period1['total_engagement']
    engagement_pct = 0.0
    if period1['total_engagement'] > 0:
        engagement_pct = (engagement_change / period1['total_engagement']) * 100

    return {
        'username': username,
        'period1': period1,
        'period2': period2,
        'changes': {
            'tweet_count_change': period2['tweet_count'] - period1['tweet_count'],
            'engagement_change': engagement_change,
            'engagement_change_pct': round(engagement_pct, 2),
            'avg_engagement_change': round(
                period2['avg_engagement_per_tweet'] - period1['avg_engagement_per_tweet'], 2
            )
        }
    }


def compare_last_weeks(username: str, weeks: int = 2) -> Dict:
    """
    Son N haftayi bir onceki N hafta ile karsilastir

    Args:
        username: Kullanici adi
        weeks: Karsilastirilacak hafta sayisi (default 2)
    """
    today = datetime.now()

    # Period 2: Son N hafta
    period2_end = today.strftime("%Y-%m-%d")
    period2_start = (today - timedelta(weeks=weeks)).strftime("%Y-%m-%d")

    # Period 1: Onceki N hafta
    period1_end = (today - timedelta(weeks=weeks)).strftime("%Y-%m-%d")
    period1_start = (today - timedelta(weeks=weeks*2)).strftime("%Y-%m-%d")

    return compare_periods(username, period1_start, period1_end, period2_start, period2_end)


# ============================================================================
# EN IYI TWEETLER
# ============================================================================

def get_top_tweets(
    username: str,
    limit: int = 10,
    sort_by: str = 'engagement',
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    include_retweets: bool = False
) -> List[Dict]:
    """
    En iyi tweetleri getir

    Args:
        username: Kullanici adi
        limit: Kac tweet getirilecek
        sort_by: Siralama kriteri ('engagement', 'likes', 'replies', 'retweets', 'views')
        start_date: Baslangic tarihi
        end_date: Bitis tarihi
        include_retweets: RT'leri dahil et

    Returns:
        Tweet listesi (en yuksekten dusuge)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Siralama kolonu
    sort_column = {
        'engagement': '(likes + replies + retweets)',
        'likes': 'likes',
        'replies': 'replies',
        'retweets': 'retweets',
        'views': 'views'
    }.get(sort_by, '(likes + replies + retweets)')

    query = """
        SELECT
            tweet_text,
            tweet_date,
            likes,
            replies,
            retweets,
            views,
            (likes + replies + retweets) as engagement,
            is_retweet,
            retweet_from
        FROM tweets
        WHERE username = ?
    """
    params = [username]

    if not include_retweets:
        query += " AND is_retweet = 0"

    if start_date:
        query += " AND tweet_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND tweet_date <= ?"
        params.append(end_date)

    query += f" ORDER BY {sort_column} DESC LIMIT ?"
    params.append(str(limit))

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        tweet_text, tweet_date, likes, replies, retweets, views, engagement, is_rt, rt_from = row
        eng_rate = (engagement / views * 100) if views > 0 else 0

        results.append({
            'text': tweet_text,
            'full_text': tweet_text,
            'date': tweet_date,
            'likes': likes,
            'replies': replies,
            'retweets': retweets,
            'views': views,
            'engagement': engagement,
            'engagement_rate': round(eng_rate, 4),
            'is_retweet': bool(is_rt),
            'retweet_from': rt_from
        })

    return results


def get_top_tweets_all_users(
    usernames: List[str],
    limit_per_user: int = 5,
    sort_by: str = 'engagement',
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, List[Dict]]:
    """
    Birden fazla kullanici icin en iyi tweetleri getir
    """
    results = {}
    for username in usernames:
        tweets = get_top_tweets(
            username,
            limit=limit_per_user,
            sort_by=sort_by,
            start_date=start_date,
            end_date=end_date
        )
        if tweets:
            results[username] = tweets
    return results


# ============================================================================
# RAPORLAMA YARDIMCILARI
# ============================================================================

def get_engagement_ranking(usernames: List[str], start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
    """
    Kullanicilari toplam etkilesime gore sirala

    Returns:
        Sirali liste (en yuksekten dusuge)
    """
    stats = []
    for username in usernames:
        user_stats = get_user_engagement_stats(username, start_date, end_date)
        stats.append(user_stats)

    # Toplam engagement'a gore sirala
    stats.sort(key=lambda x: x['total_engagement'], reverse=True)

    # Rank ekle
    for i, s in enumerate(stats, 1):
        s['rank'] = i

    return stats


def print_engagement_report(usernames: List[str], start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Etkilesim raporu yazdir"""
    ranking = get_engagement_ranking(usernames, start_date, end_date)

    print(f"\n{'='*100}")
    print("ETKILESIM RAPORU")
    if start_date or end_date:
        print(f"Donem: {start_date or 'Baslangic'} - {end_date or 'Simdi'}")
    print(f"{'='*100}")
    print(f"{'#':<3} {'Kullanici':<20} {'Tweet':<8} {'Like':<10} {'Reply':<8} {'RT':<8} {'View':<12} {'Engagement':<12} {'Ort/Tweet':<10}")
    print(f"{'-'*100}")

    for r in ranking:
        print(f"{r['rank']:<3} @{r['username']:<19} {r['tweet_count']:<8} {r['total_likes']:<10,} "
              f"{r['total_replies']:<8,} {r['total_retweets']:<8,} {r['total_views']:<12,} "
              f"{r['total_engagement']:<12,} {r['avg_engagement_per_tweet']:<10.1f}")

    print(f"{'='*100}\n")


def print_top_tweets_report(username: str, limit: int = 5):
    """En iyi tweetler raporu"""
    tweets = get_top_tweets(username, limit=limit)

    print(f"\n{'='*80}")
    print(f"@{username} - EN YUKSEK ETKILESIMLI TWEETLER")
    print(f"{'='*80}")

    for i, t in enumerate(tweets, 1):
        print(f"\n{i}. [{t['date']}]")
        print(f"   {t['text']}")
        print(f"   Like: {t['likes']:,} | Reply: {t['replies']:,} | RT: {t['retweets']:,} | View: {t['views']:,}")
        print(f"   Toplam Engagement: {t['engagement']:,} | Rate: {t['engagement_rate']:.2f}%")

    print(f"\n{'='*80}\n")


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Tweet Metrik Hesaplama")
    parser.add_argument("--users", nargs="+", help="Kullanici adlari")
    parser.add_argument("--ranking", action="store_true", help="Etkilesim siralamasi")
    parser.add_argument("--top", type=int, default=5, help="En iyi N tweet")
    parser.add_argument("--start", help="Baslangic tarihi (YYYY-MM-DD)")
    parser.add_argument("--end", help="Bitis tarihi (YYYY-MM-DD)")
    parser.add_argument("--compare", action="store_true", help="Haftalik karsilastirma")

    args = parser.parse_args()

    if args.users:
        if args.ranking:
            print_engagement_report(args.users, args.start, args.end)
        elif args.compare:
            for user in args.users:
                result = compare_last_weeks(user)
                print(f"\n@{user} Haftalik Degisim:")
                print(f"  Engagement: {result['changes']['engagement_change']:+,} ({result['changes']['engagement_change_pct']:+.1f}%)")
                print(f"  Tweet sayisi: {result['changes']['tweet_count_change']:+}")
        else:
            for user in args.users:
                print_top_tweets_report(user, args.top)
    else:
        print("Kullanim:")
        print("  python metrics.py --users user1 user2 --ranking")
        print("  python metrics.py --users user1 --top 10")
        print("  python metrics.py --users user1 user2 --compare")
        print("  python metrics.py --users user1 --start 2024-01-01 --end 2024-01-31")