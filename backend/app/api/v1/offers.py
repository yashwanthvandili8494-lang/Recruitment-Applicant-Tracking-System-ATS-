"""
Offer management endpoints — create, approve, send, respond.

Follows the approval workflow: Draft → Pending Approval → Sent → Accepted/Declined.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, PaginationParams
from app.models.user import User
from app.models.application import Application
from app.models.offer import Offer
from app.models.enums import UserRole, OfferStatus, ApplicationStatus
from app.schemas.recruitment import (
    OfferCreateRequest,
    OfferResponse,
    OfferRespondRequest,
    OfferListResponse,
)
from app.schemas.auth import MessageResponse

router = APIRouter()
logger = logging.getLogger(__name__)


def _build_offer_response(offer: Offer) -> OfferResponse:
    candidate_name = None
    job_title = None
    if offer.application:
        if offer.application.candidate:
            candidate_name = offer.application.candidate.name
        if offer.application.job:
            job_title = offer.application.job.title

    return OfferResponse(
        id=offer.id,
        application_id=offer.application_id,
        compensation_details=offer.compensation_details,
        status=offer.status,
        issued_by=offer.issued_by,
        approved_by=offer.approved_by,
        notes=offer.notes,
        issued_at=offer.issued_at,
        expires_at=offer.expires_at,
        candidate_response_at=offer.candidate_response_at,
        created_at=offer.created_at,
        updated_at=offer.updated_at,
        candidate_name=candidate_name,
        job_title=job_title,
    )


@router.post(
    "/applications/{application_id}/offers",
    response_model=OfferResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_offer(
    application_id: str,
    data: OfferCreateRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.RECRUITER)),
    db: AsyncSession = Depends(get_db),
):
    """Create a draft offer for an application."""
    result = await db.execute(
        select(Application).where(Application.id == application_id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    # Check for existing active offer
    existing = await db.execute(
        select(Offer).where(
            Offer.application_id == application_id,
            Offer.status.notin_([OfferStatus.WITHDRAWN.value, OfferStatus.DECLINED.value, OfferStatus.EXPIRED.value]),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active offer already exists for this application",
        )

    offer = Offer(
        application_id=application_id,
        compensation_details=data.compensation_details,
        notes=data.notes,
        expires_at=data.expires_at,
        issued_by=current_user.id,
        status=OfferStatus.DRAFT.value,
    )
    db.add(offer)
    await db.flush()
    await db.refresh(offer, ["application"])

    logger.info(f"Offer created: {offer.id}")
    return _build_offer_response(offer)


@router.get("", response_model=OfferListResponse)
async def list_offers(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List offers."""
    pagination = PaginationParams(page, page_size)
    query = select(Offer)

    if current_user.role == UserRole.CANDIDATE.value:
        query = query.join(Application).where(
            Application.candidate_id == current_user.id,
            Offer.status.in_([OfferStatus.SENT.value, OfferStatus.ACCEPTED.value, OfferStatus.DECLINED.value]),
        )

    if status_filter:
        query = query.where(Offer.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Offer.created_at.desc()).offset(pagination.offset).limit(pagination.limit)
    result = await db.execute(query)
    offers = result.scalars().unique().all()

    return OfferListResponse(
        offers=[_build_offer_response(o) for o in offers],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{offer_id}", response_model=OfferResponse)
async def get_offer(
    offer_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get offer details."""
    result = await db.execute(select(Offer).where(Offer.id == offer_id))
    offer = result.scalar_one_or_none()

    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")

    if current_user.role == UserRole.CANDIDATE.value:
        if offer.application.candidate_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
        if offer.status not in [OfferStatus.SENT.value, OfferStatus.ACCEPTED.value, OfferStatus.DECLINED.value]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")

    return _build_offer_response(offer)


@router.post("/{offer_id}/approve", response_model=OfferResponse)
async def approve_offer(
    offer_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HIRING_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    """Approve a pending offer."""
    result = await db.execute(select(Offer).where(Offer.id == offer_id))
    offer = result.scalar_one_or_none()

    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")

    if offer.status != OfferStatus.PENDING_APPROVAL.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending offers can be approved",
        )

    offer.approved_by = current_user.id
    offer.status = OfferStatus.SENT.value
    offer.issued_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(offer, ["application"])

    return _build_offer_response(offer)


@router.post("/{offer_id}/send", response_model=OfferResponse)
async def send_offer(
    offer_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.RECRUITER)),
    db: AsyncSession = Depends(get_db),
):
    """Submit a draft offer for approval, or send directly if already approved."""
    result = await db.execute(select(Offer).where(Offer.id == offer_id))
    offer = result.scalar_one_or_none()

    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")

    if offer.status == OfferStatus.DRAFT.value:
        offer.status = OfferStatus.PENDING_APPROVAL.value
    elif offer.status == OfferStatus.PENDING_APPROVAL.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offer is awaiting approval",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot send offer with status '{offer.status}'",
        )

    await db.flush()
    await db.refresh(offer, ["application"])

    # Update application status
    if offer.application:
        offer.application.status = ApplicationStatus.OFFERED.value

    return _build_offer_response(offer)


@router.post("/{offer_id}/respond", response_model=OfferResponse)
async def respond_to_offer(
    offer_id: str,
    data: OfferRespondRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Candidate responds to an offer (accept or decline)."""
    if current_user.role != UserRole.CANDIDATE.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only candidates can respond to offers")

    result = await db.execute(select(Offer).where(Offer.id == offer_id))
    offer = result.scalar_one_or_none()

    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")

    if offer.application.candidate_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")

    if offer.status != OfferStatus.SENT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only respond to sent offers",
        )

    # Check expiry
    if offer.expires_at:
        expires = offer.expires_at if offer.expires_at.tzinfo else offer.expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires:
            offer.status = OfferStatus.EXPIRED.value
            await db.flush()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This offer has expired",
            )

    offer.status = OfferStatus.ACCEPTED.value if data.accepted else OfferStatus.DECLINED.value
    offer.candidate_response_at = datetime.now(timezone.utc)

    # Update application status
    if data.accepted and offer.application:
        offer.application.status = ApplicationStatus.HIRED.value

    await db.flush()
    await db.refresh(offer, ["application"])

    return _build_offer_response(offer)
