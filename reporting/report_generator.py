#!/usr/bin/env python3
"""
Report Generator v1.0 - Tam Rapor Olusturma

8 Soru Raporu:
1. Ana konular nedir? (LLM)
2. Kac takipcisi var? (Profil)
3. Kac kisi takip ediyor? (Profil)
4. Takipci degisimi (Profil history)
5. Etkilesim degisimi (Metrics)
6. Parti/lider savunusu (LLM)
7. Muhalefet elestirisi (LLM)
8. En cok etkilesim alan tweetler (Metrics)
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (
    get_latest_profile,
    get_report_cache,
    save_report_cache,
    clear_report_cache
)
from scraping.profile_scraper import get_weekly_comparison
from reporting.metrics import (
    get_user_engagement_stats,
    get_top_tweets,
    compare_last_weeks
)


class ReportGenerator:
    """Tam rapor olusturucu"""

    def __init__(self, use_cache: bool = True, use_llm: bool = True):
        """
        Args:
            use_cache: Cache kullan (default True)
            use_llm: LLM analizi yap (default True, False = sadece metrikler)
        """
        self.use_cache = use_cache
        self.use_llm = use_llm
        self.analyzer = None

        if use_llm:
            try:
                from analysis.analyzer import TweetAnalyzer
                self.analyzer = TweetAnalyzer()
            except Exception as e:
                print(f"LLM baslatilamadi: {e}")
                self.use_llm = False

    def generate_report(self, username: str, force_refresh: bool = False) -> str:
        """
        Kullanici icin tam rapor olustur

        Args:
            username: Twitter kullanici adi
            force_refresh: Cache'i yoksay ve yeniden olustur

        Returns:
            Markdown formatinda rapor
        """
        # Cache kontrol
        if self.use_cache and not force_refresh:
            cached = get_report_cache(username, 'full')
            if cached:
                print(f"  Cache'den yuklendi (olusturulma: {cached['created_at']})")
                return cached['content']

        print(f"\n{'='*60}")
        print(f"RAPOR OLUSTURULUYOR: @{username}")
        print(f"{'='*60}")

        report_parts = []
        report_parts.append(self._generate_header(username))

        # Soru 2-3: Profil bilgileri
        print("  [1/6] Profil bilgileri...")
        report_parts.append(self._generate_profile_section(username))

        # Soru 4: Takipci degisimi
        print("  [2/6] Takipci degisimi...")
        report_parts.append(self._generate_follower_change_section(username))

        # Soru 5: Etkilesim degisimi
        print("  [3/6] Etkilesim metrikleri...")
        report_parts.append(self._generate_engagement_section(username))

        # Soru 8: En iyi tweetler
        print("  [4/6] En iyi tweetler...")
        report_parts.append(self._generate_top_tweets_section(username))

        # LLM Analizi (Soru 1, 6, 7)
        if self.use_llm and self.analyzer:
            print("  [5/6] LLM analizi (bu biraz zaman alabilir)...")
            report_parts.append(self._generate_llm_analysis_section(username))
        else:
            report_parts.append("\n## LLM Analizi\n*LLM analizi devre disi*\n")

        # Footer
        print("  [6/6] Rapor tamamlaniyor...")
        report_parts.append(self._generate_footer())

        # Birlestir
        report = "\n".join(report_parts)

        # Cache'e kaydet
        if self.use_cache:
            save_report_cache(username, 'full', report)
            print("  Rapor cache'e kaydedildi")

        print(f"{'='*60}")
        print(f"RAPOR TAMAMLANDI")
        print(f"{'='*60}\n")

        return report

    def _generate_header(self, username: str) -> str:
        """Rapor basligi"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"""# Twitter Analiz Raporu: @{username}

**Olusturulma Tarihi:** {now}

---
"""

    def _generate_profile_section(self, username: str) -> str:
        """Soru 2-3: Profil bilgileri"""
        profile = get_latest_profile(username)

        if not profile:
            return """## Profil Bilgileri

*Profil verisi bulunamadi*
"""

        return f"""## Profil Bilgileri

| Metrik | Deger |
|--------|-------|
| Takipci | **{profile['followers']:,}** |
| Takip | **{profile['following']:,}** |
| Tweet | **{profile['tweets']:,}** |
| Son Guncelleme | {profile['date']} |
"""

    def _generate_follower_change_section(self, username: str) -> str:
        """Soru 4: Takipci degisimi"""
        comparison = get_weekly_comparison(username)

        if not comparison:
            return """## Takipci Degisimi

*Karsilastirma icin yeterli veri yok*
"""

        followers_change = comparison['followers_change']
        change_emoji = "📈" if followers_change > 0 else "📉" if followers_change < 0 else "➡️"
        change_str = f"+{followers_change:,}" if followers_change >= 0 else f"{followers_change:,}"

        return f"""## Takipci Degisimi (Haftalik)

| Metrik | Baslangic | Son | Degisim |
|--------|-----------|-----|---------|
| Takipci | {comparison['followers_start']:,} | {comparison['followers_end']:,} | {change_emoji} **{change_str}** |
| Takip | - | - | {comparison['following_change']:+,} |
| Tweet | - | - | {comparison['tweets_change']:+,} |

**Donem:** {comparison['period_start']} - {comparison['period_end']}
"""

    def _generate_engagement_section(self, username: str) -> str:
        """Soru 5: Etkilesim metrikleri"""
        stats = get_user_engagement_stats(username)
        weekly = compare_last_weeks(username, weeks=1)

        if stats['tweet_count'] == 0:
            return """## Etkilesim Metrikleri

*Tweet verisi bulunamadi*
"""

        # Haftalik degisim
        change_section = ""
        if weekly and weekly['period1']['total_engagement'] > 0:
            change_pct = weekly['changes']['engagement_change_pct']
            change_emoji = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
            change_section = f"\n**Haftalik Degisim:** {change_emoji} {change_pct:+.1f}%"

        return f"""## Etkilesim Metrikleri

| Metrik | Toplam | Tweet Basina |
|--------|--------|--------------|
| Like | {stats['total_likes']:,} | {stats['total_likes'] / max(stats['tweet_count'], 1):.1f} |
| Reply | {stats['total_replies']:,} | {stats['total_replies'] / max(stats['tweet_count'], 1):.1f} |
| Retweet | {stats['total_retweets']:,} | {stats['total_retweets'] / max(stats['tweet_count'], 1):.1f} |
| View | {stats['total_views']:,} | {stats['total_views'] / max(stats['tweet_count'], 1):.0f} |

**Toplam Tweet:** {stats['tweet_count']}
**Toplam Engagement:** {stats['total_engagement']:,}
**Ort. Engagement/Tweet:** {stats['avg_engagement_per_tweet']:.1f}
**Engagement Rate:** {stats['avg_engagement_rate']:.2f}%{change_section}
"""

    def _generate_top_tweets_section(self, username: str, limit: int = 5) -> str:
        """Soru 8: En iyi tweetler"""
        tweets = get_top_tweets(username, limit=limit)

        if not tweets:
            return """## En Cok Etkilesim Alan Tweetler

*Tweet bulunamadi*
"""

        lines = ["## En Cok Etkilesim Alan Tweetler\n"]

        for i, t in enumerate(tweets, 1):
            text = t['text'][:150] + "..." if len(t['text']) > 150 else t['text']
            lines.append(f"""### {i}. Tweet
> {text}

- **Tarih:** {t['date'] or 'Bilinmiyor'}
- **Like:** {t['likes']:,} | **Reply:** {t['replies']:,} | **RT:** {t['retweets']:,}
- **Toplam Engagement:** {t['engagement']:,}
""")

        return "\n".join(lines)

    def _generate_llm_analysis_section(self, username: str) -> str:
        """Soru 1, 6, 7: LLM analizi"""
        if not self.analyzer:
            return "\n## LLM Analizi\n*LLM kullanilabilir degil*\n"

        # Tweetleri al
        import sqlite3
        from config import DB_PATH

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tweet_text, tweet_date
            FROM tweets
            WHERE username = ? AND is_retweet = 0
            ORDER BY tweet_date DESC
            LIMIT 30
        """, (username,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return "\n## LLM Analizi\n*Analiz icin tweet bulunamadi*\n"

        tweets = [{'text': row[0], 'date': row[1]} for row in rows]

        # Tam analiz yap
        try:
            result = self.analyzer.analyze_full(tweets, username)
            return f"\n## LLM Analizi\n\n{result['raw_response']}\n"
        except Exception as e:
            return f"\n## LLM Analizi\n*Analiz hatasi: {e}*\n"

    def _generate_footer(self) -> str:
        """Rapor footer"""
        return f"""
---

*Bu rapor Meclis Istihbarat Sistemi tarafindan otomatik olusturulmustur.*
*Rapor suresi: 1 hafta gecerlidir.*
"""


# ============================================================================
# YARDIMCI FONKSIYONLAR
# ============================================================================

def generate_report(username: str, use_cache: bool = True, use_llm: bool = True) -> str:
    """Kisa yol: Rapor olustur"""
    generator = ReportGenerator(use_cache=use_cache, use_llm=use_llm)
    return generator.generate_report(username)


def generate_reports_batch(usernames: List[str], use_llm: bool = True) -> Dict[str, str]:
    """Birden fazla kullanici icin rapor olustur"""
    generator = ReportGenerator(use_cache=True, use_llm=use_llm)
    reports = {}

    for i, username in enumerate(usernames, 1):
        print(f"\n[{i}/{len(usernames)}] @{username}")
        try:
            reports[username] = generator.generate_report(username)
        except Exception as e:
            print(f"  Hata: {e}")
            reports[username] = f"# Hata\n\nRapor olusturulamadi: {e}"

    return reports


def generate_quick_report(username: str) -> str:
    """LLM olmadan hizli rapor"""
    generator = ReportGenerator(use_cache=True, use_llm=False)
    return generator.generate_report(username)


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Rapor Olusturma")
    parser.add_argument("--user", help="Kullanici adi")
    parser.add_argument("--users", nargs="+", help="Birden fazla kullanici")
    parser.add_argument("--no-cache", action="store_true", help="Cache kullanma")
    parser.add_argument("--no-llm", action="store_true", help="LLM kullanma (hizli mod)")
    parser.add_argument("--clear-cache", action="store_true", help="Cache temizle")
    parser.add_argument("--output", help="Cikti dosyasi (.md)")

    args = parser.parse_args()

    if args.clear_cache:
        from database import clear_report_cache
        deleted = clear_report_cache()
        print(f"Cache temizlendi: {deleted} kayit silindi")

    elif args.user:
        report = generate_report(
            args.user,
            use_cache=not args.no_cache,
            use_llm=not args.no_llm
        )

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"Rapor kaydedildi: {args.output}")
        else:
            print(report)

    elif args.users:
        reports = generate_reports_batch(args.users, use_llm=not args.no_llm)
        for username, report in reports.items():
            if args.output:
                filename = f"{args.output}_{username}.md"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                print(f"Kaydedildi: {filename}")
            else:
                print(report)
                print("\n" + "="*80 + "\n")

    else:
        print("Kullanim:")
        print("  python report_generator.py --user username")
        print("  python report_generator.py --user username --no-llm")
        print("  python report_generator.py --user username --output rapor.md")
        print("  python report_generator.py --users user1 user2 user3")
        print("  python report_generator.py --clear-cache")