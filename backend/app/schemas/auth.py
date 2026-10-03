"""
Pydantic schemas for authentication and user management.

These define request/response shapes and input validation.
Password hashes, reset tokens, and internal fields are never exposed.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, field_validator
import re


# ───────────────── Auth Request Schemas ─────────────────

class RegisterRequest(BaseModel):
    """Candidate self-registration."""
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


# ───────────────── User Response Schemas ─────────────────

class UserResponse(BaseModel):
    """Public user representation — never includes password_hash."""
    id: str
    name: str
    email: str
    role: str
    is_active: bool
    is_verified: bool
    organization_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    page_size: int


# ───────────────── Staff User Management ─────────────────

class CreateStaffUserRequest(BaseModel):
    """Admin creates staff accounts."""
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(..., pattern="^(admin|recruiter|hiring_manager|interviewer)$")


class UpdateUserRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    role: Optional[str] = Field(None, pattern="^(admin|recruiter|hiring_manager|interviewer|candidate)$")
    is_active: Optional[bool] = None


class MessageResponse(BaseModel):
    message: str
