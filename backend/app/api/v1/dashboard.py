"""
Dashboard endpoints — real database-backed metrics.

No hardcoded data. Every metric comes from actual database queries.
"""

import logging

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.models.interview import Interview
from app.models.offer import Offer
from app.models.audit_log import AuditLog
from app.models.enums import (
    UserRole, JobStatus, ApplicationStatus,
    InterviewStatus, OfferStatus,
)
from app.schemas.recruitment import (
    DashboardOverview,
    RecruitmentFunnel,
    ActivityItem,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/overview", response_model=DashboardOverview)
async def get_overview(
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Dashboard overview with real-time metrics from the database."""
    # Scope by organization
    org_id = current_user.organization_id

    # Total open (published) jobs
    open_jobs_q = select(func.count(Job.id)).where(Job.status == JobStatus.PUBLISHED.value)
    if org_id:
        open_jobs_q = open_jobs_q.where(Job.organization_id == org_id)
    total_open_jobs = (await db.execute(open_jobs_q)).scalar() or 0

    # Total applications
    apps_q = select(func.count(Application.id))
    if org_id:
        apps_q = apps_q.join(Job).where(Job.organization_id == org_id)
    total_applications = (await db.execute(apps_q)).scalar() or 0

    # Applications awaiting review
    review_q = select(func.count(Application.id)).where(
        Application.status == ApplicationStatus.APPLIED.value
    )
    if org_id:
        review_q = review_q.join(Job).where(Job.organization_id == org_id)
    awaiting_review = (await db.execute(review_q)).scalar() or 0

    # Scheduled interviews
    interviews_q = select(func.count(Interview.id)).where(
        Interview.status == InterviewStatus.SCHEDULED.value
    )
    scheduled_interviews = (await db.execute(interviews_q)).scalar() or 0

    # Pending offers
    offers_q = select(func.count(Offer.id)).where(
        Offer.status.in_([OfferStatus.PENDING_APPROVAL.value, OfferStatus.SENT.value])
    )
    pending_offers = (await db.execute(offers_q)).scalar() or 0

    # Hired
    hired_q = select(func.count(Application.id)).where(
        Application.status == ApplicationStatus.HIRED.value
    )
    if org_id:
        hired_q = hired_q.join(Job).where(Job.organization_id == org_id)
    hired = (await db.execute(hired_q)).scalar() or 0

    return DashboardOverview(
        total_open_jobs=total_open_jobs,
        total_applications=total_applications,
        applications_awaiting_review=awaiting_review,
        interviews_scheduled=scheduled_interviews,
        offers_pending=pending_offers,
        candidates_hired=hired,
    )


@router.get("/recruitment-funnel", response_model=list[RecruitmentFunnel])
async def get_recruitment_funnel(
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Application counts by recruitment stage."""
    result = await db.execute(
        select(Application.status, func.count(Application.id))
        .group_by(Application.status)
    )
    rows = result.all()

    return [
        RecruitmentFunnel(stage=row[0], count=row[1])
        for row in rows
    ]


@router.get("/activity", response_model=list[ActivityItem])
async def get_recent_activity(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Recent audit log entries."""
    query = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)

    if current_user.organization_id:
        query = query.where(AuditLog.organization_id == current_user.organization_id)

    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        ActivityItem(
            action=log.action,
            resource_type=log.resource_type,
            actor_name=log.actor.name if log.actor else None,
            created_at=log.created_at,
        )
        for log in logs
    ]
