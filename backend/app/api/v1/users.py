"""
User management endpoints — admin creates staff, manages roles, views audit logs.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import hash_password
from app.core.dependencies import require_roles, PaginationParams
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.enums import UserRole
from app.schemas.auth import (
    CreateStaffUserRequest,
    UpdateUserRequest,
    UserResponse,
    UserListResponse,
    MessageResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=UserListResponse)
async def list_users(
    role: Optional[str] = None,
    search: Optional[str] = Query(None, max_length=200),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List all users — admin only."""
    pagination = PaginationParams(page, page_size)
    query = select(User)

    if current_user.organization_id:
        query = query.where(User.organization_id == current_user.organization_id)

    if role:
        query = query.where(User.role == role)
    if search:
        query = query.where(
            User.name.ilike(f"%{search}%") | User.email.ilike(f"%{search}%")
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(User.created_at.desc()).offset(pagination.offset).limit(pagination.limit)
    result = await db.execute(query)
    users = result.scalars().all()

    return UserListResponse(
        users=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_staff_user(
    data: CreateStaffUserRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Create a staff account (admin, recruiter, hiring_manager, interviewer)."""
    # Check duplicate
    existing = await db.execute(
        select(User).where(User.email == data.email.lower())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        organization_id=current_user.organization_id,
        name=data.name,
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        role=data.role,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.flush()

    logger.info(f"Staff user created: {user.email} ({user.role})")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    data: UpdateUserRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Update a user's role or active status — admin only."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if current_user.organization_id and user.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Prevent self-deactivation
    if user.id == current_user.id and data.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)

    await db.flush()
    return user


@router.delete("/{user_id}", response_model=MessageResponse)
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a user — admin only. Does not delete data."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )

    user.is_active = False
    await db.flush()

    return MessageResponse(message=f"User {user.email} has been deactivated")


@router.get("/audit-logs")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """View audit logs — admin only."""
    pagination = PaginationParams(page, page_size)

    query = select(AuditLog)
    if current_user.organization_id:
        query = query.where(AuditLog.organization_id == current_user.organization_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(AuditLog.created_at.desc()).offset(pagination.offset).limit(pagination.limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "audit_logs": [
            {
                "id": log.id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "actor_name": log.actor.name if log.actor else None,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
    }
