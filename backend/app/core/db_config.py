"""
Database Configuration - SQLAlchemy Engine and Session Management
Provides centralized database connection handling
"""
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool

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

        def add_column_if_missing(table, column, col_type):
            if table_exists(table) and not column_exists(table, column):
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
                logger.info(f"Added {column} to {table}")

        # =====================================================
        # Councilors table - all possible missing columns
        # =====================================================
        add_column_if_missing("councilors", "bio", "TEXT")
        add_column_if_missing("councilors", "location", "VARCHAR(200)")
        add_column_if_missing("councilors", "website", "VARCHAR(500)")
        add_column_if_missing("councilors", "verified", "BOOLEAN DEFAULT 0")
        add_column_if_missing("councilors", "profile_image_url", "VARCHAR(500)")
        add_column_if_missing("councilors", "join_date", "VARCHAR(50)")
        add_column_if_missing("councilors", "profile_updated_at", "DATETIME")
        add_column_if_missing("councilors", "instagram_username", "VARCHAR(100)")
        add_column_if_missing("councilors", "instagram_updated_at", "DATETIME")
        add_column_if_missing("councilors", "created_at", "DATETIME")

        # =====================================================
        # Profile history table
        # =====================================================
        add_column_if_missing("profile_history", "listed_count", "INTEGER DEFAULT 0")
        add_column_if_missing("profile_history", "created_at", "DATETIME")

        # =====================================================
        # Tweets table
        # =====================================================
        add_column_if_missing("tweets", "views", "INTEGER DEFAULT 0")
        add_column_if_missing("tweets", "created_at", "DATETIME")

        conn.commit()
        conn.close()
        logger.info("Database migrations completed")
    except Exception as e:
        logger.warning(f"Migration warning (non-fatal): {e}")


def init_db():
    """Initialize database tables using ORM models"""
    # Import all models to ensure they're registered with Base.metadata
    from app.core.models import (
        Base,
    )

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
