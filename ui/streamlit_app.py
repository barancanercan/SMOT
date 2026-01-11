#!/usr/bin/env python3
"""
Streamlit Web UI - Meclis Istihbarat Sistemi

Sade ve kullanici dostu arayuz
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import sqlite3
from datetime import datetime

from config import DB_PATH
from database import get_stats, get_latest_profile, init_database
from reporting import generate_report, generate_quick_report, get_top_tweets, get_user_engagement_stats

# ============================================================================
# SAYFA AYARLARI
# ============================================================================

st.set_page_config(
    page_title="Meclis Istihbarat Sistemi",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Minimal CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .tweet-card {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .stSelectbox > div > div {
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# YARDIMCI FONKSIYONLAR
# ============================================================================

@st.cache_data(ttl=300)
def get_all_users():
    """Tum kullanicilari getir"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT username FROM tweets
        ORDER BY username
    """)
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users


@st.cache_data(ttl=300)
def get_db_stats():
    """Veritabani istatistikleri"""
    try:
        return get_stats()
    except:
        return None


@st.cache_data(ttl=60)
def get_user_stats(username):
    """Kullanici istatistikleri"""
    return get_user_engagement_stats(username)


@st.cache_data(ttl=60)
def get_user_top_tweets(username, limit=5):
    """Kullanicinin en iyi tweetleri"""
    return get_top_tweets(username, limit=limit)


def generate_user_report_cached(username, use_llm=False):
    """Rapor olustur (cache'li)"""
    if use_llm:
        return generate_report(username, use_cache=True, use_llm=True)
    return generate_quick_report(username)


# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("## 🏛️ Meclis Istihbarat")
    st.markdown("---")

    # Sayfa secimi
    page = st.radio(
        "Sayfa",
        ["📊 Dashboard", "📋 Rapor Olustur", "🔥 En Iyi Tweetler", "⚙️ Sistem"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Hizli istatistikler
    stats = get_db_stats()
    if stats:
        st.metric("Toplam Tweet", f"{stats['total_tweets']:,}")
        st.metric("Kullanici", stats['active_users'])


# ============================================================================
# DASHBOARD SAYFASI
# ============================================================================

if page == "📊 Dashboard":
    st.markdown("# 📊 Dashboard")

    # Kullanici secimi
    users = get_all_users()
    selected_user = st.selectbox("Kullanici Sec", [""] + users, index=0)

    if selected_user:
        # Kullanici metrikleri
        user_stats = get_user_stats(selected_user)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Tweet Sayisi", user_stats['tweet_count'])
        with col2:
            st.metric("Toplam Like", f"{user_stats['total_likes']:,}")
        with col3:
            st.metric("Toplam RT", f"{user_stats['total_retweets']:,}")
        with col4:
            st.metric("Engagement Rate", f"{user_stats['avg_engagement_rate']:.2f}%")

        st.markdown("---")

        # En iyi tweetler
        st.markdown("### En Iyi 5 Tweet")
        top_tweets = get_user_top_tweets(selected_user, 5)

        for i, tweet in enumerate(top_tweets, 1):
            with st.container():
                st.markdown(f"**{i}.** {tweet['text'][:200]}...")
                cols = st.columns(4)
                cols[0].caption(f"❤️ {tweet['likes']:,}")
                cols[1].caption(f"💬 {tweet['replies']:,}")
                cols[2].caption(f"🔄 {tweet['retweets']:,}")
                cols[3].caption(f"📊 {tweet['engagement']:,}")
                st.markdown("---")
    else:
        # Genel istatistikler
        stats = get_db_stats()
        if stats:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Toplam Tweet", f"{stats['total_tweets']:,}")
            with col2:
                st.metric("Orijinal Tweet", f"{stats['total_original']:,}")
            with col3:
                st.metric("Retweet", f"{stats['total_retweets']:,}")

            col4, col5, col6 = st.columns(3)
            with col4:
                st.metric("Toplam Like", f"{stats['total_likes']:,}")
            with col5:
                st.metric("Toplam View", f"{stats['total_views']:,}")
            with col6:
                st.metric("Aktif Kullanici", stats['active_users'])


# ============================================================================
# RAPOR SAYFASI
# ============================================================================

elif page == "📋 Rapor Olustur":
    st.markdown("# 📋 Rapor Olustur")

    users = get_all_users()

    # Tek kullanici raporu
    st.markdown("### Tek Kullanici Raporu")

    col1, col2 = st.columns([3, 1])
    with col1:
        selected_user = st.selectbox("Kullanici", [""] + users, key="single_user")
    with col2:
        use_llm = st.checkbox("LLM Analizi", value=False, help="Detayli icerik analizi (yavas)")

    if st.button("Rapor Olustur", type="primary", disabled=not selected_user):
        with st.spinner(f"@{selected_user} icin rapor hazirlaniyor..."):
            report = generate_user_report_cached(selected_user, use_llm)
            st.markdown(report)

            # Indirme butonu
            st.download_button(
                "📥 Markdown Indir",
                report,
                file_name=f"rapor_{selected_user}_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )

    st.markdown("---")

    # Coklu kullanici raporu
    st.markdown("### Toplu Rapor")

    selected_users = st.multiselect("Kullanicilari Sec", users, key="multi_users")

    col1, col2 = st.columns([1, 1])
    with col1:
        multi_llm = st.checkbox("LLM Analizi", value=False, key="multi_llm")

    if st.button("Toplu Rapor Olustur", disabled=len(selected_users) == 0):
        all_reports = []
        progress = st.progress(0)

        for i, username in enumerate(selected_users):
            with st.spinner(f"@{username} ({i+1}/{len(selected_users)})"):
                report = generate_user_report_cached(username, multi_llm)
                all_reports.append(f"\n\n---\n\n{report}")
                progress.progress((i + 1) / len(selected_users))

        combined = f"# Toplu Rapor ({len(selected_users)} Kullanici)\n\n" + "\n".join(all_reports)
        st.markdown(combined)

        st.download_button(
            "📥 Toplu Rapor Indir",
            combined,
            file_name=f"toplu_rapor_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown"
        )


# ============================================================================
# EN IYI TWEETLER SAYFASI
# ============================================================================

elif page == "🔥 En Iyi Tweetler":
    st.markdown("# 🔥 En Iyi Tweetler")

    users = get_all_users()

    col1, col2 = st.columns([3, 1])
    with col1:
        selected_user = st.selectbox("Kullanici", [""] + users, key="top_user")
    with col2:
        limit = st.slider("Tweet Sayisi", 5, 20, 10)

    if selected_user:
        tweets = get_user_top_tweets(selected_user, limit)

        if tweets:
            for i, tweet in enumerate(tweets, 1):
                with st.expander(f"**#{i}** - Engagement: {tweet['engagement']:,}", expanded=(i <= 3)):
                    st.markdown(f"> {tweet['text']}")
                    st.caption(f"📅 {tweet['date'] or 'Tarih yok'}")

                    cols = st.columns(4)
                    cols[0].metric("Like", f"{tweet['likes']:,}")
                    cols[1].metric("Reply", f"{tweet['replies']:,}")
                    cols[2].metric("Retweet", f"{tweet['retweets']:,}")
                    cols[3].metric("View", f"{tweet['views']:,}")
        else:
            st.info("Bu kullanici icin tweet bulunamadi.")


# ============================================================================
# SISTEM SAYFASI
# ============================================================================

elif page == "⚙️ Sistem":
    st.markdown("# ⚙️ Sistem Durumu")

    stats = get_db_stats()

    if stats:
        st.markdown("### Veritabani")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Tweet Istatistikleri**")
            st.write(f"- Toplam Tweet: **{stats['total_tweets']:,}**")
            st.write(f"- Orijinal Tweet: **{stats['total_original']:,}**")
            st.write(f"- Retweet: **{stats['total_retweets']:,}**")

        with col2:
            st.markdown("**Etkilesim**")
            st.write(f"- Toplam Like: **{stats['total_likes']:,}**")
            st.write(f"- Toplam View: **{stats['total_views']:,}**")
            st.write(f"- Aktif Kullanici: **{stats['active_users']}**")

    st.markdown("---")

    st.markdown("### Hakkinda")
    st.markdown("""
    **Meclis Istihbarat Sistemi v2.0**

    Ankara Buyuksehir Belediyesi meclis uyelerinin Twitter/X aktivitelerini
    analiz eden ve raporlayan sistem.

    **Ozellikler:**
    - Tweet toplama (son 3 ay)
    - Engagement analizi
    - LLM destekli icerik analizi
    - Toplu raporlama
    """)


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption("Meclis Istihbarat Sistemi v2.0 | Streamlit UI")
