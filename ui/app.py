#!/usr/bin/env python3
"""
Gradio Web UI v1.0 - Meclis Istihbarat Sistemi

Ozellikler:
- Uye secimi
- Tarih filtresi
- Rapor gosterimi
- Hizli mod (LLM olmadan)
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gradio as gr
from config import DB_PATH
from database import get_stats, get_latest_profile, init_database
from reporting import generate_report, generate_quick_report, get_top_tweets, get_user_engagement_stats
from scraping.profile_scraper import get_weekly_comparison


# ============================================================================
# VERI FONKSIYONLARI
# ============================================================================

def get_all_users():
    """Veritabanindaki tum kullanicilari getir (councilors + tweets)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Hem councilors hem tweets tablosundan kullanicilari al
    cursor.execute("""
        SELECT username FROM councilors
        UNION
        SELECT DISTINCT username FROM tweets
        ORDER BY username
    """)
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users


def get_user_summary(username: str) -> str:
    """Kullanici ozet bilgisi"""
    if not username:
        return "Kullanici secin"

    profile = get_latest_profile(username)
    stats = get_user_engagement_stats(username)

    summary = f"## @{username}\n\n"

    if profile:
        summary += f"**Takipci:** {profile['followers']:,} | "
        summary += f"**Takip:** {profile['following']:,} | "
        summary += f"**Tweet:** {profile['tweets']:,}\n\n"

    if stats['tweet_count'] > 0:
        summary += f"**DB'deki Tweet:** {stats['tweet_count']} | "
        summary += f"**Toplam Engagement:** {stats['total_engagement']:,}\n"

    return summary


def generate_user_report(username: str, use_llm: bool, progress=gr.Progress()) -> str:
    """Kullanici raporu olustur"""
    if not username:
        return "Lutfen bir kullanici secin"

    progress(0.1, desc="Rapor hazirlaniyor...")

    try:
        if use_llm:
            progress(0.3, desc="LLM analizi yapiliyor (bu biraz zaman alabilir)...")
            report = generate_report(username, use_cache=True, use_llm=True)
        else:
            progress(0.3, desc="Hizli rapor olusturuluyor...")
            report = generate_quick_report(username)

        progress(1.0, desc="Tamamlandi!")
        return report

    except Exception as e:
        return f"# Hata\n\nRapor olusturulamadi: {str(e)}"


def get_top_tweets_display(username: str, limit: int = 5) -> str:
    """En iyi tweetleri goster"""
    if not username:
        return "Kullanici secin"

    tweets = get_top_tweets(username, limit=limit)

    if not tweets:
        return "Tweet bulunamadi"

    result = f"## @{username} - En Iyi {limit} Tweet\n\n"

    for i, t in enumerate(tweets, 1):
        text = t['text'][:200] + "..." if len(t['text']) > 200 else t['text']
        result += f"### {i}. (Engagement: {t['engagement']:,})\n"
        result += f"> {text}\n\n"
        result += f"Like: {t['likes']:,} | Reply: {t['replies']:,} | RT: {t['retweets']:,}\n\n"
        result += "---\n\n"

    return result


def get_comparison_display(username: str) -> str:
    """Haftalik karsilastirma goster"""
    if not username:
        return "Kullanici secin"

    comparison = get_weekly_comparison(username)

    if not comparison:
        return "Karsilastirma icin yeterli veri yok"

    followers_change = comparison['followers_change']
    emoji = "📈" if followers_change > 0 else "📉" if followers_change < 0 else "➡️"

    result = f"## @{username} - Haftalik Degisim\n\n"
    result += f"**Donem:** {comparison['period_start']} - {comparison['period_end']}\n\n"
    result += f"| Metrik | Degisim |\n"
    result += f"|--------|--------|\n"
    result += f"| Takipci | {emoji} **{followers_change:+,}** |\n"
    result += f"| Takip | {comparison['following_change']:+,} |\n"
    result += f"| Tweet | {comparison['tweets_change']:+,} |\n"

    return result


def get_db_stats() -> str:
    """Veritabani istatistikleri"""
    try:
        stats = get_stats()
        return f"""## Veritabani Durumu

| Metrik | Deger |
|--------|-------|
| Toplam Kullanici | {stats['active_users']} |
| Toplam Tweet | {stats['total_tweets']:,} |
| Orijinal Tweet | {stats['total_original']:,} |
| Retweet | {stats['total_retweets']:,} |
| Toplam Like | {stats['total_likes']:,} |
| Toplam View | {stats['total_views']:,} |
"""
    except Exception as e:
        return f"Istatistik alinamadi: {e}"


def generate_multi_user_report(selected_users: list, use_llm: bool, progress=gr.Progress()) -> str:
    """Birden fazla kullanici icin rapor olustur"""
    if not selected_users:
        return "Lutfen en az bir kullanici secin"

    reports = []
    total = len(selected_users)

    for i, username in enumerate(selected_users):
        progress((i + 0.5) / total, desc=f"@{username} raporu olusturuluyor...")

        try:
            if use_llm:
                report = generate_report(username, use_cache=True, use_llm=True)
            else:
                report = generate_quick_report(username)

            reports.append(f"---\n\n{report}")
        except Exception as e:
            reports.append(f"---\n\n# @{username}\n\nHata: {str(e)}")

    progress(1.0, desc="Tamamlandi!")

    header = f"# Toplu Rapor ({len(selected_users)} Kullanici)\n\n"
    header += f"**Secilen Kullanicilar:** {', '.join(['@' + u for u in selected_users])}\n\n"

    return header + "\n\n".join(reports)


# ============================================================================
# GRADIO ARAYUZU
# ============================================================================

def create_ui():
    """Gradio arayuzunu olustur"""

    # Kullanicilari al
    users = get_all_users()
    if not users:
        users = ["(Kullanici bulunamadi)"]

    with gr.Blocks(
        title="Meclis Istihbarat Sistemi",
        theme=gr.themes.Soft(),
        css="""
        .report-output { font-family: monospace; }
        .header { text-align: center; margin-bottom: 20px; }
        """
    ) as app:

        # Header
        gr.Markdown("""
        # 🏛️ Meclis Istihbarat Sistemi
        Twitter/X aktivite analizi ve raporlama
        """)

        with gr.Tabs():
            # ============================================================
            # TAB 1: RAPOR OLUSTUR
            # ============================================================
            with gr.Tab("📊 Rapor Olustur"):
                with gr.Row():
                    with gr.Column(scale=1):
                        user_dropdown = gr.Dropdown(
                            choices=users,
                            label="Kullanici Sec",
                            info="Analiz edilecek Twitter kullanicisi"
                        )

                        use_llm_checkbox = gr.Checkbox(
                            label="LLM Analizi Kullan",
                            value=False,
                            info="Isaretli: Detayli analiz (~2-3 dk) | Isaretli degil: Hizli rapor (~5 sn)"
                        )

                        generate_btn = gr.Button("Rapor Olustur", variant="primary")

                        user_summary = gr.Markdown("Kullanici secin")

                    with gr.Column(scale=2):
                        report_output = gr.Markdown(
                            label="Rapor",
                            value="Rapor burada gorunecek...",
                            elem_classes=["report-output"]
                        )

                # Events
                user_dropdown.change(
                    fn=get_user_summary,
                    inputs=[user_dropdown],
                    outputs=[user_summary]
                )

                generate_btn.click(
                    fn=generate_user_report,
                    inputs=[user_dropdown, use_llm_checkbox],
                    outputs=[report_output]
                )

            # ============================================================
            # TAB 2: TOPLU RAPOR (Coklu Kullanici)
            # ============================================================
            with gr.Tab("📋 Toplu Rapor"):
                with gr.Row():
                    with gr.Column(scale=1):
                        multi_user_checkbox = gr.CheckboxGroup(
                            choices=users,
                            label="Kullanicilari Sec",
                            info="Rapor olusturulacak kullanicilari isaretleyin"
                        )

                        multi_use_llm = gr.Checkbox(
                            label="LLM Analizi Kullan",
                            value=False,
                            info="Isaretli: Detayli analiz | Isaretli degil: Hizli rapor"
                        )

                        with gr.Row():
                            select_all_btn = gr.Button("Tumunu Sec", variant="secondary", size="sm")
                            clear_all_btn = gr.Button("Temizle", variant="secondary", size="sm")

                        multi_generate_btn = gr.Button("Toplu Rapor Olustur", variant="primary")

                    with gr.Column(scale=2):
                        multi_report_output = gr.Markdown(
                            label="Toplu Rapor",
                            value="Kullanicilari secin ve 'Toplu Rapor Olustur' tiklayin...",
                            elem_classes=["report-output"]
                        )

                # Events
                select_all_btn.click(
                    fn=lambda: users,
                    outputs=[multi_user_checkbox]
                )

                clear_all_btn.click(
                    fn=lambda: [],
                    outputs=[multi_user_checkbox]
                )

                multi_generate_btn.click(
                    fn=generate_multi_user_report,
                    inputs=[multi_user_checkbox, multi_use_llm],
                    outputs=[multi_report_output]
                )

            # ============================================================
            # TAB 3: EN IYI TWEETLER
            # ============================================================
            with gr.Tab("🔥 En Iyi Tweetler"):
                with gr.Row():
                    with gr.Column(scale=1):
                        top_user_dropdown = gr.Dropdown(
                            choices=users,
                            label="Kullanici Sec"
                        )

                        top_limit_slider = gr.Slider(
                            minimum=3,
                            maximum=20,
                            value=5,
                            step=1,
                            label="Tweet Sayisi"
                        )

                        top_btn = gr.Button("Goster", variant="primary")

                    with gr.Column(scale=2):
                        top_output = gr.Markdown("Kullanici secin ve 'Goster' tiklayin")

                top_btn.click(
                    fn=get_top_tweets_display,
                    inputs=[top_user_dropdown, top_limit_slider],
                    outputs=[top_output]
                )

            # ============================================================
            # TAB 3: HAFTALIK DEGISIM
            # ============================================================
            with gr.Tab("📈 Haftalik Degisim"):
                with gr.Row():
                    with gr.Column(scale=1):
                        compare_user_dropdown = gr.Dropdown(
                            choices=users,
                            label="Kullanici Sec"
                        )

                        compare_btn = gr.Button("Karsilastir", variant="primary")

                    with gr.Column(scale=2):
                        compare_output = gr.Markdown("Kullanici secin")

                compare_btn.click(
                    fn=get_comparison_display,
                    inputs=[compare_user_dropdown],
                    outputs=[compare_output]
                )

            # ============================================================
            # TAB 4: SISTEM DURUMU
            # ============================================================
            with gr.Tab("⚙️ Sistem"):
                with gr.Row():
                    refresh_stats_btn = gr.Button("Yenile", variant="secondary")

                stats_output = gr.Markdown(get_db_stats())

                refresh_stats_btn.click(
                    fn=get_db_stats,
                    outputs=[stats_output]
                )

                gr.Markdown("""
                ---
                ### Kullanim Kilavuzu

                1. **Rapor Olustur:** Kullanici secip rapor olusturun
                   - LLM Analizi: Detayli icerik analizi (yavas ama kapsamli)
                   - Hizli Mod: Sadece metrikler (hizli)

                2. **En Iyi Tweetler:** En cok etkilesim alan tweetleri gorun

                3. **Haftalik Degisim:** Takipci/takip degisimlerini izleyin

                ---
                *Meclis Istihbarat Sistemi v2.0*
                """)

        return app


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Uygulamayi baslat"""
    print("Veritabani kontrol ediliyor...")
    init_database()

    print("Gradio arayuzu baslatiliyor...")
    app = create_ui()

    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        inbrowser=True
    )


if __name__ == "__main__":
    main()