"""
Database Configuration - SQLAlchemy Engine and Session Management
Provides centralized database connection handling
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger("Database")

# Create engine with SQLite-specific settings
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # SQLite works best with StaticPool
    echo=False  # Set to True for SQL query logging
)

# Enable foreign key constraints for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Thread-local session
ScopedSession = scoped_session(SessionLocal)


def get_session() -> Session:
    """
    Get a new database session
    
    Returns:
        Session instance
    """
    return SessionLocal()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Provide a transactional scope for database operations
    
    Usage:
        with session_scope() as session:
            session.add(obj)
            # Auto-commits on success, rolls back on exception
    
    Yields:
        Session instance
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database transaction failed: {e}")
        raise
    finally:
        session.close()


def _run_migrations():
    """Run database migrations to add missing columns"""
    import sqlite3

    # Only for SQLite
    if not settings.database_url.startswith("sqlite"):
        return

    db_path = settings.database_url.replace("sqlite:///", "")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        def column_exists(table, column):
            cursor.execute(f"PRAGMA table_info({table})")
            return column in [row[1] for row in cursor.fetchall()]

        def table_exists(table):
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            return cursor.fetchone() is not None

        # Add missing columns to councilors
        if table_exists("councilors"):
            if not column_exists("councilors", "instagram_username"):
                cursor.execute("ALTER TABLE councilors ADD COLUMN instagram_username VARCHAR(100)")
                logger.info("Added instagram_username to councilors")
            if not column_exists("councilors", "instagram_updated_at"):
                cursor.execute("ALTER TABLE councilors ADD COLUMN instagram_updated_at DATETIME")
                logger.info("Added instagram_updated_at to councilors")

        # Add listed_count to profile_history
        if table_exists("profile_history"):
            if not column_exists("profile_history", "listed_count"):
                cursor.execute("ALTER TABLE profile_history ADD COLUMN listed_count INTEGER DEFAULT 0")
                logger.info("Added listed_count to profile_history")

        conn.commit()
        conn.close()
        logger.info("Database migrations completed")
    except Exception as e:
        logger.warning(f"Migration warning (non-fatal): {e}")


def init_db():
    """Initialize database tables using ORM models"""
    from app.core.models import Base

    logger.info("Creating database tables with SQLAlchemy ORM...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")

    # Run migrations for existing tables
    _run_migrations()


def get_scoped_session() -> scoped_session:
    """
    Get thread-local scoped session
    Useful for multi-threaded applications
    
    Returns:
        Scoped session instance
    """
    return ScopedSession
