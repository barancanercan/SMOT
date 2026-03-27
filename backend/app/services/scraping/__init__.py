"""
Scraping modulu
"""
from .profile_scraper import ProfileScraper, get_weekly_comparison, print_weekly_report
from .instagram_scraper import InstagramScraper

__all__ = [
    "ProfileScraper",
    "get_weekly_comparison",
    "print_weekly_report",
    "InstagramScraper"
]