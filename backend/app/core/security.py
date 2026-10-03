"""
Security utilities: password hashing, JWT token creation and verification.

Uses bcrypt for password hashing and PyJWT for token management.
Tokens are stored in HTTP-only cookies in production.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import uuid

import bcrypt
import jwt
from fastapi import HTTPException, status

from app.core.config import get_settings

settings = get_settings()


# ───────────────────── Password Hashing ─────────────────────

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ───────────────────── JWT Tokens ─────────────────────

def create_access_token(
    user_id: str,
    role: str,
    organization_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

    payload = {
        "sub": user_id,
        "role": role,
        "org": organization_id,
        "type": "access",
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    user_id: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT refresh token with longer expiry."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))

    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT token.

    Raises HTTPException on invalid or expired tokens.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def create_password_reset_token(user_id: str) -> str:
    """Create a short-lived token for password reset (15 minutes)."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "password_reset",
        "iat": now,
        "exp": now + timedelta(minutes=15),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_email_verification_token(user_id: str) -> str:
    """Create a token for email verification (24 hours)."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "email_verification",
        "iat": now,
        "exp": now + timedelta(hours=24),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
