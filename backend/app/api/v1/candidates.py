"""
Candidate management endpoints — profiles, search, filtering.

Only authorized staff can search/view candidates. Candidates manage their own profiles.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, PaginationParams
from app.models.user import User
from app.models.candidate_profile import CandidateProfile
from app.models.application import Application
from app.models.enums import UserRole
from app.schemas.recruitment import (
    CandidateProfileUpdate,
    CandidateProfileResponse,
    CandidateSearchResponse,
    CandidateListResponse,
    ApplicationResponse,
    ApplicationListResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=CandidateListResponse)
async def list_candidates(
    search: Optional[str] = Query(None, max_length=200),
    skills: Optional[str] = Query(None, description="Comma-separated skills to filter by"),
    min_experience: Optional[int] = Query(None, ge=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Search and filter candidates — staff only."""
    pagination = PaginationParams(page, page_size)

    query = (
        select(User, CandidateProfile)
        .outerjoin(CandidateProfile, User.id == CandidateProfile.user_id)
        .where(User.role == UserRole.CANDIDATE.value)
    )

    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                User.name.ilike(search_filter),
                User.email.ilike(search_filter),
            )
        )

    if min_experience:
        query = query.where(CandidateProfile.experience_years >= min_experience)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(User.created_at.desc()).offset(pagination.offset).limit(pagination.limit)
    result = await db.execute(query)
    rows = result.all()

    candidates = []
    for user, profile in rows:
        candidates.append(CandidateSearchResponse(
            id=profile.id if profile else user.id,
            user_id=user.id,
            name=user.name,
            email=user.email,
            phone=profile.phone if profile else None,
            location=profile.location if profile else None,
            skills=profile.skills if profile else None,
            experience_years=profile.experience_years if profile else None,
            created_at=user.created_at,
        ))

    return CandidateListResponse(
        candidates=candidates,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/me/profile", response_model=CandidateProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current candidate's profile."""
    if current_user.role != UserRole.CANDIDATE.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a candidate")

    result = await db.execute(
        select(CandidateProfile).where(CandidateProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        # Auto-create if missing
        profile = CandidateProfile(user_id=current_user.id)
        db.add(profile)
        await db.flush()

    return profile


@router.patch("/me/profile", response_model=CandidateProfileResponse)
async def update_my_profile(
    data: CandidateProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current candidate's profile."""
    if current_user.role != UserRole.CANDIDATE.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a candidate")

    result = await db.execute(
        select(CandidateProfile).where(CandidateProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        profile = CandidateProfile(user_id=current_user.id)
        db.add(profile)
        await db.flush()

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    await db.flush()
    return profile


@router.get("/{candidate_id}", response_model=CandidateProfileResponse)
async def get_candidate(
    candidate_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a candidate's profile — staff or the candidate themselves."""
    if (
        current_user.role == UserRole.CANDIDATE.value
        and current_user.id != candidate_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    user_result = await db.execute(
        select(User).where(User.id == candidate_id, User.role == UserRole.CANDIDATE.value)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    result = await db.execute(
        select(CandidateProfile).where(CandidateProfile.user_id == candidate_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = CandidateProfile(user_id=candidate_id)
        db.add(profile)
        await db.flush()

    res = CandidateProfileResponse.model_validate(profile)
    res.name = user.name
    res.email = user.email
    return res


@router.get("/{candidate_id}/applications", response_model=ApplicationListResponse)
async def get_candidate_applications(
    candidate_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all applications for a specific candidate — staff or the candidate themselves."""
    if (
        current_user.role == UserRole.CANDIDATE.value
        and current_user.id != candidate_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    pagination = PaginationParams(page, page_size)

    query = select(Application).where(Application.candidate_id == candidate_id)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Application.applied_at.desc()).offset(pagination.offset).limit(pagination.limit)
    result = await db.execute(query)
    applications = result.scalars().all()

    app_list = []
    for app in applications:
        app_list.append(ApplicationResponse(
            id=app.id,
            job_id=app.job_id,
            candidate_id=app.candidate_id,
            resume_id=app.resume_id,
            status=app.status,
            cover_letter=app.cover_letter,
            applied_at=app.applied_at,
            updated_at=app.updated_at,
            job_title=app.job.title if app.job else None,
            candidate_name=app.candidate.name if app.candidate else None,
        ))

    return ApplicationListResponse(
        applications=app_list,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )
