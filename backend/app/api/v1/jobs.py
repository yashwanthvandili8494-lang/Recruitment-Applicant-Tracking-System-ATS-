"""
Job management endpoints — CRUD, publish, close, public careers page.

Recruiters and admins can manage jobs. Public endpoints serve published jobs.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, PaginationParams
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.models.enums import UserRole, JobStatus
from app.schemas.jobs import (
    JobCreateRequest,
    JobUpdateRequest,
    JobResponse,
    JobListResponse,
    PublicJobResponse,
)
from app.schemas.auth import MessageResponse

router = APIRouter()
logger = logging.getLogger(__name__)


# ───────────────── Public Endpoints ─────────────────

@router.get("/public", response_model=JobListResponse)
async def list_public_jobs(
    search: Optional[str] = Query(None, max_length=200),
    department: Optional[str] = None,
    employment_type: Optional[str] = None,
    work_mode: Optional[str] = None,
    location: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List published jobs for the public careers page."""
    pagination = PaginationParams(page, page_size)

    query = select(Job).where(Job.status == JobStatus.PUBLISHED.value)

    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                Job.title.ilike(search_filter),
                Job.description.ilike(search_filter),
                Job.department.ilike(search_filter),
            )
        )
    if department:
        query = query.where(Job.department == department)
    if employment_type:
        query = query.where(Job.employment_type == employment_type)
    if work_mode:
        query = query.where(Job.work_mode == work_mode)
    if location:
        query = query.where(Job.location.ilike(f"%{location}%"))

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Fetch
    query = query.order_by(Job.created_at.desc()).offset(pagination.offset).limit(pagination.limit)
    result = await db.execute(query)
    jobs = result.scalars().all()

    return JobListResponse(
        jobs=[JobResponse.model_validate(j) for j in jobs],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/public/{job_id}", response_model=PublicJobResponse)
async def get_public_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single published job's details."""
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.status == JobStatus.PUBLISHED.value)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


# ───────────────── Authenticated Endpoints ─────────────────

@router.get("", response_model=JobListResponse)
async def list_jobs(
    search: Optional[str] = Query(None, max_length=200),
    department: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """List jobs for authorized staff — filtered by organization."""
    pagination = PaginationParams(page, page_size)

    query = select(Job)
    if current_user.organization_id:
        query = query.where(Job.organization_id == current_user.organization_id)

    if current_user.role == UserRole.HIRING_MANAGER.value:
        query = query.where(Job.hiring_manager_id == current_user.id)

    if search:
        query = query.where(
            or_(Job.title.ilike(f"%{search}%"), Job.department.ilike(f"%{search}%"))
        )
    if department:
        query = query.where(Job.department == department)
    if status_filter:
        query = query.where(Job.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Job.created_at.desc()).offset(pagination.offset).limit(pagination.limit)
    result = await db.execute(query)
    jobs = result.scalars().all()

    return JobListResponse(
        jobs=[JobResponse.model_validate(j) for j in jobs],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single job's details."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Org isolation for staff
    if current_user.role != UserRole.CANDIDATE.value:
        if current_user.organization_id and job.organization_id != current_user.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return job


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    data: JobCreateRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.RECRUITER)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new job posting (starts as draft)."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    job = Job(
        organization_id=current_user.organization_id,
        title=data.title,
        description=data.description,
        responsibilities=data.responsibilities,
        requirements=data.requirements,
        preferred_skills=data.preferred_skills,
        department=data.department,
        employment_type=data.employment_type,
        work_mode=data.work_mode,
        location=data.location,
        experience_min=data.experience_min,
        experience_max=data.experience_max,
        salary_min=data.salary_min,
        salary_max=data.salary_max,
        openings=data.openings,
        deadline=data.deadline,
        hiring_manager_id=data.hiring_manager_id,
        status=JobStatus.DRAFT.value,
    )
    db.add(job)
    await db.flush()

    logger.info(f"Job created: {job.title} (id={job.id})")
    return job


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    data: JobUpdateRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.RECRUITER)),
    db: AsyncSession = Depends(get_db),
):
    """Update a job posting."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if current_user.organization_id and job.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(job, key, value)

    await db.flush()
    return job


@router.post("/{job_id}/publish", response_model=JobResponse)
async def publish_job(
    job_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.RECRUITER)),
    db: AsyncSession = Depends(get_db),
):
    """Publish a draft or paused job to make it visible and accept applications."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if current_user.organization_id and job.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.status not in [JobStatus.DRAFT.value, JobStatus.PAUSED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot publish a job with status '{job.status}'",
        )

    job.status = JobStatus.PUBLISHED.value
    await db.flush()
    logger.info(f"Job published: {job.title}")
    return job


@router.post("/{job_id}/close", response_model=JobResponse)
async def close_job(
    job_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.RECRUITER)),
    db: AsyncSession = Depends(get_db),
):
    """Close a published job — no more applications accepted."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if current_user.organization_id and job.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.status != JobStatus.PUBLISHED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only published jobs can be closed",
        )

    job.status = JobStatus.CLOSED.value
    await db.flush()
    return job


@router.delete("/{job_id}", response_model=MessageResponse)
async def delete_job(
    job_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Delete a draft job. Published/active jobs should be archived instead."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if current_user.organization_id and job.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.status != JobStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft jobs can be deleted. Archive or close active jobs instead.",
        )

    await db.delete(job)
    await db.flush()
    return MessageResponse(message="Job deleted")
