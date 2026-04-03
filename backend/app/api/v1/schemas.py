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


# =============================================================================
# Chat with Tweets Models
# =============================================================================

from typing import Any, Dict

class ChatQueryRequest(BaseModel):
    """Request model for chat query"""
    query: str
    max_results: int = 20
    include_summary: bool = True
    platform: Platform = Platform.TWITTER
    party_filter: Optional[str] = None  # Filter tweets by party (e.g., "CHP", "AK Parti")


class ChatTweetResult(BaseModel):
    """Tweet result in chat response"""
    id: int
    username: str
    name: Optional[str] = None
    party: Optional[str] = None
    tweet_text: str
    tweet_date: Optional[str] = None
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    views: int = 0
    relevance_score: float = 0.0
    # Classification fields (for criticism search)
    criticism_topic: Optional[str] = None
    criticism_explanation: Optional[str] = None


class ChatSummary(BaseModel):
    """Summary section of chat response"""
    total_found: int = 0
    top_topics: List[str] = []
    sentiment: str = "notr"  # olumlu, olumsuz, notr
    most_active_users: List[str] = []
    date_range: Optional[str] = None


class ChatQueryResponse(BaseModel):
    """Response model for chat query"""
    query: str
    answer: str
    summary: ChatSummary
    tweets: List[ChatTweetResult] = []
    filters_applied: Dict[str, Any] = {}
    confidence_score: float = 0.0
    execution_time_ms: float = 0.0
    cached: bool = False
    intent_type: str = "search_topic"


class ChatSuggestionsResponse(BaseModel):
    """Response model for suggested questions"""
    suggestions: List[str] = []


# =============================================================================
# Chat Session Models (v5.0)
# =============================================================================

class CreateSessionRequest(BaseModel):
    """Request model for creating a new chat session"""
    platform: Platform = Platform.TWITTER
    party_filter: Optional[str] = None
    title: Optional[str] = None


class CreateSessionResponse(BaseModel):
    """Response model for created session"""
    id: str
    title: str
    platform: str
    party_filter: Optional[str]
    created_at: str
    message_count: int = 0


class ChatMessageResponse(BaseModel):
    """Response model for a single chat message"""
    id: int
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: str


class SessionDetailResponse(BaseModel):
    """Response model for session with messages"""
    id: str
    title: str
    platform: str
    party_filter: Optional[str]
    created_at: str
    updated_at: Optional[str]
    message_count: int
    messages: List[ChatMessageResponse] = []


class SessionListResponse(BaseModel):
    """Response model for list of sessions"""
    sessions: List[CreateSessionResponse]
    total: int


class UpdateSessionRequest(BaseModel):
    """Request model for updating a session"""
    title: Optional[str] = None
    platform: Optional[Platform] = None
    party_filter: Optional[str] = None


class AddMessageRequest(BaseModel):
    """Request model for adding a message to a session"""
    role: str  # "user" or "assistant"
    content: str
    metadata: Optional[Dict[str, Any]] = None
