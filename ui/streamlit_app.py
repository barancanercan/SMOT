#!/usr/bin/env python3
"""
Streamlit Web UI - Meclis Istihbarat Sistemi

Sade ve kullanici dostu arayuz + Dashboard Grafikleri
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import sqlite3
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from config import DB_PATH
from database import get_stats, get_latest_profile, init_database
from reporting import generate_report, generate_quick_report, get_top_tweets, get_user_engagement_stats, export_to_excel, export_engagement_excel

# ============================================================================
# SAYFA AYARLARI
# ============================================================================

st.set_page_config(
    page_title="Meclis Istihbarat Sistemi",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Beyaz Tema CSS
st.markdown("""
<style>
    /* Ana arka plan beyaz */
    .stApp {
        background-color: #ffffff;
    }

    /* Sidebar beyaz */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }

    /* Metrikler */
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }

    /* Tweet kartları */
    .tweet-card {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }

    /* Selectbox beyaz */
    .stSelectbox > div > div {
        background-color: white;
    }

    /* Expander içerikleri */
    .streamlit-expanderContent {
        background-color: #fafafa;
        border-radius: 8px;
        padding: 1rem;
    }

    /* Multiselect */
    .stMultiSelect > div {
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# YARDIMCI FONKSIYONLAR
# ============================================================================

def normalize_party(party: str) -> str:
    """Parti isimlerini normalize et (CHP = Cumhuriyet Halk Partisi, etc.)"""
    if not party:
        return "BAGIMSIZ"

    party_upper = str(party).upper().strip()

    # CHP eşleştirmesi
    if party_upper in ['CHP', 'CUMHURIYET HALK PARTISI', 'CUMHURIYET HALK PARTİSİ'] or 'CUMHURIYET' in party_upper:
        return 'CHP'

    # AKP eşleştirmesi
    if party_upper in ['AKP', 'AK PARTI', 'ADALET VE KALKINMA PARTISI', 'ADALET VE KALKINMA PARTİSİ'] or 'ADALET' in party_upper or 'KALKINMA' in party_upper:
        return 'AKP'

    # MHP eşleştirmesi
    if party_upper in ['MHP', 'MILLIYETCI HAREKET PARTISI', 'MİLLİYETÇİ HAREKET PARTİSİ'] or 'MILLIYETCI' in party_upper or 'MİLLİYETÇİ' in party_upper:
        return 'MHP'

    # BBP eşleştirmesi
    if party_upper in ['BBP', 'BUYUK BIRLIK PARTISI', 'BÜYÜK BİRLİK PARTİSİ', 'BÜYÜK BIRLIK'] or 'BUYUK BIRLIK' in party_upper or 'BÜYÜK BİRLİK' in party_upper:
        return 'BBP'

    # YRP eşleştirmesi
    if party_upper in ['YRP', 'YENIDEN REFAH PARTISI', 'YENİDEN REFAH PARTİSİ'] or 'REFAH' in party_upper:
        return 'YRP'

    # Bağımsız
    if party_upper in ['BAGIMSIZ', 'BAĞIMSIZ', 'INDEPENDENT']:
        return 'BAGIMSIZ'

    return party_upper


@st.cache_data(ttl=300)
def get_all_users():
    """Tum kullanicilari getir (councilors tablosundan)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT username FROM councilors
        ORDER BY username
    """)
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users


@st.cache_data(ttl=300)
def get_all_councilors():
    """Tum meclis uyelerini detayli getir"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.username, c.name, c.party, c.district,
               COALESCE(ph.followers_count, 0) as followers
        FROM councilors c
        LEFT JOIN profile_history ph ON c.username = ph.username
        ORDER BY c.name
    """)
    rows = cursor.fetchall()
    conn.close()
    return [{'username': r[0], 'name': r[1], 'party': r[2], 'district': r[3], 'followers': r[4]} for r in rows]


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


@st.cache_data(ttl=300)
def get_followers_data():
    """Takipci verilerini getir (profile_history'den)"""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT
            ph.username,
            c.name,
            c.party,
            c.district,
            ph.followers_count
        FROM profile_history ph
        JOIN councilors c ON ph.username = c.username
        WHERE ph.scrape_date = (
            SELECT MAX(scrape_date) FROM profile_history WHERE username = ph.username
        )
        ORDER BY ph.followers_count DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=300)
def get_party_stats():
    """Parti bazli istatistikler"""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT
            c.party,
            COUNT(DISTINCT c.username) as member_count,
            COALESCE(SUM(ph.followers_count), 0) as total_followers
        FROM councilors c
        LEFT JOIN profile_history ph ON c.username = ph.username
        GROUP BY c.party
        ORDER BY total_followers DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=300)
def get_engagement_by_user():
    """Kullanici bazli engagement verileri"""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT
            t.username,
            c.name,
            c.party,
            COUNT(*) as tweet_count,
            COALESCE(SUM(t.likes), 0) as total_likes,
            COALESCE(SUM(t.retweets), 0) as total_retweets,
            COALESCE(SUM(t.views), 0) as total_views,
            COALESCE(SUM(t.likes + t.retweets + t.replies), 0) as total_engagement
        FROM tweets t
        JOIN councilors c ON t.username = c.username
        WHERE t.is_retweet = 0
        GROUP BY t.username
        ORDER BY total_engagement DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=300)
def get_district_stats():
    """Ilce bazli istatistikler"""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT
            c.district,
            COUNT(DISTINCT c.username) as member_count,
            COALESCE(SUM(ph.followers_count), 0) as total_followers
        FROM councilors c
        LEFT JOIN profile_history ph ON c.username = ph.username
        GROUP BY c.district
        HAVING member_count > 0
        ORDER BY total_followers DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("## 🏛️ Meclis Istihbarat")
    st.markdown("---")

    # Sayfa secimi
    page = st.radio(
        "Sayfa",
        ["📊 Dashboard", "📈 Grafikler", "📋 Rapor Olustur", "🔥 En Iyi Tweetler", "⚙️ Sistem"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Hizli istatistikler
    stats = get_db_stats()
    all_users = get_all_users()
    if stats:
        st.metric("Toplam Tweet", f"{stats['total_tweets']:,}")
        st.metric("Meclis Uyesi", len(all_users))


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
                st.markdown(f"**{i}.** {tweet['text']}")
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
# GRAFIKLER SAYFASI
# ============================================================================

elif page == "📈 Grafikler":
    st.markdown("# 📈 Analiz Grafikleri")

    # Tab yapisi
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Takipci Siralaması", "🏛️ Parti Analizi", "📊 Engagement", "🗺️ Ilce Analizi"])

    # ----- TAB 1: TAKIPCI SIRALAMASI -----
    with tab1:
        st.markdown("### En Cok Takipcisi Olan Meclis Uyeleri")

        followers_df = get_followers_data()

        if not followers_df.empty:
            # Top 20 bar chart
            top_20 = followers_df.head(20)

            fig = px.bar(
                top_20,
                x='followers_count',
                y='name',
                orientation='h',
                color='party',
                title='Top 20 - Takipci Sayisina Gore',
                labels={'followers_count': 'Takipci', 'name': 'Meclis Uyesi', 'party': 'Parti'},
                color_discrete_map={
                    'Cumhuriyet Halk Partisi': '#e31b23',
                    'Adalet Ve Kalkınma Partisi': '#ffa500',
                    'Milliyetçi Hareket Partisi': '#c8102e',
                    'Büyük Birlik Partisi': '#1e3a8a',
                    'Yeniden Refah Partisi': '#006400',
                    'Bağımsız': '#808080'
                }
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=600)
            st.plotly_chart(fig, use_container_width=True)

            # Tablo
            st.markdown("### Tam Liste")
            st.dataframe(
                followers_df[['name', 'party', 'district', 'followers_count']].rename(columns={
                    'name': 'Isim',
                    'party': 'Parti',
                    'district': 'Ilce',
                    'followers_count': 'Takipci'
                }),
                use_container_width=True,
                height=400
            )

            # Excel Export
            st.markdown("### Export")
            export_data = followers_df.to_dict('records')
            if st.button("📥 Excel Olarak Indir", key="export_followers"):
                filepath = export_to_excel(export_data, f"takipci_listesi_{datetime.now().strftime('%Y%m%d')}")
                if filepath:
                    with open(filepath, 'rb') as f:
                        st.download_button(
                            "💾 Excel Dosyasini Kaydet",
                            f.read(),
                            file_name=filepath.split('/')[-1],
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
        else:
            st.info("Takipci verisi bulunamadi. Profile scraper calistirilmali.")

    # ----- TAB 2: PARTI ANALIZI -----
    with tab2:
        st.markdown("### Parti Bazli Analiz")

        party_df = get_party_stats()

        if not party_df.empty and party_df['total_followers'].sum() > 0:
            col1, col2 = st.columns(2)

            with col1:
                # Parti uye sayisi pie chart
                fig1 = px.pie(
                    party_df,
                    values='member_count',
                    names='party',
                    title='Parti Bazli Uye Dagilimi',
                    color='party',
                    color_discrete_map={
                        'Cumhuriyet Halk Partisi': '#e31b23',
                        'Adalet Ve Kalkınma Partisi': '#ffa500',
                        'Milliyetçi Hareket Partisi': '#c8102e',
                        'Büyük Birlik Partisi': '#1e3a8a',
                        'Yeniden Refah Partisi': '#006400',
                        'Bağımsız': '#808080'
                    }
                )
                st.plotly_chart(fig1, use_container_width=True)

            with col2:
                # Parti toplam takipci bar chart
                fig2 = px.bar(
                    party_df,
                    x='party',
                    y='total_followers',
                    title='Parti Bazli Toplam Takipci',
                    labels={'party': 'Parti', 'total_followers': 'Toplam Takipci'},
                    color='party',
                    color_discrete_map={
                        'Cumhuriyet Halk Partisi': '#e31b23',
                        'Adalet Ve Kalkınma Partisi': '#ffa500',
                        'Milliyetçi Hareket Partisi': '#c8102e',
                        'Büyük Birlik Partisi': '#1e3a8a',
                        'Yeniden Refah Partisi': '#006400',
                        'Bağımsız': '#808080'
                    }
                )
                fig2.update_layout(showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)

            # Parti istatistikleri tablosu
            st.markdown("### Parti Istatistikleri")
            party_display = party_df.copy()
            party_display['avg_followers'] = (party_display['total_followers'] / party_display['member_count']).astype(int)
            st.dataframe(
                party_display.rename(columns={
                    'party': 'Parti',
                    'member_count': 'Uye Sayisi',
                    'total_followers': 'Toplam Takipci',
                    'avg_followers': 'Ortalama Takipci'
                }),
                use_container_width=True
            )
        else:
            st.info("Parti verisi bulunamadi.")

    # ----- TAB 3: ENGAGEMENT -----
    with tab3:
        st.markdown("### Engagement Analizi")

        engagement_df = get_engagement_by_user()

        if not engagement_df.empty:
            # Top 15 engagement bar chart
            top_15 = engagement_df.head(15)

            fig = px.bar(
                top_15,
                x='total_engagement',
                y='name',
                orientation='h',
                color='party',
                title='Top 15 - Toplam Engagement (Like + RT + Reply)',
                labels={'total_engagement': 'Engagement', 'name': 'Meclis Uyesi'},
                color_discrete_map={
                    'Cumhuriyet Halk Partisi': '#e31b23',
                    'Adalet Ve Kalkınma Partisi': '#ffa500',
                    'Milliyetçi Hareket Partisi': '#c8102e',
                    'Büyük Birlik Partisi': '#1e3a8a',
                    'Yeniden Refah Partisi': '#006400',
                    'Bağımsız': '#808080'
                }
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
            st.plotly_chart(fig, use_container_width=True)

            # Like vs Retweet scatter
            st.markdown("### Like vs Retweet Dagilimi")
            fig2 = px.scatter(
                engagement_df,
                x='total_likes',
                y='total_retweets',
                size='tweet_count',
                color='party',
                hover_name='name',
                title='Like vs Retweet (Boyut = Tweet Sayisi)',
                labels={'total_likes': 'Toplam Like', 'total_retweets': 'Toplam Retweet'},
                color_discrete_map={
                    'Cumhuriyet Halk Partisi': '#e31b23',
                    'Adalet Ve Kalkınma Partisi': '#ffa500',
                    'Milliyetçi Hareket Partisi': '#c8102e',
                    'Büyük Birlik Partisi': '#1e3a8a',
                    'Yeniden Refah Partisi': '#006400',
                    'Bağımsız': '#808080'
                }
            )
            st.plotly_chart(fig2, use_container_width=True)

            # Tablo
            st.markdown("### Detayli Tablo")
            st.dataframe(
                engagement_df[['name', 'party', 'tweet_count', 'total_likes', 'total_retweets', 'total_views']].rename(columns={
                    'name': 'Isim',
                    'party': 'Parti',
                    'tweet_count': 'Tweet',
                    'total_likes': 'Like',
                    'total_retweets': 'RT',
                    'total_views': 'View'
                }),
                use_container_width=True,
                height=400
            )

            # Excel Export
            st.markdown("### Export")
            engagement_export = engagement_df.to_dict('records')
            if st.button("📥 Excel Olarak Indir", key="export_engagement"):
                filepath = export_to_excel(engagement_export, f"engagement_raporu_{datetime.now().strftime('%Y%m%d')}")
                if filepath:
                    with open(filepath, 'rb') as f:
                        st.download_button(
                            "💾 Excel Dosyasini Kaydet",
                            f.read(),
                            file_name=filepath.split('/')[-1],
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_engagement"
                        )
        else:
            st.info("Engagement verisi bulunamadi.")

    # ----- TAB 4: ILCE ANALIZI -----
    with tab4:
        st.markdown("### Ilce Bazli Analiz")

        district_df = get_district_stats()

        if not district_df.empty:
            col1, col2 = st.columns(2)

            with col1:
                # Ilce uye sayisi
                fig1 = px.bar(
                    district_df.head(15),
                    x='district',
                    y='member_count',
                    title='Ilce Bazli Uye Sayisi',
                    labels={'district': 'Ilce', 'member_count': 'Uye Sayisi'},
                    color='member_count',
                    color_continuous_scale='Blues'
                )
                fig1.update_layout(showlegend=False)
                st.plotly_chart(fig1, use_container_width=True)

            with col2:
                # Ilce takipci sayisi
                fig2 = px.bar(
                    district_df.head(15),
                    x='district',
                    y='total_followers',
                    title='Ilce Bazli Toplam Takipci',
                    labels={'district': 'Ilce', 'total_followers': 'Toplam Takipci'},
                    color='total_followers',
                    color_continuous_scale='Reds'
                )
                fig2.update_layout(showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)

            # Tablo
            st.dataframe(
                district_df.rename(columns={
                    'district': 'Ilce',
                    'member_count': 'Uye Sayisi',
                    'total_followers': 'Toplam Takipci'
                }),
                use_container_width=True
            )
        else:
            st.info("Ilce verisi bulunamadi.")


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

    # Hizli secim butonlari
    councilors = get_all_councilors()
    parties = list(set([c['party'] for c in councilors if c['party']]))

    st.markdown("**Hizli Secim:**")
    col_btns = st.columns(5)

    # Session state for selected users - use widget key directly
    if 'multi_users_selection' not in st.session_state:
        st.session_state.multi_users_selection = []

    with col_btns[0]:
        if st.button("✅ Tumunu Sec", use_container_width=True):
            st.session_state.multi_users_selection = users.copy()
            st.rerun()

    with col_btns[1]:
        if st.button("❌ Temizle", use_container_width=True):
            st.session_state.multi_users_selection = []
            st.rerun()

    with col_btns[2]:
        if st.button("🔴 CHP", use_container_width=True):
            chp_users = [c['username'] for c in councilors if normalize_party(c['party']) == 'CHP']
            st.session_state.multi_users_selection = chp_users
            st.rerun()

    with col_btns[3]:
        if st.button("🟠 AKP", use_container_width=True):
            akp_users = [c['username'] for c in councilors if normalize_party(c['party']) == 'AKP']
            st.session_state.multi_users_selection = akp_users
            st.rerun()

    with col_btns[4]:
        if st.button("🔵 Diger", use_container_width=True):
            other_users = [c['username'] for c in councilors if normalize_party(c['party']) not in ['CHP', 'AKP']]
            st.session_state.multi_users_selection = other_users
            st.rerun()

    # Multiselect - value directly from session state
    selected_users = st.multiselect(
        "Kullanicilari Sec",
        users,
        default=st.session_state.multi_users_selection
    )

    # Sync back to session state when user manually changes selection
    if selected_users != st.session_state.multi_users_selection:
        st.session_state.multi_users_selection = selected_users

    st.caption(f"Secili: {len(selected_users)} / {len(users)} kullanici")

    # LLM checkbox - separate from multiselect to avoid interference
    multi_llm = st.checkbox("LLM Analizi Ekle", value=False, key="toplu_llm_checkbox")

    if st.button("Toplu Rapor Olustur", type="primary", disabled=len(selected_users) == 0):
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
