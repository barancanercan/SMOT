"""
Tests for Chat with Tweets functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Test IntentParser
class TestIntentParser:
    """Tests for intent parsing"""

    def test_parse_belediye_query(self):
        """Test parsing a simple topic query"""
        from app.services.chat.intent_parser import IntentParser

        parser = IntentParser()
        # Force rule-based parsing for testing
        parser.llm_available = False

        result = parser.parse("Belediye hizmetleriyle atilmis tweetleri getir")

        assert result.intent_type in ["search_topic", "search_date"]
        assert "belediye" in [k.lower() for k in result.filters.get("keywords", [])]

    def test_parse_date_query(self):
        """Test parsing a date range query"""
        from app.services.chat.intent_parser import IntentParser

        parser = IntentParser()
        parser.llm_available = False

        result = parser.parse("01-01-2024 tarihinden 31-03-2024 tarihine kadar atilmis tweetleri getir")

        assert result.intent_type == "search_date"
        assert result.filters.get("start_date") == "2024-01-01"
        assert result.filters.get("end_date") == "2024-03-31"

    def test_parse_username_query(self):
        """Test parsing a user-specific query"""
        from app.services.chat.intent_parser import IntentParser

        parser = IntentParser()
        parser.llm_available = False

        result = parser.parse("@testuser kullanicisinin tweetleri")

        assert result.filters.get("username") == "testuser" or result.filters.get("retweet_from") == "testuser"

    def test_parse_party_query(self):
        """Test parsing a party-specific query"""
        from app.services.chat.intent_parser import IntentParser

        parser = IntentParser()
        parser.llm_available = False

        result = parser.parse("CHP parti uyelerinin tweetlerini goster")

        assert result.filters.get("party") == "CHP"

    def test_parse_criticism_query(self):
        """Test parsing a criticism search query"""
        from app.services.chat.intent_parser import IntentParser

        parser = IntentParser()
        parser.llm_available = False

        result = parser.parse("Elestiri iceren tweetleri getir")

        assert result.intent_type == "search_criticism"
        assert result.filters.get("is_criticism") == True

    def test_parse_empty_query(self):
        """Test parsing an empty query"""
        from app.services.chat.intent_parser import IntentParser

        parser = IntentParser()

        result = parser.parse("")

        assert result.confidence == 0.0

    def test_validate_date_formats(self):
        """Test date validation with different formats"""
        from app.services.chat.intent_parser import IntentParser

        parser = IntentParser()

        # YYYY-MM-DD format
        assert parser._validate_date("2024-01-15") == "2024-01-15"

        # DD-MM-YYYY format
        assert parser._validate_date("15-01-2024") == "2024-01-15"

        # Invalid format
        assert parser._validate_date("invalid") is None


# Test ResponseGenerator
class TestResponseGenerator:
    """Tests for response generation"""

    def test_generate_empty_tweets(self):
        """Test response generation with no tweets"""
        from app.services.chat.response_generator import ResponseGenerator

        generator = ResponseGenerator()
        generator.llm_available = False

        result = generator.generate(
            query="Test query",
            tweets=[],
            intent_type="search_topic"
        )

        assert "bulunamadı" in result.answer.lower() or "bulunamadi" in result.answer.lower()
        assert result.summary["total_found"] == 0

    def test_generate_simple_response(self):
        """Test simple response generation without LLM"""
        from app.services.chat.response_generator import ResponseGenerator

        generator = ResponseGenerator()
        generator.llm_available = False

        tweets = [
            {"username": "user1", "tweet_text": "Test tweet 1", "tweet_date": "2024-01-15", "likes": 10},
            {"username": "user1", "tweet_text": "Test tweet 2", "tweet_date": "2024-01-16", "likes": 20},
            {"username": "user2", "tweet_text": "Test tweet 3", "tweet_date": "2024-01-17", "likes": 30},
        ]

        result = generator.generate(
            query="Test query",
            tweets=tweets,
            intent_type="search_topic"
        )

        assert result.summary["total_found"] == 3
        assert "user1" in result.summary["most_active_users"]

    def test_generate_returns_chat_response(self):
        """Test that generate returns a proper ChatResponse"""
        from app.services.chat.response_generator import ResponseGenerator

        generator = ResponseGenerator()
        generator.llm_available = False

        result = generator.generate(
            query="Test query",
            tweets=[],
            intent_type="search_topic"
        )

        assert result.confidence_score == 0.0
        assert isinstance(result.summary, dict)


# Test ChatHandler
class TestChatHandler:
    """Tests for chat handler"""

    def test_process_short_query(self):
        """Test handling of too short queries"""
        from app.services.chat.chat_handler import ChatHandler

        # Mock database session
        mock_db = Mock()

        handler = ChatHandler(mock_db)
        result = handler.process_query("ab")

        assert "en az 3 karakter" in result.answer.lower()
        assert result.confidence_score == 0.0

    def test_get_suggested_questions(self):
        """Test suggested questions retrieval"""
        from app.services.chat.chat_handler import ChatHandler

        mock_db = Mock()
        handler = ChatHandler(mock_db)

        suggestions = handler.get_suggested_questions()

        assert len(suggestions) > 0
        assert all(isinstance(s, str) for s in suggestions)


# Test Chat Prompts
class TestChatPrompts:
    """Tests for chat prompt templates"""

    def test_format_tweets_for_chat(self):
        """Test tweet formatting for chat"""
        from app.services.analysis.chat_prompts import format_tweets_for_chat

        tweets = [
            {"username": "user1", "tweet_text": "Test tweet", "tweet_date": "2024-01-15", "likes": 10}
        ]

        result = format_tweets_for_chat(tweets)

        assert "@user1" in result
        assert "Test tweet" in result
        assert "2024-01-15" in result

    def test_format_empty_tweets(self):
        """Test formatting with no tweets"""
        from app.services.analysis.chat_prompts import format_tweets_for_chat

        result = format_tweets_for_chat([])

        assert "bulunamadi" in result.lower()

    def test_get_chat_prompt_intent(self):
        """Test intent prompt generation"""
        from app.services.analysis.chat_prompts import get_chat_prompt

        prompt = get_chat_prompt('intent', query="Test query")

        assert "Test query" in prompt
        assert "JSON" in prompt

    def test_get_chat_prompt_response(self):
        """Test response prompt generation"""
        from app.services.analysis.chat_prompts import get_chat_prompt

        tweets = [{"username": "test", "tweet_text": "test tweet", "tweet_date": "2024-01-01", "likes": 5}]
        prompt = get_chat_prompt('response', query="Test query", tweets=tweets, tweet_count=1)

        assert "Test query" in prompt
        assert "1" in prompt  # tweet_count

    def test_get_chat_prompt_invalid_type(self):
        """Test invalid prompt type"""
        from app.services.analysis.chat_prompts import get_chat_prompt

        with pytest.raises(ValueError):
            get_chat_prompt('invalid_type', query="test")


# Integration test (requires database)
class TestChatIntegration:
    """Integration tests for chat functionality"""

    @pytest.mark.skip(reason="Requires database connection")
    def test_full_query_flow(self):
        """Test complete query flow with database"""
        from app.core.db_config import session_scope
        from app.services.chat.chat_handler import ChatHandler

        with session_scope() as db:
            handler = ChatHandler(db)
            result = handler.process_query(
                query="Belediye hizmetleriyle ilgili tweetler",
                max_results=5
            )

            assert result.query == "Belediye hizmetleriyle ilgili tweetler"
            assert result.execution_time_ms > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
