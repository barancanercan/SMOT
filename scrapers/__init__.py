"""
Scrapers module - CDP-based web scraping infrastructure
"""
from .cdp_browser import CDPBrowser
from .session_manager import SessionManager

__all__ = ["CDPBrowser", "SessionManager"]
