#!/usr/bin/env python3
"""
Session Manager v1.0 - Cookie session management for scrapers

- x_session.json / ig_session.json cookie yonetimi
- Cookie expiry kontrolu (7 gunden eski -> uyari)
- validate_session(platform): cookie gecerliligi test
  - Twitter: /home'a git, login'e redirect = gecersiz
  - Instagram: profile'a git, login'e redirect = gecersiz
- Cookie dosyasi olusturma / guncelleme
"""

import json
import os
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List

try:
    from .cdp_browser import CDPBrowser
except ImportError:
    from cdp_browser import CDPBrowser

logger = logging.getLogger("SessionManager")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Session file paths
SESSION_FILES = {
    "twitter": os.path.join(PROJECT_ROOT, "x_session.json"),
    "instagram": os.path.join(PROJECT_ROOT, "ig_session.json"),
}

# Domains
DOMAINS = {
    "twitter": ".x.com",
    "instagram": ".instagram.com",
}

# Cookie expiry warning threshold (days)
EXPIRY_WARNING_DAYS = 7

# Validation URLs
VALIDATION_CONFIG = {
    "twitter": {
        "test_url": "https://x.com/home",
        "login_indicators": ["x.com/login", "x.com/i/flow/login"],
        "success_indicators": ["x.com/home"],
    },
    "instagram": {
        "test_url": "https://www.instagram.com/",
        "login_indicators": ["instagram.com/accounts/login"],
        "success_indicators": ["instagram.com/"],
    },
}


class SessionManager:
    """Manage browser session cookies for Twitter and Instagram"""

    def __init__(self):
        self.browser: Optional[CDPBrowser] = None

    def _get_browser(self) -> CDPBrowser:
        """Get or create CDPBrowser instance"""
        if self.browser is None:
            self.browser = CDPBrowser()
        return self.browser

    # ------------------------------------------------------------------
    # Session File Operations
    # ------------------------------------------------------------------

    def get_session_file(self, platform: str) -> str:
        """Get session file path for platform"""
        platform = platform.lower()
        if platform not in SESSION_FILES:
            raise ValueError(f"Unknown platform: {platform}. Use 'twitter' or 'instagram'")
        return SESSION_FILES[platform]

    def session_exists(self, platform: str) -> bool:
        """Check if session file exists"""
        path = self.get_session_file(platform)
        return os.path.isfile(path)

    def load_session(self, platform: str) -> Optional[List[Dict]]:
        """Load cookies from session file"""
        path = self.get_session_file(platform)
        if not os.path.isfile(path):
            logger.warning(f"Session file not found: {path}")
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                cookies = json.load(f)

            if not isinstance(cookies, list):
                logger.error(f"Invalid session format (expected list): {path}")
                return None

            logger.info(f"Loaded {len(cookies)} cookies from {path}")
            return cookies

        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load session: {e}")
            return None

    def save_session(self, platform: str, cookies: List[Dict]) -> bool:
        """Save cookies to session file"""
        path = self.get_session_file(platform)

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved {len(cookies)} cookies to {path}")
            return True

        except IOError as e:
            logger.error(f"Failed to save session: {e}")
            return False

    # ------------------------------------------------------------------
    # Cookie Expiry Check
    # ------------------------------------------------------------------

    def check_expiry(self, platform: str) -> Dict:
        """
        Check cookie expiry status.

        Returns:
            {
                'valid': bool,
                'file_age_days': float,
                'expired_cookies': int,
                'total_cookies': int,
                'warning': str or None,
                'oldest_cookie_days': float,
            }
        """
        result = {
            "valid": False,
            "file_age_days": 0,
            "expired_cookies": 0,
            "total_cookies": 0,
            "warning": None,
            "oldest_cookie_days": 0,
        }

        path = self.get_session_file(platform)

        if not os.path.isfile(path):
            result["warning"] = f"Session file not found: {path}"
            return result

        # Check file modification time
        file_mtime = os.path.getmtime(path)
        file_age = (time.time() - file_mtime) / 86400  # days
        result["file_age_days"] = round(file_age, 1)

        if file_age > EXPIRY_WARNING_DAYS:
            result["warning"] = (
                f"Session file is {file_age:.0f} days old (>{EXPIRY_WARNING_DAYS} day threshold). "
                f"Cookies may be expired. Re-login recommended."
            )
            logger.warning(result["warning"])

        # Check individual cookie expiry
        cookies = self.load_session(platform)
        if not cookies:
            result["warning"] = "Could not load cookies"
            return result

        result["total_cookies"] = len(cookies)
        now = time.time()
        expired_count = 0
        oldest_days = 0

        for cookie in cookies:
            expires = cookie.get("expires") or cookie.get("expirationDate")
            if expires:
                try:
                    exp_ts = float(expires)
                    if exp_ts > 0 and exp_ts < now:
                        expired_count += 1

                    # Track oldest cookie
                    cookie_age = (now - exp_ts) / 86400
                    if cookie_age > oldest_days:
                        oldest_days = cookie_age
                except (ValueError, TypeError):
                    pass

        result["expired_cookies"] = expired_count
        result["oldest_cookie_days"] = round(abs(oldest_days), 1)

        # Determine overall validity
        if expired_count > len(cookies) * 0.5:
            result["valid"] = False
            result["warning"] = (
                f"{expired_count}/{len(cookies)} cookies expired. Re-login required."
            )
        elif file_age > EXPIRY_WARNING_DAYS:
            result["valid"] = False  # Old file = likely invalid
        else:
            result["valid"] = True

        return result

    # ------------------------------------------------------------------
    # Session Validation (live check)
    # ------------------------------------------------------------------

    def validate_session(self, platform: str) -> Dict:
        """
        Test if session cookies are still valid by navigating to a test page.

        - Twitter: Navigate to /home, check if redirected to /login
        - Instagram: Navigate to /, check if redirected to /accounts/login

        Returns:
            {
                'valid': bool,
                'platform': str,
                'final_url': str,
                'message': str,
            }
        """
        platform = platform.lower()
        if platform not in VALIDATION_CONFIG:
            return {"valid": False, "platform": platform, "final_url": "", "message": "Unknown platform"}

        config = VALIDATION_CONFIG[platform]
        result = {"valid": False, "platform": platform, "final_url": "", "message": ""}

        # First check file expiry
        expiry = self.check_expiry(platform)
        if not expiry["valid"] and expiry["warning"]:
            result["message"] = expiry["warning"]
            logger.warning(f"Session expiry check failed: {expiry['warning']}")
            # Continue with live check anyway

        browser = self._get_browser()

        try:
            browser.ensure_running()

            # Clear existing cookies first
            browser.clear_cookies()

            # Inject session cookies
            session_file = self.get_session_file(platform)
            domain = DOMAINS[platform]
            count = browser.inject_cookies(session_file, domain)

            if count == 0:
                result["message"] = "No cookies to inject"
                return result

            # Navigate to test URL
            browser.navigate(config["test_url"])
            time.sleep(3)  # Wait for redirects

            # Check final URL
            final_url = browser.get_current_url()
            result["final_url"] = final_url

            # Check for login redirect (= invalid)
            for indicator in config["login_indicators"]:
                if indicator in final_url:
                    result["valid"] = False
                    result["message"] = (
                        f"Session INVALID: redirected to login ({final_url}). "
                        f"Re-login required."
                    )
                    logger.warning(result["message"])
                    return result

            # Check for success indicators
            for indicator in config["success_indicators"]:
                if indicator in final_url:
                    result["valid"] = True
                    result["message"] = f"Session VALID for {platform}"
                    logger.info(result["message"])
                    return result

            # Ambiguous - check page content
            page_text = browser.evaluate("document.body.innerText.substring(0, 500)") or ""
            if "login" in page_text.lower() or "sign in" in page_text.lower() or "giriş" in page_text.lower():
                result["valid"] = False
                result["message"] = f"Session likely invalid (login text found on page)"
            else:
                result["valid"] = True
                result["message"] = f"Session appears valid (final URL: {final_url})"

            return result

        except Exception as e:
            result["message"] = f"Validation error: {str(e)[:100]}"
            logger.error(result["message"])
            return result

    # ------------------------------------------------------------------
    # Extract Cookies from Browser
    # ------------------------------------------------------------------

    def capture_cookies(self, platform: str) -> bool:
        """
        Capture current browser cookies and save to session file.
        Use after manual login in Chrome to save the session.

        Connects to running Chrome via CDP, gets all cookies for the platform
        domain, and saves them to the session file.
        """
        platform = platform.lower()
        domain = DOMAINS.get(platform, "")
        if not domain:
            logger.error(f"Unknown platform: {platform}")
            return False

        browser = self._get_browser()

        try:
            browser.ensure_running()

            # Use the public get_all_cookies method with domain filter
            platform_cookies = browser.get_all_cookies(domain_filter=domain)

            if not platform_cookies:
                logger.warning(f"No cookies found for {domain}")
                logger.warning("Make sure you are logged in to the platform in the Chrome window")
                return False

            logger.info(f"Captured {len(platform_cookies)} cookies for {domain}")

            # Save to session file
            success = self.save_session(platform, platform_cookies)
            if success:
                logger.info(f"Session saved: {self.get_session_file(platform)}")
            return success

        except Exception as e:
            logger.error(f"Failed to capture cookies: {e}")
            return False

    # ------------------------------------------------------------------
    # Status Report
    # ------------------------------------------------------------------

    def status(self) -> Dict[str, Dict]:
        """Get status of all platform sessions"""
        results = {}
        for platform in SESSION_FILES:
            info = {
                "file_exists": self.session_exists(platform),
                "file_path": self.get_session_file(platform),
            }

            if info["file_exists"]:
                expiry = self.check_expiry(platform)
                info.update(expiry)
            else:
                info["valid"] = False
                info["warning"] = "Session file does not exist"

            results[platform] = info

        return results

    def close(self) -> None:
        if self.browser:
            self.browser.close()
            self.browser = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ======================================================================
# CLI
# ======================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Session Manager v1.0")
    parser.add_argument("action", choices=["status", "check", "validate", "capture"],
                        help="Action: status=show all, check=expiry check, validate=live test, capture=save cookies")
    parser.add_argument("--platform", "-p", choices=["twitter", "instagram"],
                        help="Platform (required for check/validate/capture)")

    args = parser.parse_args()

    sm = SessionManager()

    try:
        if args.action == "status":
            status = sm.status()
            for platform, info in status.items():
                print(f"\n{'=' * 50}")
                print(f"  {platform.upper()}")
                print(f"{'=' * 50}")
                print(f"  File: {info['file_path']}")
                print(f"  Exists: {info['file_exists']}")
                if info.get("file_age_days"):
                    print(f"  File age: {info['file_age_days']} days")
                if info.get("total_cookies"):
                    print(f"  Cookies: {info['total_cookies']} total, {info.get('expired_cookies', 0)} expired")
                print(f"  Valid: {info.get('valid', False)}")
                if info.get("warning"):
                    print(f"  WARNING: {info['warning']}")

        elif args.action == "check":
            if not args.platform:
                parser.error("--platform required for check")
            result = sm.check_expiry(args.platform)
            print(f"\nExpiry check for {args.platform}:")
            print(f"  Valid: {result['valid']}")
            print(f"  File age: {result['file_age_days']} days")
            print(f"  Cookies: {result['total_cookies']} total, {result['expired_cookies']} expired")
            if result["warning"]:
                print(f"  WARNING: {result['warning']}")

        elif args.action == "validate":
            if not args.platform:
                parser.error("--platform required for validate")
            print(f"\nValidating {args.platform} session (live check)...")
            result = sm.validate_session(args.platform)
            print(f"  Valid: {result['valid']}")
            print(f"  Final URL: {result['final_url']}")
            print(f"  Message: {result['message']}")

        elif args.action == "capture":
            if not args.platform:
                parser.error("--platform required for capture")
            print(f"\nCapturing {args.platform} cookies from browser...")
            success = sm.capture_cookies(args.platform)
            print(f"  Success: {success}")

    finally:
        sm.close()
