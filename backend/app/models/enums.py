"""
Enum definitions for all domain-specific status fields.

These Python enums map to PostgreSQL VARCHAR columns via SQLAlchemy.
Keeping them in one place avoids circular imports and provides
a single source of truth for allowed values.
"""

import enum


class UserRole(str, enum.Enum):
    """Roles determining user permissions."""
    ADMIN = "admin"
    RECRUITER = "recruiter"
    HIRING_MANAGER = "hiring_manager"
    INTERVIEWER = "interviewer"
    CANDIDATE = "candidate"


class JobStatus(str, enum.Enum):
    """Lifecycle stages of a job posting."""
    DRAFT = "draft"
    PUBLISHED = "published"
    PAUSED = "paused"
    CLOSED = "closed"
    ARCHIVED = "archived"


class EmploymentType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    TEMPORARY = "temporary"


class WorkMode(str, enum.Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"


class ApplicationStatus(str, enum.Enum):
    """Recruitment pipeline stages."""
    APPLIED = "applied"
    UNDER_REVIEW = "under_review"
    SHORTLISTED = "shortlisted"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    OFFERED = "offered"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    ON_HOLD = "on_hold"


# Valid forward transitions — enforced on the backend
APPLICATION_STATUS_TRANSITIONS: dict[ApplicationStatus, list[ApplicationStatus]] = {
    ApplicationStatus.APPLIED: [
        ApplicationStatus.UNDER_REVIEW,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    ],
    ApplicationStatus.UNDER_REVIEW: [
        ApplicationStatus.SHORTLISTED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.ON_HOLD,
        ApplicationStatus.WITHDRAWN,
    ],
    ApplicationStatus.SHORTLISTED: [
        ApplicationStatus.INTERVIEW_SCHEDULED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.ON_HOLD,
        ApplicationStatus.WITHDRAWN,
    ],
    ApplicationStatus.INTERVIEW_SCHEDULED: [
        ApplicationStatus.INTERVIEW_COMPLETED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.ON_HOLD,
        ApplicationStatus.WITHDRAWN,
    ],
    ApplicationStatus.INTERVIEW_COMPLETED: [
        ApplicationStatus.INTERVIEW_SCHEDULED,  # Another round
        ApplicationStatus.OFFERED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.ON_HOLD,
        ApplicationStatus.WITHDRAWN,
    ],
    ApplicationStatus.OFFERED: [
        ApplicationStatus.HIRED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    ],
    ApplicationStatus.ON_HOLD: [
        ApplicationStatus.UNDER_REVIEW,
        ApplicationStatus.SHORTLISTED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    ],
    # Terminal states — no further transitions
    ApplicationStatus.HIRED: [],
    ApplicationStatus.REJECTED: [],
    ApplicationStatus.WITHDRAWN: [],
}


class InterviewType(str, enum.Enum):
    PHONE = "phone"
    VIDEO = "video"
    IN_PERSON = "in_person"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    PANEL = "panel"


class InterviewStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"
    NO_SHOW = "no_show"


class OfferStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    SENT = "sent"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


class NotificationType(str, enum.Enum):
    ACCOUNT_VERIFICATION = "account_verification"
    PASSWORD_RESET = "password_reset"
    APPLICATION_CONFIRMATION = "application_confirmation"
    STATUS_CHANGE = "status_change"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_RESCHEDULED = "interview_rescheduled"
    INTERVIEW_CANCELLED = "interview_cancelled"
    INTERVIEW_REMINDER = "interview_reminder"
    OFFER_NOTIFICATION = "offer_notification"
    HIRING_DECISION = "hiring_decision"


class DeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


class Recommendation(str, enum.Enum):
    STRONG_YES = "strong_yes"
    YES = "yes"
    MAYBE = "maybe"
    NO = "no"
    STRONG_NO = "strong_no"
