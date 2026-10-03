"""Database models package. Import all models here for Alembic discovery."""

from app.core.database import Base  # noqa: F401
from app.models.organization import Organization  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.candidate_profile import CandidateProfile  # noqa: F401
from app.models.job import Job  # noqa: F401
from app.models.resume import Resume  # noqa: F401
from app.models.application import Application  # noqa: F401
from app.models.application_status_history import ApplicationStatusHistory  # noqa: F401
from app.models.interview import Interview  # noqa: F401
from app.models.interview_participant import InterviewParticipant  # noqa: F401
from app.models.interview_feedback import InterviewFeedback  # noqa: F401
from app.models.offer import Offer  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
