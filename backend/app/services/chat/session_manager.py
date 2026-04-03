#!/usr/bin/env python3
"""
Session Manager - Chat Session CRUD Operations

Provides persistent chat session management:
- Create new sessions
- List existing sessions
- Get session with messages
- Delete sessions
- Add messages to sessions
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from app.core.models import ChatSession, ChatMessage
from app.utils.logger import get_logger

logger = get_logger("SessionManager")


class SessionManager:
    """
    Manages chat sessions and messages.

    Features:
    - Auto-generate session title from first message
    - Persist platform and party filter settings
    - Ordered message history
    """

    MAX_TITLE_LENGTH = 100
    MAX_SESSIONS_PER_USER = 50  # Limit total sessions

    def __init__(self, db: Session):
        """Initialize session manager with database session."""
        self.db = db

    def create_session(
        self,
        platform: str = "twitter",
        party_filter: Optional[str] = None,
        title: Optional[str] = None
    ) -> ChatSession:
        """
        Create a new chat session.

        Args:
            platform: Platform filter (twitter, instagram, both)
            party_filter: Optional party filter
            title: Optional title (auto-generated if not provided)

        Returns:
            Created ChatSession
        """
        session_id = str(uuid.uuid4())
        default_title = title or "Yeni Sohbet"

        session = ChatSession(
            id=session_id,
            title=default_title,
            platform=platform,
            party_filter=party_filter,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        logger.info(f"Created session: {session_id}")
        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Get a session by ID with its messages.

        Args:
            session_id: Session UUID

        Returns:
            ChatSession or None if not found
        """
        return self.db.query(ChatSession).filter(
            ChatSession.id == session_id
        ).first()

    def list_sessions(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> List[ChatSession]:
        """
        List all sessions ordered by most recent first.

        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            List of ChatSession objects
        """
        return self.db.query(ChatSession).order_by(
            ChatSession.updated_at.desc()
        ).offset(offset).limit(limit).all()

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its messages.

        Args:
            session_id: Session UUID

        Returns:
            True if deleted, False if not found
        """
        session = self.get_session(session_id)
        if not session:
            return False

        self.db.delete(session)
        self.db.commit()

        logger.info(f"Deleted session: {session_id}")
        return True

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ChatMessage]:
        """
        Add a message to a session.

        If this is the first user message, auto-generate session title.

        Args:
            session_id: Session UUID
            role: "user" or "assistant"
            content: Message content
            metadata: Optional metadata (filters, summary, etc.)

        Returns:
            Created ChatMessage or None if session not found
        """
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"Session not found: {session_id}")
            return None

        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            message_metadata=metadata,
            created_at=datetime.utcnow()
        )

        self.db.add(message)

        # Update session timestamp
        session.updated_at = datetime.utcnow()

        # Auto-generate title from first user message
        if role == "user" and session.title == "Yeni Sohbet":
            session.title = self._generate_title(content)
            logger.info(f"Auto-generated title: {session.title}")

        self.db.commit()
        self.db.refresh(message)

        return message

    def get_messages(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[ChatMessage]:
        """
        Get messages for a session.

        Args:
            session_id: Session UUID
            limit: Maximum messages to return

        Returns:
            List of ChatMessage objects ordered by created_at
        """
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(
            ChatMessage.created_at.asc()
        ).limit(limit).all()

    def update_session(
        self,
        session_id: str,
        title: Optional[str] = None,
        platform: Optional[str] = None,
        party_filter: Optional[str] = None
    ) -> Optional[ChatSession]:
        """
        Update session properties.

        Args:
            session_id: Session UUID
            title: New title (optional)
            platform: New platform filter (optional)
            party_filter: New party filter (optional)

        Returns:
            Updated ChatSession or None if not found
        """
        session = self.get_session(session_id)
        if not session:
            return None

        if title is not None:
            session.title = title[:self.MAX_TITLE_LENGTH]
        if platform is not None:
            session.platform = platform
        if party_filter is not None:
            session.party_filter = party_filter if party_filter else None

        session.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(session)

        return session

    def _generate_title(self, first_message: str) -> str:
        """
        Generate a session title from the first user message.

        Takes the first meaningful part of the message.

        Args:
            first_message: First user message content

        Returns:
            Generated title string
        """
        # Clean and truncate
        title = first_message.strip()

        # Remove filter tags like [CHP, X]
        if title.endswith("]"):
            bracket_start = title.rfind("[")
            if bracket_start > 0:
                title = title[:bracket_start].strip()

        # Truncate to max length
        if len(title) > self.MAX_TITLE_LENGTH:
            # Try to break at word boundary
            truncated = title[:self.MAX_TITLE_LENGTH]
            last_space = truncated.rfind(" ")
            if last_space > self.MAX_TITLE_LENGTH - 20:
                title = truncated[:last_space] + "..."
            else:
                title = truncated + "..."
        elif len(title) == 0:
            title = "Yeni Sohbet"

        return title

    def cleanup_old_sessions(self, keep_count: int = 20) -> int:
        """
        Remove oldest sessions if limit exceeded.

        Args:
            keep_count: Number of sessions to keep

        Returns:
            Number of sessions deleted
        """
        total = self.db.query(ChatSession).count()
        if total <= keep_count:
            return 0

        # Get IDs of sessions to delete (oldest first)
        to_delete = self.db.query(ChatSession.id).order_by(
            ChatSession.updated_at.asc()
        ).limit(total - keep_count).all()

        delete_ids = [s.id for s in to_delete]

        self.db.query(ChatSession).filter(
            ChatSession.id.in_(delete_ids)
        ).delete(synchronize_session='fetch')

        self.db.commit()

        logger.info(f"Cleaned up {len(delete_ids)} old sessions")
        return len(delete_ids)


# =============================================================================
# Helper functions for API endpoints
# =============================================================================

def session_to_dict(session: ChatSession, include_messages: bool = False) -> Dict[str, Any]:
    """
    Convert ChatSession to dictionary for API response.

    Args:
        session: ChatSession object
        include_messages: Whether to include message list

    Returns:
        Dictionary representation
    """
    data = {
        "id": session.id,
        "title": session.title,
        "platform": session.platform,
        "party_filter": session.party_filter,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        "message_count": len(session.messages) if session.messages else 0,
    }

    if include_messages and session.messages:
        data["messages"] = [
            message_to_dict(msg) for msg in session.messages
        ]

    return data


def message_to_dict(message: ChatMessage) -> Dict[str, Any]:
    """
    Convert ChatMessage to dictionary for API response.

    Args:
        message: ChatMessage object

    Returns:
        Dictionary representation
    """
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "metadata": message.message_metadata,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }
