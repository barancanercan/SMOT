"""
Retry Configuration - Centralized retry logic using tenacity
Provides decorators for different operation types with appropriate retry strategies
"""
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
import logging
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException
)
import sqlite3

logger = logging.getLogger("MeclisIstihbarat")


# Scraping retry decorator - for web scraping operations
retry_on_scraping_error = retry(
    retry=retry_if_exception_type((
        TimeoutException,
        NoSuchElementException,
        StaleElementReferenceException,
        WebDriverException
    )),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    after=after_log(logger, logging.INFO)
)


# Session retry decorator - for browser session errors
retry_on_session_error = retry(
    retry=retry_if_exception_type((
        WebDriverException,
    )),
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=3, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    after=after_log(logger, logging.INFO)
)


# Database retry decorator - for database operations
retry_on_db_error = retry(
    retry=retry_if_exception_type((
        sqlite3.OperationalError,  # Database locked
        sqlite3.IntegrityError,     # Constraint violations
    )),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=0.5, min=1, max=5),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    after=after_log(logger, logging.INFO)
)


# Network retry decorator - for HTTP requests
retry_on_network_error = retry(
    retry=retry_if_exception_type((
        ConnectionError,
        TimeoutError,
    )),
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=15),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    after=after_log(logger, logging.INFO)
)
