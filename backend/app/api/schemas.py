"""
API Response Schemas - Pagination and Common Models
"""
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination query parameters"""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def create(cls, items: list[T], total: int, page: int, page_size: int):
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


# User schemas
class UserBase(BaseModel):
    username: str
    name: str
    party: str | None = None
    district: str | None = None


class UserListItem(UserBase):
    id: int
    tweet_count: int | None = None


class UserDetail(UserBase):
    id: int
    tweet_count: int
    profile: dict | None = None


# Tweet schemas
class TweetBase(BaseModel):
    id: int
    username: str
    tweet_text: str
    tweet_date: str | None = None
    likes: int = 0
    replies: int = 0
    retweets: int = 0
    views: int = 0


class TweetWithEngagement(TweetBase):
    engagement: int = 0


# Analytics schemas
class PartyStats(BaseModel):
    party: str
    member_count: int
    total_followers: int = 0
    total_tweets: int = 0
    total_likes: int = 0


class EngagementStats(BaseModel):
    username: str
    name: str
    party: str | None = None
    tweet_count: int = 0
    total_likes: int = 0
    total_retweets: int = 0
    total_engagement: int = 0


class DistrictStats(BaseModel):
    district: str
    member_count: int
