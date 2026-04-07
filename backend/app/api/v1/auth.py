"""
Authentication API Routes
"""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import UserInDB, get_current_user_required
from app.core.rate_limit import RateLimits, limiter
from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    Token,
    authenticate_user,
    create_access_token,
)

router = APIRouter()


@router.post("/token", response_model=Token)
@limiter.limit(RateLimits.AUTH)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login.

    Returns JWT access token for valid credentials.
    """
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "scopes": ["read", "write"] if user.is_admin else ["read"]},
        expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me")
async def get_current_user_info(
    current_user: UserInDB = Depends(get_current_user_required)
):
    """
    Get current authenticated user information.
    """
    return {
        "username": current_user.username,
        "full_name": current_user.full_name,
        "is_admin": current_user.is_admin,
        "disabled": current_user.disabled
    }


@router.post("/verify")
async def verify_token_endpoint(
    current_user: UserInDB = Depends(get_current_user_required)
):
    """
    Verify if current token is valid.

    Returns user info if token is valid.
    """
    return {
        "valid": True,
        "username": current_user.username,
        "is_admin": current_user.is_admin
    }
