"""
Scraping modulu
"""
from .instagram_scraper import InstagramScraper
from .profile_scraper import ProfileScraper, get_weekly_comparison, print_weekly_report

__all__ = [
    "ProfileScraper",
    "get_weekly_comparison",
    "print_weekly_report",
    "InstagramScraper"
]
