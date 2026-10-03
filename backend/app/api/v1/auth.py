"""
Authentication endpoints — register, login, refresh, logout, password reset.

Tokens are returned in both the response body and HTTP-only cookies.
"""

from datetime import timedelta
import logging

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    decode_token,
)
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.candidate_profile import CandidateProfile
from app.models.enums import UserRole
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserResponse,
    MessageResponse,
)

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new candidate account."""
    # Check for duplicate email
    existing = await db.execute(
        select(User).where(User.email == data.email.lower())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        name=data.name,
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        role=UserRole.CANDIDATE.value,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()

    # Create empty candidate profile
    profile = CandidateProfile(user_id=user.id)
    db.add(profile)
    await db.flush()

    logger.info(f"New candidate registered: {user.email}")
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate and receive JWT tokens."""
    result = await db.execute(
        select(User).where(User.email == data.email.lower())
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    access_token = create_access_token(
        user_id=user.id,
        role=user.role,
        organization_id=user.organization_id,
    )
    refresh_token = create_refresh_token(user_id=user.id)
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    # Set HTTP-only cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=expires_in,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )

    logger.info(f"User logged in: {user.email}")
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using a valid refresh token."""
    payload = decode_token(data.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    access_token = create_access_token(
        user_id=user.id,
        role=user.role,
        organization_id=user.organization_id,
    )
    new_refresh_token = create_refresh_token(user_id=user.id)
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=expires_in,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=expires_in,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response):
    """Clear authentication cookies."""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return MessageResponse(message="Logged out successfully")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Request a password reset link. Always returns success to prevent user enumeration."""
    result = await db.execute(
        select(User).where(User.email == data.email.lower())
    )
    user = result.scalar_one_or_none()

    if user:
        token = create_password_reset_token(user.id)
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        logger.info(f"Password reset requested for: {user.email}")
        logger.info(f"Reset URL (dev only): {reset_url}")
        # In production, this would queue an email via the background worker

    return MessageResponse(
        message="If an account with that email exists, a reset link has been sent"
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using a valid reset token."""
    payload = decode_token(data.token)

    if payload.get("type") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    user.password_hash = hash_password(data.new_password)
    await db.flush()

    logger.info(f"Password reset completed for: {user.email}")
    return MessageResponse(message="Password has been reset successfully")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return current_user
