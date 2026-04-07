"""
Chat API Routes - Chat with Tweets functionality v7.0

Allows users to query social media content using natural language.
Hybrid RAG: BM25 + Dense Embeddings + RRF + Cross-Encoder Reranking.
"""
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_db
from app.api.v1.schemas import (
    AddMessageRequest,
    ChatMessageResponse,
    ChatQueryRequest,
    ChatQueryResponse,
    ChatSuggestionsResponse,
    ChatSummary,
    ChatTweetResult,
    # Session schemas
    CreateSessionRequest,
    CreateSessionResponse,
    SessionDetailResponse,
    SessionListResponse,
    UpdateSessionRequest,
)
from app.core.rate_limit import RateLimits, limiter
from app.services.chat.chat_handler import ChatHandler
from app.services.chat.query_cache import clear_cache as clear_query_cache
from app.services.chat.session_manager import (
    SessionManager,
)

logger = logging.getLogger("Chat")
router = APIRouter()


@router.post("/query", response_model=ChatQueryResponse)
@limiter.limit(RateLimits.HEAVY)
async def chat_query(
    request: Request,
    body: ChatQueryRequest,
    db: DBSession = Depends(get_db)
):
    """
    Process a natural language query about tweets.

    This endpoint allows users to ask questions in Turkish about tweets
    in the database. The system uses AI to understand the intent and
    search for relevant tweets.

    Examples:
    - "Belediye hizmetleriyle atilmis tweetleri getir"
    - "01-01-2024 tarihinden 31-03-2024 tarihine kadar atilmis tweetleri getir"
    - "Atilla Celik'in attigi tweetlerin konulari neledir"
    - "Cumhurbaskanina elestiri iceren tweetleri getir"
    - "@chp kullanicisini rt yapan tweetleri getir"

    Args:
        query: Turkish natural language query (min 3 characters)
        max_results: Maximum number of tweets to return (1-100, default 20)
        include_summary: Whether to include AI summary (default true)
        platform: Platform to search (twitter only for now)

    Returns:
        ChatQueryResponse with answer, summary, and matching tweets

    Rate limit: 5 requests per minute
    """
    query_text = body.query.strip()

    if len(query_text) < 3:
        raise HTTPException(
            status_code=400,
            detail="Sorgu en az 3 karakter olmali"
        )

    if len(query_text) > 500:
        raise HTTPException(
            status_code=400,
            detail="Sorgu en fazla 500 karakter olmali"
        )

    if body.max_results < 1:
        body.max_results = 1
    elif body.max_results > 100:
        body.max_results = 100

    try:
        logger.info(f"Processing chat query: {query_text[:50]}...")
        logger.info(f"Party filter: '{body.party_filter}', Platform: '{body.platform}'")

        handler = ChatHandler(db)

        # Run blocking ML operations in thread pool to avoid blocking event loop
        result = await asyncio.to_thread(
            handler.process_query,
            query=query_text,
            max_results=body.max_results,
            include_summary=body.include_summary,
            party_filter=body.party_filter,
            platform=body.platform.value if body.platform else "twitter",
        )

        # Convert tweets to response model
        tweet_results = [
            ChatTweetResult(
                id=t["id"],
                username=t["username"],
                name=t.get("name"),
                party=t.get("party"),
                tweet_text=t["tweet_text"],
                tweet_date=t.get("tweet_date"),
                likes=t.get("likes", 0),
                retweets=t.get("retweets", 0),
                replies=t.get("replies", 0),
                views=t.get("views", 0),
                relevance_score=t.get("relevance_score", 0.0),
                criticism_topic=t.get("criticism_topic"),
                criticism_explanation=t.get("criticism_explanation")
            )
            for t in result.tweets
        ]

        # Build summary
        summary_data = result.summary or {}
        summary = ChatSummary(
            total_found=summary_data.get("total_found", len(result.tweets)),
            top_topics=summary_data.get("top_topics", []),
            sentiment=summary_data.get("sentiment", "notr"),
            most_active_users=summary_data.get("most_active_users", []),
            date_range=summary_data.get("date_range")
        )

        logger.info(
            f"Chat query completed: {len(tweet_results)} tweets, "
            f"{result.execution_time_ms:.0f}ms"
        )

        return ChatQueryResponse(
            query=result.query,
            answer=result.answer,
            summary=summary,
            tweets=tweet_results,
            filters_applied=result.filters_applied,
            confidence_score=result.confidence_score,
            execution_time_ms=result.execution_time_ms,
            cached=result.cached,
            intent_type=result.intent_type
        )

    except Exception as e:
        logger.error(f"Chat query error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Sorgu islenirken hata olustu: {str(e)}"
        )


@router.get("/suggestions", response_model=ChatSuggestionsResponse)
@limiter.limit(RateLimits.STANDARD)
async def get_suggestions(
    request: Request,
    platform: str | None = Query(default="twitter", description="Platform filter (twitter, instagram, both)"),
    party: str | None = Query(default=None, description="Party filter for context-aware suggestions"),
    db: DBSession = Depends(get_db)
):
    """
    Get suggested questions for the chat interface.

    Returns a list of example queries that users can click to try.
    Suggestions are dynamic based on platform and party filter.

    Args:
        platform: Platform to search (twitter, instagram, both)
        party: Selected party filter for context-aware suggestions

    Rate limit: 30 requests per minute
    """
    def _get_suggestions():
        h = ChatHandler(db)
        return h.get_suggested_questions(
            platform=platform or "twitter",
            party_filter=party
        )

    suggestions = await asyncio.to_thread(_get_suggestions)
    return ChatSuggestionsResponse(suggestions=suggestions)


@router.get("/health")
async def chat_health():
    """
    Health check for chat service.

    Returns status of the chat service and its dependencies.
    """
    from app.services.chat.intent_parser import IntentParser
    from app.services.chat.response_generator import ResponseGenerator

    try:
        intent_parser = IntentParser()
        response_generator = ResponseGenerator()

        return {
            "status": "healthy",
            "llm_available": intent_parser.llm_available and response_generator.llm_available,
            "services": {
                "intent_parser": "ok",
                "response_generator": "ok",
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "llm_available": False,
            "error": str(e),
            "services": {
                "intent_parser": "error",
                "response_generator": "error",
            }
        }


# =============================================================================
# Session Management Endpoints (v5.0)
# =============================================================================

@router.post("/sessions", response_model=CreateSessionResponse)
@limiter.limit(RateLimits.STANDARD)
async def create_session(
    request: Request,
    body: CreateSessionRequest,
    db: DBSession = Depends(get_db)
):
    """
    Create a new chat session.

    Creates a persistent chat session that can store conversation history.
    The session can be configured with platform and party filters.

    Args:
        platform: Platform filter (twitter, instagram, both)
        party_filter: Optional party filter
        title: Optional title (auto-generated if not provided)

    Returns:
        CreateSessionResponse with session details
    """
    try:
        manager = SessionManager(db)
        session = manager.create_session(
            platform=body.platform.value if body.platform else "twitter",
            party_filter=body.party_filter,
            title=body.title
        )

        return CreateSessionResponse(
            id=session.id,
            title=session.title,
            platform=session.platform,
            party_filter=session.party_filter,
            created_at=session.created_at.isoformat(),
            message_count=0
        )
    except Exception as e:
        logger.error(f"Create session error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Oturum olusturulamadi: {str(e)}"
        )


@router.get("/sessions", response_model=SessionListResponse)
@limiter.limit(RateLimits.STANDARD)
async def list_sessions(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    db: DBSession = Depends(get_db)
):
    """
    List all chat sessions.

    Returns sessions ordered by most recent first.

    Args:
        limit: Maximum number of sessions to return (default 20)
        offset: Number of sessions to skip

    Returns:
        SessionListResponse with list of sessions
    """
    try:
        manager = SessionManager(db)
        sessions = manager.list_sessions(limit=limit, offset=offset)

        return SessionListResponse(
            sessions=[
                CreateSessionResponse(
                    id=s.id,
                    title=s.title,
                    platform=s.platform,
                    party_filter=s.party_filter,
                    created_at=s.created_at.isoformat() if s.created_at else "",
                    message_count=len(s.messages) if s.messages else 0
                )
                for s in sessions
            ],
            total=len(sessions)
        )
    except Exception as e:
        logger.error(f"List sessions error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Oturumlar listelenirken hata: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
@limiter.limit(RateLimits.STANDARD)
async def get_session(
    request: Request,
    session_id: str,
    db: DBSession = Depends(get_db)
):
    """
    Get a session with its messages.

    Returns full session details including message history.

    Args:
        session_id: Session UUID

    Returns:
        SessionDetailResponse with session and messages
    """
    try:
        manager = SessionManager(db)
        session = manager.get_session(session_id)

        if not session:
            raise HTTPException(
                status_code=404,
                detail="Oturum bulunamadi"
            )

        return SessionDetailResponse(
            id=session.id,
            title=session.title,
            platform=session.platform,
            party_filter=session.party_filter,
            created_at=session.created_at.isoformat() if session.created_at else "",
            updated_at=session.updated_at.isoformat() if session.updated_at else None,
            message_count=len(session.messages) if session.messages else 0,
            messages=[
                ChatMessageResponse(
                    id=msg.id,
                    role=msg.role,
                    content=msg.content,
                    metadata=msg.message_metadata,
                    created_at=msg.created_at.isoformat() if msg.created_at else ""
                )
                for msg in session.messages
            ] if session.messages else []
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get session error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Oturum getirilirken hata: {str(e)}"
        )


@router.delete("/sessions/{session_id}")
@limiter.limit(RateLimits.STANDARD)
async def delete_session(
    request: Request,
    session_id: str,
    db: DBSession = Depends(get_db)
):
    """
    Delete a chat session.

    Removes the session and all its messages.

    Args:
        session_id: Session UUID

    Returns:
        Success message
    """
    try:
        manager = SessionManager(db)
        deleted = manager.delete_session(session_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Oturum bulunamadi"
            )

        return {"success": True, "message": "Oturum silindi"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete session error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Oturum silinirken hata: {str(e)}"
        )


@router.patch("/sessions/{session_id}", response_model=CreateSessionResponse)
@limiter.limit(RateLimits.STANDARD)
async def update_session(
    request: Request,
    session_id: str,
    body: UpdateSessionRequest,
    db: DBSession = Depends(get_db)
):
    """
    Update a chat session.

    Updates session properties like title, platform, or party filter.

    Args:
        session_id: Session UUID
        title: New title (optional)
        platform: New platform filter (optional)
        party_filter: New party filter (optional)

    Returns:
        Updated session details
    """
    try:
        manager = SessionManager(db)
        session = manager.update_session(
            session_id=session_id,
            title=body.title,
            platform=body.platform.value if body.platform else None,
            party_filter=body.party_filter
        )

        if not session:
            raise HTTPException(
                status_code=404,
                detail="Oturum bulunamadi"
            )

        return CreateSessionResponse(
            id=session.id,
            title=session.title,
            platform=session.platform,
            party_filter=session.party_filter,
            created_at=session.created_at.isoformat() if session.created_at else "",
            message_count=len(session.messages) if session.messages else 0
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update session error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Oturum guncellenirken hata: {str(e)}"
        )


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
@limiter.limit(RateLimits.STANDARD)
async def add_message(
    request: Request,
    session_id: str,
    body: AddMessageRequest,
    db: DBSession = Depends(get_db)
):
    """
    Add a message to a chat session.

    Adds a user or assistant message to the session history.

    Args:
        session_id: Session UUID
        role: "user" or "assistant"
        content: Message content
        metadata: Optional metadata

    Returns:
        Created message details
    """
    if body.role not in ["user", "assistant"]:
        raise HTTPException(
            status_code=400,
            detail="Rol 'user' veya 'assistant' olmali"
        )

    try:
        manager = SessionManager(db)
        message = manager.add_message(
            session_id=session_id,
            role=body.role,
            content=body.content,
            metadata=body.metadata
        )

        if not message:
            raise HTTPException(
                status_code=404,
                detail="Oturum bulunamadi"
            )

        return ChatMessageResponse(
            id=message.id,
            role=message.role,
            content=message.content,
            metadata=message.message_metadata,
            created_at=message.created_at.isoformat() if message.created_at else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add message error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Mesaj eklenirken hata: {str(e)}"
        )


@router.post("/cache/clear")
async def clear_cache():
    """Clear chat query cache."""
    clear_query_cache()
    logger.info("Chat cache cleared")
    return {"status": "ok", "message": "Cache temizlendi"}
