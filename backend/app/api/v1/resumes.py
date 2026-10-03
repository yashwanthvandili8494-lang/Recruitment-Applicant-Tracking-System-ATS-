"""
Resume upload and management endpoints.

Validates file type, size, and stores with unique keys.
Downloads require authorization.
"""

import hashlib
import logging
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.resume import Resume
from app.models.application import Application
from app.models.enums import UserRole
from app.schemas.recruitment import ResumeResponse
from app.schemas.auth import MessageResponse

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


@router.post("", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a resume (PDF or DOCX). Candidates only."""
    if current_user.role != UserRole.CANDIDATE.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only candidates can upload resumes")

    # Validate extension
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename required")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid content type. Upload a PDF or DOCX file.",
        )

    # Read and validate size
    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # Validate file signature (magic bytes)
    if ext == ".pdf" and not content[:4] == b"%PDF":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match PDF format",
        )
    if ext == ".docx" and not content[:2] == b"PK":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match DOCX format",
        )

    # Generate unique storage key
    storage_key = f"{current_user.id}/{uuid.uuid4().hex}{ext}"
    checksum = hashlib.sha256(content).hexdigest()

    # Store file
    file_path = os.path.join(settings.UPLOAD_DIRECTORY, storage_key)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)

    # Deactivate previous resumes
    result = await db.execute(
        select(Resume).where(
            Resume.candidate_id == current_user.id,
            Resume.is_active == True,
        )
    )
    for old_resume in result.scalars().all():
        old_resume.is_active = False

    # Extract text (optional, best-effort)
    extracted_text = None
    try:
        if ext == ".pdf":
            import fitz
            doc = fitz.open(stream=content, filetype="pdf")
            extracted_text = "\n".join(page.get_text() for page in doc)
            doc.close()
        elif ext == ".docx":
            import io
            from docx import Document
            doc = Document(io.BytesIO(content))
            extracted_text = "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        logger.warning(f"Text extraction failed for {file.filename}: {e}")

    resume = Resume(
        candidate_id=current_user.id,
        storage_key=storage_key,
        original_filename=file.filename,
        content_type=file.content_type or f"application/{ext[1:]}",
        file_size=len(content),
        extracted_text=extracted_text,
        checksum=checksum,
        is_active=True,
    )
    db.add(resume)
    await db.flush()

    logger.info(f"Resume uploaded: {resume.original_filename} by {current_user.email}")
    return resume


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume_info(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get resume metadata (not the file itself)."""
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()

    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    # Authorization: owner or staff
    if current_user.role == UserRole.CANDIDATE.value and resume.candidate_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    return resume


@router.get("/{resume_id}/download")
async def download_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a resume file. Authorized users only."""
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()

    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    # Authorization check
    if current_user.role == UserRole.CANDIDATE.value:
        if resume.candidate_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    elif current_user.role == UserRole.INTERVIEWER.value:
        # Only allow if interviewer is assigned to an interview for this candidate
        from app.models.interview import Interview
        from app.models.interview_participant import InterviewParticipant

        result = await db.execute(
            select(InterviewParticipant)
            .join(Interview)
            .join(Application)
            .where(
                InterviewParticipant.user_id == current_user.id,
                Application.candidate_id == resume.candidate_id,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    file_path = os.path.join(settings.UPLOAD_DIRECTORY, resume.storage_key)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on storage")

    return FileResponse(
        path=file_path,
        filename=resume.original_filename,
        media_type=resume.content_type,
    )


@router.delete("/{resume_id}", response_model=MessageResponse)
async def delete_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a resume. Candidate can delete their own unused resumes."""
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()

    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    if current_user.role == UserRole.CANDIDATE.value and resume.candidate_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    # Check if resume is attached to any active application
    result = await db.execute(
        select(Application).where(Application.resume_id == resume_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a resume attached to an application",
        )

    # Delete file
    file_path = os.path.join(settings.UPLOAD_DIRECTORY, resume.storage_key)
    if os.path.exists(file_path):
        os.remove(file_path)

    await db.delete(resume)
    await db.flush()

    return MessageResponse(message="Resume deleted")
