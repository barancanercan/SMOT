"""
Shared API Schemas and Enums
"""
from enum import Enum
from typing import Any

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
    usernames: list[str]
    use_llm: bool = True
    platform: Platform = Platform.TWITTER


class ComparisonRequest(BaseModel):
    """Request model for user comparison"""
    usernames: list[str]
    platform: Platform = Platform.TWITTER


class PartyComparisonRequest(BaseModel):
    """Request model for party comparison"""
    parties: list[str]
    platform: Platform = Platform.TWITTER


# =============================================================================
# Response Models
# =============================================================================

class InstagramPostResponse(BaseModel):
    """Response model for Instagram post"""
    id: int
    username: str
    caption: str | None
    post_date: str | None
    post_url: str | None
    likes: int = 0
    comments: int = 0
    is_video: bool = False


class InstagramProfileResponse(BaseModel):
    """Response model for Instagram profile"""
    username: str
    full_name: str | None
    bio: str | None
    followers: int = 0
    following: int = 0
    posts_count: int = 0
    date: str | None


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
    total_posts: int | None = None
    total_instagram_profiles: int | None = None
    total_instagram_likes: int | None = None
    total_comments: int | None = None
    instagram_active_users: int | None = None
    # Platform indicator
    platform: str = "twitter"


# =============================================================================
# Chat with Tweets Models
# =============================================================================

class ChatQueryRequest(BaseModel):
    """Request model for chat query"""
    query: str
    max_results: int = 20
    include_summary: bool = True
    platform: Platform = Platform.TWITTER
    party_filter: str | None = None  # Filter tweets by party (e.g., "CHP", "AK Parti")


class ChatTweetResult(BaseModel):
    """Tweet result in chat response"""
    id: int
    username: str
    name: str | None = None
    party: str | None = None
    tweet_text: str
    tweet_date: str | None = None
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    views: int = 0
    relevance_score: float = 0.0
    # Classification fields (for criticism search)
    criticism_topic: str | None = None
    criticism_explanation: str | None = None


class ChatSummary(BaseModel):
    """Summary section of chat response"""
    total_found: int = 0
    top_topics: list[str] = []
    sentiment: str = "notr"  # olumlu, olumsuz, notr
    most_active_users: list[str] = []
    date_range: str | None = None


class ChatQueryResponse(BaseModel):
    """Response model for chat query"""
    query: str
    answer: str
    summary: ChatSummary
    tweets: list[ChatTweetResult] = []
    filters_applied: dict[str, Any] = {}
    confidence_score: float = 0.0
    execution_time_ms: float = 0.0
    cached: bool = False
    intent_type: str = "search_topic"


class ChatSuggestionsResponse(BaseModel):
    """Response model for suggested questions"""
    suggestions: list[str] = []


# =============================================================================
# Chat Session Models (v5.0)
# =============================================================================

class CreateSessionRequest(BaseModel):
    """Request model for creating a new chat session"""
    platform: Platform = Platform.TWITTER
    party_filter: str | None = None
    title: str | None = None


class CreateSessionResponse(BaseModel):
    """Response model for created session"""
    id: str
    title: str
    platform: str
    party_filter: str | None
    created_at: str
    message_count: int = 0


class ChatMessageResponse(BaseModel):
    """Response model for a single chat message"""
    id: int
    role: str
    content: str
    metadata: dict[str, Any] | None = None
    created_at: str


class SessionDetailResponse(BaseModel):
    """Response model for session with messages"""
    id: str
    title: str
    platform: str
    party_filter: str | None
    created_at: str
    updated_at: str | None
    message_count: int
    messages: list[ChatMessageResponse] = []


class SessionListResponse(BaseModel):
    """Response model for list of sessions"""
    sessions: list[CreateSessionResponse]
    total: int


class UpdateSessionRequest(BaseModel):
    """Request model for updating a session"""
    title: str | None = None
    platform: Platform | None = None
    party_filter: str | None = None


class AddMessageRequest(BaseModel):
    """Request model for adding a message to a session"""
    role: str  # "user" or "assistant"
    content: str
    metadata: dict[str, Any] | None = None
