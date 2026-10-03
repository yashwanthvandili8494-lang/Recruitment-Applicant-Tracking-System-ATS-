"""
Application endpoints — apply, track, status transitions, history.

Enforces valid status transitions and duplicate prevention.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, PaginationParams
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.models.application_status_history import ApplicationStatusHistory
from app.models.enums import (
    UserRole, JobStatus, ApplicationStatus, APPLICATION_STATUS_TRANSITIONS,
)
from app.schemas.recruitment import (
    ApplicationCreateRequest,
    ApplicationStatusUpdateRequest,
    ApplicationResponse,
    ApplicationListResponse,
    StatusHistoryResponse,
    CandidateApplicationStatusResponse,
)
from app.schemas.auth import MessageResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# Candidate-friendly status labels
STATUS_DISPLAY = {
    "applied": "Application Received",
    "under_review": "Under Review",
    "shortlisted": "Shortlisted",
    "interview_scheduled": "Interview Scheduled",
    "interview_completed": "Interview Completed",
    "offered": "Offer Extended",
    "hired": "Hired",
    "rejected": "Not Selected",
    "withdrawn": "Withdrawn",
    "on_hold": "Under Review",  # Don't expose "on hold" to candidates
}


@router.post(
    "/jobs/{job_id}/apply",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def apply_for_job(
    job_id: str,
    data: ApplicationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit an application to a published job."""
    if current_user.role != UserRole.CANDIDATE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only candidates can apply for jobs",
        )

    # Verify job is published
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job or job.status != JobStatus.PUBLISHED.value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or not accepting applications",
        )

    # Check duplicate
    existing = await db.execute(
        select(Application).where(
            Application.job_id == job_id,
            Application.candidate_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already applied for this job",
        )

    application = Application(
        job_id=job_id,
        candidate_id=current_user.id,
        resume_id=data.resume_id,
        cover_letter=data.cover_letter,
        status=ApplicationStatus.APPLIED.value,
    )
    db.add(application)
    await db.flush()

    # Record initial status
    history = ApplicationStatusHistory(
        application_id=application.id,
        previous_status=None,
        new_status=ApplicationStatus.APPLIED.value,
        changed_by=current_user.id,
        reason="Application submitted",
    )
    db.add(history)
    await db.flush()

    logger.info(f"Application submitted: {application.id} for job {job.title}")

    return ApplicationResponse(
        id=application.id,
        job_id=application.job_id,
        candidate_id=application.candidate_id,
        resume_id=application.resume_id,
        status=application.status,
        cover_letter=application.cover_letter,
        applied_at=application.applied_at,
        updated_at=application.updated_at,
        job_title=job.title,
        candidate_name=current_user.name,
    )


@router.get("", response_model=ApplicationListResponse)
async def list_applications(
    job_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List applications.
    - Candidates see their own applications.
    - Staff see applications for their authorized jobs.
    """
    pagination = PaginationParams(page, page_size)
    query = select(Application)

    if current_user.role == UserRole.CANDIDATE.value:
        query = query.where(Application.candidate_id == current_user.id)
    else:
        if current_user.role == UserRole.HIRING_MANAGER.value:
            # Only jobs they manage
            job_subquery = select(Job.id).where(
                Job.hiring_manager_id == current_user.id
            )
            query = query.where(Application.job_id.in_(job_subquery))
        elif current_user.organization_id:
            job_subquery = select(Job.id).where(
                Job.organization_id == current_user.organization_id
            )
            query = query.where(Application.job_id.in_(job_subquery))

    if job_id:
        query = query.where(Application.job_id == job_id)
    if status_filter:
        query = query.where(Application.status == status_filter)

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
            cover_letter=app.cover_letter if current_user.role != UserRole.CANDIDATE.value else app.cover_letter,
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


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get application details."""
    result = await db.execute(
        select(Application).where(Application.id == application_id)
    )
    app = result.scalar_one_or_none()

    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    # Authorization
    if current_user.role == UserRole.CANDIDATE.value and app.candidate_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    return ApplicationResponse(
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
    )


@router.patch("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: str,
    data: ApplicationStatusUpdateRequest,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Move an application to a new stage.
    Validates that the transition is allowed per the pipeline rules.
    """
    result = await db.execute(
        select(Application).where(Application.id == application_id)
    )
    app = result.scalar_one_or_none()

    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    # Validate transition
    try:
        current_status = ApplicationStatus(app.status)
        new_status = ApplicationStatus(data.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {data.status}",
        )

    allowed = APPLICATION_STATUS_TRANSITIONS.get(current_status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from '{current_status.value}' to '{new_status.value}'",
        )

    previous_status = app.status
    app.status = new_status.value

    # Record history
    history = ApplicationStatusHistory(
        application_id=app.id,
        previous_status=previous_status,
        new_status=new_status.value,
        changed_by=current_user.id,
        reason=data.reason,
    )
    db.add(history)
    await db.flush()

    logger.info(f"Application {app.id}: {previous_status} → {new_status.value}")

    return ApplicationResponse(
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
    )


@router.post("/{application_id}/withdraw", response_model=MessageResponse)
async def withdraw_application(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Candidate withdraws their own application."""
    if current_user.role != UserRole.CANDIDATE.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only candidates can withdraw")

    result = await db.execute(
        select(Application).where(
            Application.id == application_id,
            Application.candidate_id == current_user.id,
        )
    )
    app = result.scalar_one_or_none()

    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    current_status = ApplicationStatus(app.status)
    if ApplicationStatus.WITHDRAWN not in APPLICATION_STATUS_TRANSITIONS.get(current_status, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot withdraw application in its current status",
        )

    previous = app.status
    app.status = ApplicationStatus.WITHDRAWN.value

    history = ApplicationStatusHistory(
        application_id=app.id,
        previous_status=previous,
        new_status=ApplicationStatus.WITHDRAWN.value,
        changed_by=current_user.id,
        reason="Withdrawn by candidate",
    )
    db.add(history)
    await db.flush()

    return MessageResponse(message="Application withdrawn")


@router.get("/{application_id}/history", response_model=list[StatusHistoryResponse])
async def get_application_history(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get status change history for an application."""
    # Verify access
    result = await db.execute(
        select(Application).where(Application.id == application_id)
    )
    app = result.scalar_one_or_none()

    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    if current_user.role == UserRole.CANDIDATE.value and app.candidate_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    result = await db.execute(
        select(ApplicationStatusHistory)
        .where(ApplicationStatusHistory.application_id == application_id)
        .order_by(ApplicationStatusHistory.created_at.asc())
    )
    history = result.scalars().all()

    items = []
    for h in history:
        items.append(StatusHistoryResponse(
            id=h.id,
            previous_status=h.previous_status,
            new_status=h.new_status,
            changed_by=h.changed_by if current_user.role != UserRole.CANDIDATE.value else None,
            changed_by_name=h.actor.name if h.actor and current_user.role != UserRole.CANDIDATE.value else None,
            reason=h.reason if current_user.role != UserRole.CANDIDATE.value else None,
            created_at=h.created_at,
        ))

    return items


@router.get("/my/applications", response_model=list[CandidateApplicationStatusResponse])
async def get_my_applications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Candidate-friendly view of their application statuses."""
    if current_user.role != UserRole.CANDIDATE.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a candidate")

    result = await db.execute(
        select(Application)
        .where(Application.candidate_id == current_user.id)
        .order_by(Application.applied_at.desc())
    )
    applications = result.scalars().all()

    return [
        CandidateApplicationStatusResponse(
            id=app.id,
            job_title=app.job.title if app.job else "Unknown",
            status=app.status,
            status_display=STATUS_DISPLAY.get(app.status, app.status),
            applied_at=app.applied_at,
            updated_at=app.updated_at,
        )
        for app in applications
    ]
