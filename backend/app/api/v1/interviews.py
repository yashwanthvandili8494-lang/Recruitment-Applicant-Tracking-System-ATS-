"""
Interview scheduling endpoints — create, reschedule, cancel, conflict detection.

Includes feedback/scorecard submission.
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, PaginationParams
from app.models.user import User
from app.models.application import Application
from app.models.interview import Interview
from app.models.interview_participant import InterviewParticipant
from app.models.interview_feedback import InterviewFeedback
from app.models.enums import UserRole, InterviewStatus
from app.schemas.recruitment import (
    InterviewCreateRequest,
    InterviewUpdateRequest,
    InterviewResponse,
    InterviewListResponse,
    FeedbackCreateRequest,
    FeedbackResponse,
)
from app.schemas.auth import MessageResponse

router = APIRouter()
logger = logging.getLogger(__name__)


def _build_interview_response(interview: Interview) -> InterviewResponse:
    """Build a consistent InterviewResponse from a model instance."""
    interviewers = []
    if interview.participants:
        for p in interview.participants:
            interviewers.append({
                "user_id": p.user_id,
                "name": p.user.name if p.user else "Unknown",
                "role": p.role or "interviewer",
            })

    candidate_name = None
    job_title = None
    if interview.application:
        if interview.application.candidate:
            candidate_name = interview.application.candidate.name
        if interview.application.job:
            job_title = interview.application.job.title

    return InterviewResponse(
        id=interview.id,
        application_id=interview.application_id,
        interview_round=interview.interview_round,
        interview_type=interview.interview_type,
        start_time=interview.start_time,
        end_time=interview.end_time,
        timezone=interview.timezone,
        meeting_location=interview.meeting_location,
        status=interview.status,
        notes=interview.notes,
        created_at=interview.created_at,
        updated_at=interview.updated_at,
        interviewers=interviewers,
        candidate_name=candidate_name,
        job_title=job_title,
    )


async def _check_scheduling_conflicts(
    db: AsyncSession,
    interviewer_ids: list[str],
    start_time: datetime,
    end_time: datetime,
    exclude_interview_id: Optional[str] = None,
) -> list[dict]:
    """Check for scheduling conflicts with existing interviews."""
    conflicts = []

    for uid in interviewer_ids:
        query = (
            select(Interview)
            .join(InterviewParticipant)
            .where(
                InterviewParticipant.user_id == uid,
                Interview.status.in_([
                    InterviewStatus.SCHEDULED.value,
                    InterviewStatus.RESCHEDULED.value,
                ]),
                or_(
                    and_(Interview.start_time < end_time, Interview.end_time > start_time),
                ),
            )
        )
        if exclude_interview_id:
            query = query.where(Interview.id != exclude_interview_id)

        result = await db.execute(query)
        conflicting = result.scalars().all()

        for c in conflicting:
            conflicts.append({
                "interviewer_id": uid,
                "conflicting_interview_id": c.id,
                "start_time": str(c.start_time),
                "end_time": str(c.end_time),
            })

    return conflicts


@router.post(
    "/applications/{application_id}/schedule",
    response_model=InterviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def schedule_interview(
    application_id: str,
    data: InterviewCreateRequest,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Schedule an interview for an application."""
    # Verify application exists
    result = await db.execute(
        select(Application).where(Application.id == application_id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    if data.start_time >= data.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time",
        )

    # Check conflicts
    conflicts = await _check_scheduling_conflicts(
        db, data.interviewer_ids, data.start_time, data.end_time
    )
    if conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Scheduling conflicts detected", "conflicts": conflicts},
        )

    interview = Interview(
        application_id=application_id,
        interview_round=data.interview_round,
        interview_type=data.interview_type,
        start_time=data.start_time,
        end_time=data.end_time,
        timezone=data.timezone,
        meeting_location=data.meeting_location,
        notes=data.notes,
        status=InterviewStatus.SCHEDULED.value,
    )
    db.add(interview)
    await db.flush()

    # Add participants
    for uid in data.interviewer_ids:
        participant = InterviewParticipant(
            interview_id=interview.id,
            user_id=uid,
            role="interviewer",
        )
        db.add(participant)
    await db.flush()

    # Refresh to load relationships
    await db.refresh(interview, ["participants", "application"])

    logger.info(f"Interview scheduled: {interview.id} for application {application_id}")
    return _build_interview_response(interview)


@router.get("", response_model=InterviewListResponse)
async def list_interviews(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List interviews based on user role."""
    pagination = PaginationParams(page, page_size)

    query = select(Interview)

    if current_user.role == UserRole.CANDIDATE.value:
        query = query.join(Application).where(
            Application.candidate_id == current_user.id
        )
    elif current_user.role == UserRole.INTERVIEWER.value:
        query = query.join(InterviewParticipant).where(
            InterviewParticipant.user_id == current_user.id
        )

    if status_filter:
        query = query.where(Interview.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Interview.start_time.desc()).offset(pagination.offset).limit(pagination.limit)
    result = await db.execute(query)
    interviews = result.scalars().unique().all()

    return InterviewListResponse(
        interviews=[_build_interview_response(i) for i in interviews],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{interview_id}", response_model=InterviewResponse)
async def get_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get interview details."""
    result = await db.execute(
        select(Interview).where(Interview.id == interview_id)
    )
    interview = result.scalar_one_or_none()

    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    # Authorization
    if current_user.role == UserRole.CANDIDATE.value:
        if interview.application.candidate_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
    elif current_user.role == UserRole.INTERVIEWER.value:
        participant_ids = [p.user_id for p in interview.participants]
        if current_user.id not in participant_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not assigned to this interview")

    return _build_interview_response(interview)


@router.patch("/{interview_id}", response_model=InterviewResponse)
async def update_interview(
    interview_id: str,
    data: InterviewUpdateRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.RECRUITER)),
    db: AsyncSession = Depends(get_db),
):
    """Reschedule or update an interview."""
    result = await db.execute(
        select(Interview).where(Interview.id == interview_id)
    )
    interview = result.scalar_one_or_none()

    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    update_data = data.model_dump(exclude_unset=True)

    # If rescheduling, check conflicts
    if "start_time" in update_data or "end_time" in update_data:
        start = update_data.get("start_time", interview.start_time)
        end = update_data.get("end_time", interview.end_time)

        interviewer_ids = [p.user_id for p in interview.participants]
        if "interviewer_ids" in update_data:
            interviewer_ids = update_data.pop("interviewer_ids")

        conflicts = await _check_scheduling_conflicts(
            db, interviewer_ids, start, end, exclude_interview_id=interview.id
        )
        if conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": "Scheduling conflicts detected", "conflicts": conflicts},
            )

        interview.status = InterviewStatus.RESCHEDULED.value

    # Update participants if specified
    if "interviewer_ids" in update_data:
        new_ids = update_data.pop("interviewer_ids")
        # Remove old participants
        for p in interview.participants:
            await db.delete(p)
        # Add new ones
        for uid in new_ids:
            db.add(InterviewParticipant(interview_id=interview.id, user_id=uid))

    for key, value in update_data.items():
        setattr(interview, key, value)

    await db.flush()
    await db.refresh(interview, ["participants", "application"])

    return _build_interview_response(interview)


@router.post("/{interview_id}/cancel", response_model=MessageResponse)
async def cancel_interview(
    interview_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.RECRUITER)),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a scheduled interview."""
    result = await db.execute(
        select(Interview).where(Interview.id == interview_id)
    )
    interview = result.scalar_one_or_none()

    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    if interview.status in [InterviewStatus.COMPLETED.value, InterviewStatus.CANCELLED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel interview with status '{interview.status}'",
        )

    interview.status = InterviewStatus.CANCELLED.value
    await db.flush()

    return MessageResponse(message="Interview cancelled")


@router.post("/{interview_id}/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    interview_id: str,
    data: FeedbackCreateRequest,
    current_user: User = Depends(
        require_roles(UserRole.INTERVIEWER, UserRole.HIRING_MANAGER, UserRole.ADMIN, UserRole.RECRUITER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Submit interview scorecard/feedback."""
    result = await db.execute(
        select(Interview).where(Interview.id == interview_id)
    )
    interview = result.scalar_one_or_none()

    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    # Check if user is a participant (or admin/recruiter)
    if current_user.role in [UserRole.INTERVIEWER.value, UserRole.HIRING_MANAGER.value]:
        participant_ids = [p.user_id for p in interview.participants]
        if current_user.id not in participant_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not assigned to this interview",
            )

    # Check for duplicate feedback
    existing = await db.execute(
        select(InterviewFeedback).where(
            InterviewFeedback.interview_id == interview_id,
            InterviewFeedback.interviewer_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already submitted feedback for this interview",
        )

    feedback = InterviewFeedback(
        interview_id=interview_id,
        interviewer_id=current_user.id,
        criterion_scores=data.criterion_scores,
        strengths=data.strengths,
        concerns=data.concerns,
        recommendation=data.recommendation,
        overall_notes=data.overall_notes,
    )
    db.add(feedback)
    await db.flush()

    return FeedbackResponse(
        id=feedback.id,
        interview_id=feedback.interview_id,
        interviewer_id=feedback.interviewer_id,
        interviewer_name=current_user.name,
        criterion_scores=feedback.criterion_scores,
        strengths=feedback.strengths,
        concerns=feedback.concerns,
        recommendation=feedback.recommendation,
        overall_notes=feedback.overall_notes,
        submitted_at=feedback.submitted_at,
    )


@router.get("/{interview_id}/feedback", response_model=list[FeedbackResponse])
async def get_interview_feedback(
    interview_id: str,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER, UserRole.INTERVIEWER)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Get all feedback for an interview — staff only."""
    result = await db.execute(
        select(InterviewFeedback).where(InterviewFeedback.interview_id == interview_id)
    )
    feedbacks = result.scalars().all()

    return [
        FeedbackResponse(
            id=f.id,
            interview_id=f.interview_id,
            interviewer_id=f.interviewer_id,
            interviewer_name=f.interviewer.name if f.interviewer else None,
            criterion_scores=f.criterion_scores,
            strengths=f.strengths,
            concerns=f.concerns,
            recommendation=f.recommendation,
            overall_notes=f.overall_notes,
            submitted_at=f.submitted_at,
        )
        for f in feedbacks
    ]
