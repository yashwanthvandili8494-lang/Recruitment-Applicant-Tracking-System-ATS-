"""Pydantic schemas for job management."""

from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, Field


class JobCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    responsibilities: Optional[str] = None
    requirements: Optional[str] = None
    preferred_skills: Optional[str] = None
    department: Optional[str] = Field(None, max_length=100)
    employment_type: str = Field(default="full_time")
    work_mode: str = Field(default="onsite")
    location: Optional[str] = Field(None, max_length=255)
    experience_min: Optional[int] = Field(None, ge=0)
    experience_max: Optional[int] = Field(None, ge=0)
    salary_min: Optional[float] = Field(None, ge=0)
    salary_max: Optional[float] = Field(None, ge=0)
    openings: int = Field(default=1, ge=1)
    deadline: Optional[date] = None
    hiring_manager_id: Optional[str] = None


class JobUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    responsibilities: Optional[str] = None
    requirements: Optional[str] = None
    preferred_skills: Optional[str] = None
    department: Optional[str] = Field(None, max_length=100)
    employment_type: Optional[str] = None
    work_mode: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    experience_min: Optional[int] = Field(None, ge=0)
    experience_max: Optional[int] = Field(None, ge=0)
    salary_min: Optional[float] = Field(None, ge=0)
    salary_max: Optional[float] = Field(None, ge=0)
    openings: Optional[int] = Field(None, ge=1)
    deadline: Optional[date] = None
    hiring_manager_id: Optional[str] = None


class JobResponse(BaseModel):
    id: str
    organization_id: str
    title: str
    description: str
    responsibilities: Optional[str] = None
    requirements: Optional[str] = None
    preferred_skills: Optional[str] = None
    department: Optional[str] = None
    employment_type: str
    work_mode: str
    location: Optional[str] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    openings: int
    deadline: Optional[date] = None
    hiring_manager_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    application_count: Optional[int] = None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int
    page: int
    page_size: int


class PublicJobResponse(BaseModel):
    """Job details visible to unauthenticated visitors on the careers page."""
    id: str
    title: str
    description: str
    responsibilities: Optional[str] = None
    requirements: Optional[str] = None
    preferred_skills: Optional[str] = None
    department: Optional[str] = None
    employment_type: str
    work_mode: str
    location: Optional[str] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    openings: int
    deadline: Optional[date] = None
    created_at: datetime

    model_config = {"from_attributes": True}
