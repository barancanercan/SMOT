#!/usr/bin/env python3
"""
Scraper Tests - Mock mode tests for CDP-based scrapers

Tests run WITHOUT Chrome/browser - all scrapers use --mock flag.
Tests cover:
- Mock tweet generation and structure
- Mock Instagram post generation
- Metric parsing (K, M, B suffixes)
- Date parsing (ISO, relative)
- SQLite save/dedup
- Session manager file operations
- CDPBrowser singleton pattern
"""

import json
import os
import sqlite3
import tempfile
import time
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add project root to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ======================================================================
# Twitter Scraper Tests
# ======================================================================

class TestTwitterMetricParsing:
    """Test engagement metric parsing"""

    def test_parse_integer(self):
        from scrapers.twitter_scraper import parse_metric
        assert parse_metric(1234) == 1234
        assert parse_metric(0) == 0

    def test_parse_string_number(self):
        from scrapers.twitter_scraper import parse_metric
        assert parse_metric("1234") == 1234
        assert parse_metric("0") == 0

    def test_parse_k_suffix(self):
        from scrapers.twitter_scraper import parse_metric
        assert parse_metric("1.2K") == 1200
        assert parse_metric("5.5K") == 5500
        assert parse_metric("72K") == 72000

    def test_parse_m_suffix(self):
        from scrapers.twitter_scraper import parse_metric
        assert parse_metric("1.5M") == 1500000
        assert parse_metric("3M") == 3000000

    def test_parse_b_suffix(self):
        from scrapers.twitter_scraper import parse_metric
        assert parse_metric("1.2B") == 1200000000

    def test_parse_empty(self):
        from scrapers.twitter_scraper import parse_metric
        assert parse_metric("") == 0
        assert parse_metric(None) == 0

    def test_parse_garbage(self):
        from scrapers.twitter_scraper import parse_metric
        assert parse_metric("abc") == 0


class TestTwitterDateParsing:
    """Test tweet date parsing - robust ISO format handling"""

    def test_iso_with_z(self):
        from scrapers.twitter_scraper import parse_tweet_date
        dt = parse_tweet_date("2024-01-15T12:00:00.000Z")
        assert dt is not None
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15

    def test_iso_without_z(self):
        from scrapers.twitter_scraper import parse_tweet_date
        dt = parse_tweet_date("2024-06-20T08:30:00")
        assert dt is not None
        assert dt.month == 6

    def test_iso_with_timezone(self):
        from scrapers.twitter_scraper import parse_tweet_date
        dt = parse_tweet_date("2024-03-10T15:00:00+00:00")
        assert dt is not None

    def test_empty(self):
        from scrapers.twitter_scraper import parse_tweet_date
        assert parse_tweet_date("") is None
        assert parse_tweet_date(None) is None

    def test_invalid_format(self):
        from scrapers.twitter_scraper import parse_tweet_date
        assert parse_tweet_date("not-a-date") is None


class TestTwitterWithinDays:
    """Test time window filtering"""

    def test_recent_tweet(self):
        from scrapers.twitter_scraper import is_within_days
        recent = datetime.now() - timedelta(days=5)
        assert is_within_days(recent, 90) is True

    def test_old_tweet(self):
        from scrapers.twitter_scraper import is_within_days
        old = datetime.now() - timedelta(days=100)
        assert is_within_days(old, 90) is False

    def test_none_date(self):
        from scrapers.twitter_scraper import is_within_days
        assert is_within_days(None, 90) is True


class TestTwitterMockMode:
    """Test mock tweet generation"""

    def test_mock_generates_tweets(self):
        from scrapers.twitter_scraper import generate_mock_tweets
        tweets = generate_mock_tweets("test_user", 20)
        assert len(tweets) == 20

    def test_mock_tweet_structure(self):
        from scrapers.twitter_scraper import generate_mock_tweets
        tweets = generate_mock_tweets("test_user", 5)
        tweet = tweets[0]

        assert "text" in tweet
        assert "tweet_id" in tweet
        assert "timestamp" in tweet
        assert "username" in tweet
        assert tweet["username"] == "test_user"
        assert "likes" in tweet
        assert "retweets" in tweet
        assert "views" in tweet
        assert "is_retweet" in tweet
        assert "media_type" in tweet

    def test_mock_scraper_class(self):
        from scrapers.twitter_scraper import TwitterCDPScraper
        scraper = TwitterCDPScraper(mock=True)
        tweets = scraper.scrape_tweets("test_user", max_tweets=10)
        assert len(tweets) > 0
        assert all(t["username"] == "test_user" for t in tweets)


class TestTwitterSQLiteSave:
    """Test SQLite save with WAL mode"""

    def test_save_to_db(self):
        from scrapers.twitter_scraper import generate_mock_tweets, save_to_db

        tweets = generate_mock_tweets("test_user", 10)

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            saved = save_to_db(tweets, politician_id=1, db_path=db_path)
            assert saved > 0

            # Verify data in DB
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT COUNT(*) FROM tweets")
            count = cursor.fetchone()[0]
            conn.close()
            assert count == 10

    def test_dedup_by_tweet_id(self):
        from scrapers.twitter_scraper import generate_mock_tweets, save_to_db

        tweets = generate_mock_tweets("test_user", 5)

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")

            # Save once
            save_to_db(tweets, politician_id=1, db_path=db_path)

            # Save again (same tweets)
            save_to_db(tweets, politician_id=1, db_path=db_path)

            # Should still be 5 (dedup by tweet_id)
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT COUNT(*) FROM tweets")
            count = cursor.fetchone()[0]
            conn.close()
            assert count == 5

    def test_wal_mode_enabled(self):
        from scrapers.twitter_scraper import generate_mock_tweets, save_to_db

        tweets = generate_mock_tweets("test_user", 3)

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            save_to_db(tweets, politician_id=1, db_path=db_path)

            conn = sqlite3.connect(db_path)
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            conn.close()
            assert mode == "wal"


# ======================================================================
# Instagram Scraper Tests
# ======================================================================

class TestInstagramMetricParsing:
    """Test Instagram metric parsing (TR/EN formats)"""

    def test_parse_integer(self):
        from scrapers.instagram_scraper import parse_ig_metric
        assert parse_ig_metric(1234) == 1234

    def test_parse_k_suffix(self):
        from scrapers.instagram_scraper import parse_ig_metric
        assert parse_ig_metric("72.4K") == 72400
        assert parse_ig_metric("5K") == 5000

    def test_parse_tr_b_suffix(self):
        """Turkish: B = Bin (thousand)"""
        from scrapers.instagram_scraper import parse_ig_metric
        assert parse_ig_metric("72B") == 72000

    def test_parse_m_suffix(self):
        from scrapers.instagram_scraper import parse_ig_metric
        assert parse_ig_metric("1.5M") == 1500000

    def test_parse_tr_comma_decimal(self):
        """Turkish: comma is decimal separator"""
        from scrapers.instagram_scraper import parse_ig_metric
        assert parse_ig_metric("72,4K") == 72400

    def test_parse_en_thousands(self):
        from scrapers.instagram_scraper import parse_ig_metric
        assert parse_ig_metric("1,283") == 1283

    def test_parse_empty(self):
        from scrapers.instagram_scraper import parse_ig_metric
        assert parse_ig_metric("") == 0
        assert parse_ig_metric(None) == 0


class TestInstagramDateParsing:
    """Test Instagram date parsing"""

    def test_iso_format(self):
        from scrapers.instagram_scraper import parse_ig_date
        dt = parse_ig_date("2024-01-15T12:00:00.000Z")
        assert dt is not None
        assert dt.year == 2024

    def test_relative_days(self):
        from scrapers.instagram_scraper import parse_ig_date
        dt = parse_ig_date("3 days ago")
        assert dt is not None
        assert (datetime.now() - dt).days in (2, 3, 4)  # Allow 1 day margin

    def test_relative_tr_gun(self):
        from scrapers.instagram_scraper import parse_ig_date
        dt = parse_ig_date("2 gün önce")
        assert dt is not None

    def test_relative_weeks(self):
        from scrapers.instagram_scraper import parse_ig_date
        dt = parse_ig_date("2 weeks ago")
        assert dt is not None
        assert (datetime.now() - dt).days >= 12

    def test_empty(self):
        from scrapers.instagram_scraper import parse_ig_date
        assert parse_ig_date("") is None
        assert parse_ig_date(None) is None


class TestInstagramMockMode:
    """Test mock Instagram post generation"""

    def test_mock_generates_posts(self):
        from scrapers.instagram_scraper import generate_mock_posts
        posts = generate_mock_posts("test_user", 15)
        assert len(posts) == 15

    def test_mock_post_structure(self):
        from scrapers.instagram_scraper import generate_mock_posts
        posts = generate_mock_posts("test_user", 3)
        post = posts[0]

        assert "username" in post
        assert "post_id" in post
        assert "caption" in post
        assert "likes" in post
        assert "comments" in post
        assert "post_date" in post
        assert post["username"] == "test_user"

    def test_mock_scraper_class(self):
        from scrapers.instagram_scraper import InstagramCDPScraper
        scraper = InstagramCDPScraper(mock=True)
        posts = scraper.scrape_posts("test_user", max_posts=10)
        assert len(posts) > 0

    def test_mock_profile(self):
        from scrapers.instagram_scraper import InstagramCDPScraper
        scraper = InstagramCDPScraper(mock=True)
        profile = scraper.scrape_profile("test_user")
        assert profile is not None
        assert profile["username"] == "test_user"
        assert profile["followers"] > 0


class TestInstagramSQLiteSave:
    """Test Instagram SQLite save"""

    def test_save_posts(self):
        from scrapers.instagram_scraper import generate_mock_posts, save_posts_to_db

        posts = generate_mock_posts("test_user", 8)

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            saved = save_posts_to_db(posts, politician_id=1, db_path=db_path)
            assert saved == 8

            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT COUNT(*) FROM instagram_posts")
            count = cursor.fetchone()[0]
            conn.close()
            assert count == 8

    def test_dedup_by_post_id(self):
        from scrapers.instagram_scraper import generate_mock_posts, save_posts_to_db

        posts = generate_mock_posts("test_user", 5)

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            save_posts_to_db(posts, politician_id=1, db_path=db_path)
            save_posts_to_db(posts, politician_id=1, db_path=db_path)

            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT COUNT(*) FROM instagram_posts")
            count = cursor.fetchone()[0]
            conn.close()
            assert count == 5


# ======================================================================
# CDPBrowser Tests
# ======================================================================

class TestCDPBrowserSingleton:
    """Test CDPBrowser singleton pattern"""

    def test_singleton_same_instance(self):
        from scrapers.cdp_browser import CDPBrowser

        # Reset singleton for test
        CDPBrowser._instance = None

        b1 = CDPBrowser.__new__(CDPBrowser)
        b2 = CDPBrowser.__new__(CDPBrowser)
        assert b1 is b2

        # Cleanup
        CDPBrowser._instance = None

    def test_find_chrome_binary(self):
        from scrapers.cdp_browser import CDPBrowser
        # This tests that the method runs without error
        # Result depends on whether Chrome is installed
        result = CDPBrowser._find_chrome_binary()
        # On CI without Chrome, result may be None - that's OK
        assert result is None or isinstance(result, str)


# ======================================================================
# Session Manager Tests
# ======================================================================

class TestSessionManager:
    """Test session manager operations"""

    def test_session_file_paths(self):
        from scrapers.session_manager import SessionManager
        sm = SessionManager()
        assert "x_session.json" in sm.get_session_file("twitter")
        assert "ig_session.json" in sm.get_session_file("instagram")

    def test_unknown_platform_raises(self):
        from scrapers.session_manager import SessionManager
        sm = SessionManager()
        with pytest.raises(ValueError):
            sm.get_session_file("facebook")

    def test_load_save_session(self):
        from scrapers.session_manager import SessionManager, SESSION_FILES

        sm = SessionManager()

        # Create temp session file
        test_cookies = [
            {"name": "test_cookie", "value": "abc123", "domain": ".x.com"},
            {"name": "auth_token", "value": "xyz789", "domain": ".x.com"},
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_cookies, f)
            temp_path = f.name

        try:
            # Override session file path temporarily
            original = SESSION_FILES["twitter"]
            SESSION_FILES["twitter"] = temp_path

            # Load
            loaded = sm.load_session("twitter")
            assert loaded is not None
            assert len(loaded) == 2
            assert loaded[0]["name"] == "test_cookie"

            # Save new cookies
            new_cookies = [{"name": "new_cookie", "value": "new_val", "domain": ".x.com"}]
            success = sm.save_session("twitter", new_cookies)
            assert success is True

            # Reload
            reloaded = sm.load_session("twitter")
            assert len(reloaded) == 1
            assert reloaded[0]["name"] == "new_cookie"

        finally:
            SESSION_FILES["twitter"] = original
            os.unlink(temp_path)

    def test_check_expiry_missing_file(self):
        from scrapers.session_manager import SessionManager, SESSION_FILES

        sm = SessionManager()
        original = SESSION_FILES["twitter"]
        SESSION_FILES["twitter"] = "/nonexistent/path.json"

        try:
            result = sm.check_expiry("twitter")
            assert result["valid"] is False
            assert result["warning"] is not None
        finally:
            SESSION_FILES["twitter"] = original

    def test_check_expiry_fresh_file(self):
        from scrapers.session_manager import SessionManager, SESSION_FILES

        sm = SessionManager()

        # Create a fresh session file with future-expiring cookies
        future_ts = time.time() + 86400 * 30  # 30 days from now
        cookies = [
            {"name": "auth", "value": "x", "domain": ".x.com", "expires": future_ts},
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(cookies, f)
            temp_path = f.name

        original = SESSION_FILES["twitter"]
        SESSION_FILES["twitter"] = temp_path

        try:
            result = sm.check_expiry("twitter")
            assert result["total_cookies"] == 1
            assert result["expired_cookies"] == 0
            assert result["file_age_days"] < 1
            assert result["valid"] is True
        finally:
            SESSION_FILES["twitter"] = original
            os.unlink(temp_path)

    def test_status_report(self):
        from scrapers.session_manager import SessionManager
        sm = SessionManager()
        status = sm.status()
        assert "twitter" in status
        assert "instagram" in status
        assert "file_exists" in status["twitter"]


# ======================================================================
# Integration: End-to-end mock scraping
# ======================================================================

class TestEndToEndMock:
    """Full mock scraping pipeline"""

    def test_twitter_mock_pipeline(self):
        """Mock: scrape -> save -> verify"""
        from scrapers.twitter_scraper import TwitterCDPScraper, save_to_db

        scraper = TwitterCDPScraper(mock=True)
        tweets = scraper.scrape_tweets("mock_politician", max_tweets=15)

        assert len(tweets) > 0
        assert all("text" in t for t in tweets)
        assert all("tweet_id" in t for t in tweets)

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            saved = save_to_db(tweets, politician_id=42, db_path=db_path)
            assert saved > 0

    def test_instagram_mock_pipeline(self):
        """Mock: scrape profile + posts -> save -> verify"""
        from scrapers.instagram_scraper import InstagramCDPScraper, save_posts_to_db

        scraper = InstagramCDPScraper(mock=True)
        data = scraper.scrape_user_complete("mock_politician", max_posts=10)

        assert data["profile"] is not None
        assert len(data["posts"]) > 0

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            saved = save_posts_to_db(data["posts"], politician_id=42, db_path=db_path)
            assert saved > 0

    def test_multiple_users_mock(self):
        """Mock: batch scrape multiple users"""
        from scrapers.twitter_scraper import TwitterCDPScraper

        scraper = TwitterCDPScraper(mock=True)
        results = scraper.scrape_multiple(
            ["user1", "user2", "user3"],
            max_tweets=10,
        )

        assert len(results) == 3
        assert all(len(tweets) > 0 for tweets in results.values())


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
