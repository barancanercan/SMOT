"""
API Dependencies - Dependency Injection
"""
from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.db_config import SessionLocal
from app.core.security import TokenData, UserInDB, get_user, verify_token

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency.

    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB | None:
    """
    Get current authenticated user from token.

    Returns None if no token provided (for optional auth).
    Raises HTTPException if token is invalid.
    """
    if token is None:
        return None

    token_data: TokenData = verify_token(token)
    user = get_user(token_data.username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    return user


async def get_current_user_required(
    current_user: UserInDB | None = Depends(get_current_user)
) -> UserInDB:
    """
    Require authenticated user.

    Raises HTTPException if user is not authenticated.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def get_admin_user(
    current_user: UserInDB = Depends(get_current_user_required)
) -> UserInDB:
    """
    Require admin user.

    Raises HTTPException if user is not admin.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user
