"""
Security Module - JWT Authentication & Password Hashing
"""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = getattr(settings, 'secret_key', 'sam-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token payload data"""
    username: str | None = None
    scopes: list[str] = []


class UserCreate(BaseModel):
    """User creation request"""
    username: str
    password: str
    full_name: str | None = None
    is_admin: bool = False


class UserInDB(BaseModel):
    """User stored in database"""
    username: str
    hashed_password: str
    full_name: str | None = None
    is_admin: bool = False
    disabled: bool = False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create JWT access token.

    Args:
        data: Payload data (should include 'sub' for subject/username)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenData with username and scopes

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception

        scopes = payload.get("scopes", [])
        token_data = TokenData(username=username, scopes=scopes)

        return token_data

    except JWTError:
        raise credentials_exception


# Default admin user for development (should be removed in production)
DEFAULT_USERS = {
    "admin": UserInDB(
        username="admin",
        hashed_password=get_password_hash("admin123"),  # Change in production!
        full_name="Administrator",
        is_admin=True,
        disabled=False
    )
}


def get_user(username: str) -> UserInDB | None:
    """
    Get user from storage.

    Note: This is a simple in-memory implementation.
    In production, this should query a database.
    """
    if username in DEFAULT_USERS:
        return DEFAULT_USERS[username]
    return None


def authenticate_user(username: str, password: str) -> UserInDB | None:
    """
    Authenticate user with username and password.

    Returns:
        UserInDB if authentication successful, None otherwise
    """
    user = get_user(username)

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user
