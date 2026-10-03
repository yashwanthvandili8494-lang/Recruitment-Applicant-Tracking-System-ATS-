"""Pydantic schemas for candidates, applications, resumes, interviews, offers."""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


# ───────────────── Candidate Profile ─────────────────

class CandidateProfileUpdate(BaseModel):
    phone: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = Field(None, ge=0)
    education: Optional[List[Dict[str, Any]]] = None
    portfolio_url: Optional[str] = Field(None, max_length=500)
    github_url: Optional[str] = Field(None, max_length=500)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    summary: Optional[str] = None


class CandidateProfileResponse(BaseModel):
    id: str
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = None
    education: Optional[List[Dict[str, Any]]] = None
    portfolio_url: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CandidateSearchResponse(BaseModel):
    id: str
    user_id: str
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CandidateListResponse(BaseModel):
    candidates: List[CandidateSearchResponse]
    total: int
    page: int
    page_size: int


# ───────────────── Application ─────────────────

class ApplicationCreateRequest(BaseModel):
    resume_id: Optional[str] = None
    cover_letter: Optional[str] = Field(None, max_length=5000)


class ApplicationStatusUpdateRequest(BaseModel):
    status: str
    reason: Optional[str] = Field(None, max_length=1000)


class ApplicationResponse(BaseModel):
    id: str
    job_id: str
    candidate_id: str
    resume_id: Optional[str] = None
    status: str
    cover_letter: Optional[str] = None
    applied_at: datetime
    updated_at: datetime
    job_title: Optional[str] = None
    candidate_name: Optional[str] = None

    model_config = {"from_attributes": True}


class ApplicationListResponse(BaseModel):
    applications: List[ApplicationResponse]
    total: int
    page: int
    page_size: int


class StatusHistoryResponse(BaseModel):
    id: str
    previous_status: Optional[str] = None
    new_status: str
    changed_by: Optional[str] = None
    changed_by_name: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CandidateApplicationStatusResponse(BaseModel):
    """Candidate-friendly view — no internal notes or other candidate info."""
    id: str
    job_title: str
    status: str
    status_display: str
    applied_at: datetime
    updated_at: datetime


# ───────────────── Resume ─────────────────

class ResumeResponse(BaseModel):
    id: str
    candidate_id: str
    original_filename: str
    content_type: str
    file_size: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ───────────────── Interview ─────────────────

class InterviewCreateRequest(BaseModel):
    interview_round: int = Field(default=1, ge=1)
    interview_type: str = "video"
    start_time: datetime
    end_time: datetime
    timezone: str = "UTC"
    meeting_location: Optional[str] = None
    notes: Optional[str] = None
    interviewer_ids: List[str] = Field(..., min_length=1)


class InterviewUpdateRequest(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timezone: Optional[str] = None
    meeting_location: Optional[str] = None
    interview_type: Optional[str] = None
    notes: Optional[str] = None
    interviewer_ids: Optional[List[str]] = None


class InterviewResponse(BaseModel):
    id: str
    application_id: str
    interview_round: int
    interview_type: str
    start_time: datetime
    end_time: datetime
    timezone: str
    meeting_location: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    interviewers: Optional[List[Dict[str, str]]] = None
    candidate_name: Optional[str] = None
    job_title: Optional[str] = None

    model_config = {"from_attributes": True}


class InterviewListResponse(BaseModel):
    interviews: List[InterviewResponse]
    total: int
    page: int
    page_size: int


# ───────────────── Interview Feedback ─────────────────

class FeedbackCreateRequest(BaseModel):
    criterion_scores: Dict[str, int] = Field(
        ...,
        description="Scores for each criterion, e.g. {'technical_skills': 4, 'communication': 5}",
    )
    strengths: Optional[str] = None
    concerns: Optional[str] = None
    recommendation: str = Field(
        ...,
        pattern="^(strong_yes|yes|maybe|no|strong_no)$",
    )
    overall_notes: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: str
    interview_id: str
    interviewer_id: str
    interviewer_name: Optional[str] = None
    criterion_scores: Optional[Dict[str, int]] = None
    strengths: Optional[str] = None
    concerns: Optional[str] = None
    recommendation: Optional[str] = None
    overall_notes: Optional[str] = None
    submitted_at: datetime

    model_config = {"from_attributes": True}


# ───────────────── Offer ─────────────────

class OfferCreateRequest(BaseModel):
    compensation_details: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    expires_at: Optional[datetime] = None


class OfferResponse(BaseModel):
    id: str
    application_id: str
    compensation_details: Optional[Dict[str, Any]] = None
    status: str
    issued_by: Optional[str] = None
    approved_by: Optional[str] = None
    notes: Optional[str] = None
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    candidate_response_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    candidate_name: Optional[str] = None
    job_title: Optional[str] = None

    model_config = {"from_attributes": True}


class OfferRespondRequest(BaseModel):
    accepted: bool


class OfferListResponse(BaseModel):
    offers: List[OfferResponse]
    total: int
    page: int
    page_size: int


# ───────────────── Dashboard ─────────────────

class DashboardOverview(BaseModel):
    total_open_jobs: int
    total_applications: int
    applications_awaiting_review: int
    interviews_scheduled: int
    offers_pending: int
    candidates_hired: int


class RecruitmentFunnel(BaseModel):
    stage: str
    count: int


class ActivityItem(BaseModel):
    action: str
    resource_type: str
    actor_name: Optional[str] = None
    created_at: datetime
