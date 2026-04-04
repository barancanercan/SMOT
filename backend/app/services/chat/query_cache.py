#!/usr/bin/env python3
"""
Query Cache for Chat with Tweets

Provides caching for:
1. Intent parsing results (same query -> same intent)
2. Response caching (similar queries -> cached response)
3. TTL-based expiration

Uses both in-memory cache and database cache (ReportCache).
"""

import hashlib
import json
import time
from typing import Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.utils.logger import get_logger

logger = get_logger("QueryCache")


# =============================================================================
# CACHE CONFIGURATION
# =============================================================================

# Cache TTL in seconds
INTENT_CACHE_TTL = 3600  # 1 hour for intent
RESPONSE_CACHE_TTL = 1800  # 30 minutes for responses


# =============================================================================
# IN-MEMORY CACHE
# =============================================================================

@dataclass
class CacheEntry:
    """Single cache entry."""
    key: str
    value: Any
    expires_at: float
    created_at: float
    hit_count: int = 0


class InMemoryCache:
    """
    Simple in-memory cache with TTL support.

    Thread-safe enough for single-process deployments.
    For multi-process, use Redis or similar.
    """

    MAX_SIZE = 1000  # Maximum entries

    def __init__(self):
        """Initialize the cache."""
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: list = []  # LRU tracking

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        entry = self._cache.get(key)

        if entry is None:
            return None

        # Check expiration
        if time.time() > entry.expires_at:
            self._remove(key)
            return None

        # Update access
        entry.hit_count += 1
        self._update_access(key)

        return entry.value

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        # Evict if at max size
        if len(self._cache) >= self.MAX_SIZE:
            self._evict_oldest()

        now = time.time()
        entry = CacheEntry(
            key=key,
            value=value,
            expires_at=now + ttl,
            created_at=now,
            hit_count=0
        )

        self._cache[key] = entry
        self._update_access(key)

        logger.debug(f"Cache SET: {key[:50]}... (TTL: {ttl}s)")

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        return self._remove(key)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._access_order.clear()
        logger.info("Cache cleared")

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        now = time.time()
        valid_entries = sum(
            1 for e in self._cache.values()
            if e.expires_at > now
        )
        total_hits = sum(e.hit_count for e in self._cache.values())

        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "total_hits": total_hits,
            "max_size": self.MAX_SIZE
        }

    def _remove(self, key: str) -> bool:
        """Remove entry from cache."""
        if key in self._cache:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return True
        return False

    def _update_access(self, key: str) -> None:
        """Update LRU access order."""
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

    def _evict_oldest(self) -> None:
        """Evict least recently used entry."""
        if self._access_order:
            oldest_key = self._access_order.pop(0)
            self._remove(oldest_key)
            logger.debug(f"Evicted: {oldest_key[:50]}...")


# Global cache instance
_cache = InMemoryCache()


# =============================================================================
# CACHE FUNCTIONS
# =============================================================================

def generate_cache_key(prefix: str, query: str, filters: Optional[Dict] = None) -> str:
    """
    Generate a unique cache key.

    Args:
        prefix: Cache type prefix (intent, response)
        query: User query
        filters: Optional filters

    Returns:
        Cache key string
    """
    # Normalize query
    normalized_query = query.lower().strip()

    # Include filters in key
    filter_str = ""
    if filters:
        # Sort for consistency
        sorted_filters = sorted(
            (k, v) for k, v in filters.items()
            if v is not None
        )
        filter_str = str(sorted_filters)

    # Hash for consistent key length
    content = f"{normalized_query}|{filter_str}"
    hash_value = hashlib.md5(content.encode()).hexdigest()[:16]

    return f"{prefix}:{hash_value}"


def get_intent_cache(
    query: str,
    party_filter: Optional[str] = None,
    platform: str = "twitter"
) -> Optional[Dict]:
    """
    Get cached intent for query with filters.

    Args:
        query: User query
        party_filter: Party filter
        platform: Platform

    Returns:
        Cached intent dict or None
    """
    key = generate_cache_key("intent", query, {"party": party_filter, "platform": platform})
    cached = _cache.get(key)

    if cached:
        logger.info(f"Intent cache HIT: {query[:30]}...")
    else:
        logger.debug(f"Intent cache MISS: {query[:30]}...")

    return cached


def set_intent_cache(
    query: str,
    intent: Dict,
    party_filter: Optional[str] = None,
    platform: str = "twitter"
) -> None:
    """
    Cache intent for query with filters.

    Args:
        query: User query
        intent: Intent dict to cache
        party_filter: Party filter
        platform: Platform
    """
    key = generate_cache_key("intent", query, {"party": party_filter, "platform": platform})
    _cache.set(key, intent, ttl=INTENT_CACHE_TTL)


def get_response_cache(
    query: str,
    filters: Optional[Dict] = None,
    platform: str = "twitter"
) -> Optional[Dict]:
    """
    Get cached response for query.

    Args:
        query: User query
        filters: Applied filters
        platform: Platform

    Returns:
        Cached response dict or None
    """
    combined_filters = {
        **(filters or {}),
        "_platform": platform
    }
    key = generate_cache_key("response", query, combined_filters)
    cached = _cache.get(key)

    if cached:
        logger.info(f"Response cache HIT: {query[:30]}...")

    return cached


def set_response_cache(
    query: str,
    response: Dict,
    filters: Optional[Dict] = None,
    platform: str = "twitter"
) -> None:
    """
    Cache response for query.

    Args:
        query: User query
        response: Response dict to cache
        filters: Applied filters
        platform: Platform
    """
    combined_filters = {
        **(filters or {}),
        "_platform": platform
    }
    key = generate_cache_key("response", query, combined_filters)
    _cache.set(key, response, ttl=RESPONSE_CACHE_TTL)


def clear_cache() -> None:
    """Clear all cache."""
    _cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    return _cache.stats()


# =============================================================================
# DATABASE CACHE (for persistent caching)
# =============================================================================

def get_db_cache(
    db: Session,
    cache_type: str,
    key: str
) -> Optional[str]:
    """
    Get value from database cache (ReportCache).

    Args:
        db: Database session
        cache_type: Type of cache (chat_intent, chat_response)
        key: Cache key

    Returns:
        Cached content or None
    """
    from app.core.models import ReportCache

    try:
        cache_entry = db.query(ReportCache).filter(
            ReportCache.username == key,
            ReportCache.report_type == cache_type,
            ReportCache.expires_at > datetime.utcnow()
        ).first()

        if cache_entry:
            logger.info(f"DB cache HIT: {cache_type}/{key[:30]}")
            return cache_entry.content

    except Exception as e:
        logger.warning(f"DB cache error: {e}")

    return None


def set_db_cache(
    db: Session,
    cache_type: str,
    key: str,
    content: str,
    ttl_hours: int = 1
) -> bool:
    """
    Set value in database cache.

    Args:
        db: Database session
        cache_type: Type of cache
        key: Cache key
        content: Content to cache
        ttl_hours: TTL in hours

    Returns:
        Success status
    """
    from app.core.models import ReportCache

    try:
        # Delete existing
        db.query(ReportCache).filter(
            ReportCache.username == key,
            ReportCache.report_type == cache_type
        ).delete()

        # Create new
        cache_entry = ReportCache(
            username=key,
            report_type=cache_type,
            content=content,
            expires_at=datetime.utcnow() + timedelta(hours=ttl_hours)
        )
        db.add(cache_entry)
        db.commit()

        logger.debug(f"DB cache SET: {cache_type}/{key[:30]}")
        return True

    except Exception as e:
        logger.error(f"DB cache write error: {e}")
        db.rollback()
        return False


# =============================================================================
# CLI TEST
# =============================================================================

if __name__ == "__main__":
    print("=== QUERY CACHE TEST ===\n")

    # Test in-memory cache
    query = "hükümet eleştirisi içeren tweetler"
    filters = {"party": "CHP", "start_date": "2024-01-01"}

    # Test intent cache
    intent = {"intent_type": "search_criticism", "filters": filters}
    set_intent_cache(query, intent)
    cached_intent = get_intent_cache(query)
    print(f"Intent cache: {cached_intent is not None}")

    # Test response cache
    response = {"answer": "Test response", "tweets": []}
    set_response_cache(query, response, filters)
    cached_response = get_response_cache(query, filters)
    print(f"Response cache: {cached_response is not None}")

    # Stats
    stats = get_cache_stats()
    print(f"Cache stats: {stats}")
