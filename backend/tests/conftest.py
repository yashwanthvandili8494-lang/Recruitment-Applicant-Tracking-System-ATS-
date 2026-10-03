"""
Pytest configuration and fixtures for RecruitFlow ATS.

Uses an in-memory SQLite database with async engine (aiosqlite)
and ASGITransport for fast, isolated async testing.
"""

import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy import event

from app.core.database import Base, get_db
from app.core.security import hash_password, create_access_token
from app.models import (
    Organization, User, CandidateProfile, Job, Application,
    ApplicationStatusHistory, Resume, Interview, InterviewParticipant,
    InterviewFeedback, Offer, Notification, AuditLog,
)
from app.models.enums import UserRole, JobStatus, EmploymentType, WorkMode
from app.main import app

# Test database engine — single in-memory SQLite shared across all connections via StaticPool
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)




@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    """Create tables before test and drop afterwards."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session for tests."""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(autouse=True)
def mock_smtp():
    """Prevent actual email dispatch in tests."""
    with patch("app.services.email_service.send_email", new_callable=AsyncMock) as mocked:
        mocked.return_value = True
        yield mocked


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Test HTTP client with dependency overrides."""
    async def override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_org(db_session: AsyncSession) -> Organization:
    """Create test organization."""
    org = Organization(name="Acme Global", slug="acme-global")
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession, test_org: Organization) -> User:
    """Create test admin user."""
    user = User(
        organization_id=test_org.id,
        name="Admin Test",
        email="admin@test.com",
        password_hash=hash_password("Password123!"),
        role=UserRole.ADMIN.value,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def recruiter_user(db_session: AsyncSession, test_org: Organization) -> User:
    """Create test recruiter user."""
    user = User(
        organization_id=test_org.id,
        name="Recruiter Test",
        email="recruiter@test.com",
        password_hash=hash_password("Password123!"),
        role=UserRole.RECRUITER.value,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def interviewer_user(db_session: AsyncSession, test_org: Organization) -> User:
    """Create test interviewer user."""
    user = User(
        organization_id=test_org.id,
        name="Interviewer Test",
        email="interviewer@test.com",
        password_hash=hash_password("Password123!"),
        role=UserRole.INTERVIEWER.value,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def candidate_user(db_session: AsyncSession) -> User:
    """Create test candidate user and profile."""
    user = User(
        name="Candidate Test",
        email="candidate@test.com",
        password_hash=hash_password("Password123!"),
        role=UserRole.CANDIDATE.value,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    profile = CandidateProfile(
        user_id=user.id,
        phone="+1234567890",
        location="Remote",
        skills=["Python", "FastAPI", "React"],
        experience_years=4,
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def admin_headers(admin_user: User) -> dict:
    """Auth headers for admin user."""
    token = create_access_token(
        user_id=admin_user.id,
        role=admin_user.role,
        organization_id=admin_user.organization_id,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def recruiter_headers(recruiter_user: User) -> dict:
    """Auth headers for recruiter user."""
    token = create_access_token(
        user_id=recruiter_user.id,
        role=recruiter_user.role,
        organization_id=recruiter_user.organization_id,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def interviewer_headers(interviewer_user: User) -> dict:
    """Auth headers for interviewer user."""
    token = create_access_token(
        user_id=interviewer_user.id,
        role=interviewer_user.role,
        organization_id=interviewer_user.organization_id,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def candidate_headers(candidate_user: User) -> dict:
    """Auth headers for candidate user."""
    token = create_access_token(
        user_id=candidate_user.id,
        role=candidate_user.role,
        organization_id=None,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def published_job(db_session: AsyncSession, test_org: Organization, recruiter_user: User) -> Job:
    """Create a published job."""
    job = Job(
        organization_id=test_org.id,
        title="Senior Backend Engineer",
        description="Build scalable distributed systems with FastAPI and Postgres.",
        department="Engineering",
        employment_type=EmploymentType.FULL_TIME.value,
        work_mode=WorkMode.REMOTE.value,
        location="Remote, US",
        status=JobStatus.PUBLISHED.value,
        hiring_manager_id=recruiter_user.id,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job
