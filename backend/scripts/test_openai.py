#!/usr/bin/env python3
"""
Test OpenAI Integration - Quick verification script
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.analysis.analyzer import TweetAnalyzer
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger("TestOpenAI")


def test_openai_connection():
    """Test OpenAI API connection and basic analysis"""

    print("="*60)
    print("OpenAI Integration Test")
    print("="*60)

    # Check config
    print(f"\nConfiguration:")
    print(f"  LLM Provider: {settings.llm_provider}")
    print(f"  OpenAI Model: {settings.openai_model}")
    print(f"  API Key set: {'Yes' if settings.openai_api_key else 'No'}")

    if not settings.openai_api_key:
        print("\n❌ ERROR: OPENAI_API_KEY not set in .env")
        print("   Please add: OPENAI_API_KEY=your-key-here")
        return False

    # Initialize analyzer
    print(f"\nInitializing analyzer...")
    analyzer = TweetAnalyzer()
    print(f"  Provider: {analyzer.provider}")
    print(f"  Model: {analyzer.model}")

    # Test with simple tweet data
    test_tweets = [
        {
            'text': 'İstanbul için yeni projeler başlatıyoruz. Halkımıza daha iyi hizmet için çalışıyoruz.',
            'date': '2024-01-15',
            'likes': 150,
            'retweets': 30,
            'replies': 10,
            'views': 5000
        },
        {
            'text': 'Belediyemiz vatandaşların sesine kulak veriyor. Şeffaf yönetim devam ediyor.',
            'date': '2024-01-14',
            'likes': 200,
            'retweets': 45,
            'replies': 15,
            'views': 6000
        }
    ]

    print(f"\nTesting analysis with {len(test_tweets)} sample tweets...")

    try:
        result = analyzer.analyze_intelligence(
            tweets=test_tweets,
            username='test_user',
            period='Test Period',
            party='Test Party'
        )

        print(f"\n✓ Analysis completed!")
        print(f"  Validated: {result.get('validated', False)}")
        print(f"  Duration: {result.get('elapsed_seconds', 0):.2f}s")

        if result.get('validated') and result.get('analysis'):
            analysis = result['analysis']
            print(f"\nAnalysis Preview:")
            print(f"  Executive Summary: {analysis.executive_summary[:100]}...")
            print(f"  Loyalty Level: {analysis.loyalty_level}")
            print(f"  Criticism Level: {analysis.criticism_level}")
            print(f"  Confidence Score: {analysis.confidence_score}")

        print("\n✓ OpenAI integration working correctly!")
        return True

    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_openai_connection()
    sys.exit(0 if success else 1)
