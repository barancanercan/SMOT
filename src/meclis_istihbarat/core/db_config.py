"""
Database Configuration - SQLAlchemy Engine and Session Management
Provides centralized database connection handling
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
from meclis_istihbarat.core.config import DB_PATH
from meclis_istihbarat.utils.logger import get_logger

logger = get_logger("Database")

# Create engine with SQLite-specific settings
engine = create_engine(
    f"sqlite:///{DB_PATH}",
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


def init_db():
    """Initialize database tables using ORM models"""
    from meclis_istihbarat.core.models import Base
    
    logger.info("Creating database tables with SQLAlchemy ORM...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def get_scoped_session() -> scoped_session:
    """
    Get thread-local scoped session
    Useful for multi-threaded applications
    
    Returns:
        Scoped session instance
    """
    return ScopedSession
