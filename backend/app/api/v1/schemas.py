"""
Shared API Schemas and Enums
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class Platform(str, Enum):
    """Platform types for multi-platform support"""
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    BOTH = "both"


# =============================================================================
# Request Models with Platform Support
# =============================================================================

class GenerateReportRequest(BaseModel):
    """Request model for generating user reports"""
    username: str
    use_llm: bool = True
    force_refresh: bool = False
    platform: Platform = Platform.TWITTER


class PartyReportRequest(BaseModel):
    """Request model for generating party reports"""
    party: str
    use_llm: bool = False
    platform: Platform = Platform.TWITTER


class MultiUserReportRequest(BaseModel):
    """Request model for multi-user reports"""
    usernames: List[str]
    use_llm: bool = True
    platform: Platform = Platform.TWITTER


class ComparisonRequest(BaseModel):
    """Request model for user comparison"""
    usernames: List[str]
    platform: Platform = Platform.TWITTER


class PartyComparisonRequest(BaseModel):
    """Request model for party comparison"""
    parties: List[str]
    platform: Platform = Platform.TWITTER


# =============================================================================
# Response Models
# =============================================================================

class InstagramPostResponse(BaseModel):
    """Response model for Instagram post"""
    id: int
    username: str
    caption: Optional[str]
    post_date: Optional[str]
    post_url: Optional[str]
    likes: int = 0
    comments: int = 0
    is_video: bool = False


class InstagramProfileResponse(BaseModel):
    """Response model for Instagram profile"""
    username: str
    full_name: Optional[str]
    bio: Optional[str]
    followers: int = 0
    following: int = 0
    posts_count: int = 0
    date: Optional[str]


class DashboardStatsResponse(BaseModel):
    """Response model for dashboard statistics"""
    # Twitter stats
    total_tweets: int = 0
    total_original: int = 0
    total_retweets: int = 0
    total_retweets_count: int = 0
    total_councilors: int = 0
    total_profiles: int = 0
    active_users: int = 0
    total_likes: int = 0
    total_views: int = 0
    total_replies: int = 0
    # Instagram stats (when applicable)
    total_posts: Optional[int] = None
    total_instagram_profiles: Optional[int] = None
    total_instagram_likes: Optional[int] = None
    total_comments: Optional[int] = None
    instagram_active_users: Optional[int] = None
    # Platform indicator
    platform: str = "twitter"
