"""
Seed script — creates demo data for development and testing.

Usage:
    python -m app.seed

Creates: 1 organization, admin, recruiter, hiring manager, interviewer,
         5 candidates, 8 jobs, sample applications, interviews, and scorecards.

All data is fictional. Credentials are read from environment variables.
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime, timezone, timedelta, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings
from app.core.database import async_session_factory, engine, Base
from app.core.security import hash_password
from app.models import *  # noqa — ensures all models are registered
from app.models.enums import (
    UserRole, JobStatus, EmploymentType, WorkMode,
    ApplicationStatus, InterviewType, InterviewStatus, OfferStatus,
)

settings = get_settings()


async def seed():
    """Create all demo data inside a single transaction."""
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        try:
            # ───── Organization ─────
            org = Organization(
                name="TechCorp Solutions",
                slug="techcorp",
            )
            db.add(org)
            await db.flush()

            default_pw = hash_password(settings.DEMO_ADMIN_PASSWORD or "Demo1234!")

            # ───── Staff Users ─────
            admin = User(
                organization_id=org.id, name="Sarah Admin",
                email=settings.DEMO_ADMIN_EMAIL or "admin@recruitflow.dev",
                password_hash=default_pw, role=UserRole.ADMIN.value,
                is_active=True, is_verified=True,
            )
            recruiter = User(
                organization_id=org.id, name="Mark Recruiter",
                email="recruiter@recruitflow.dev",
                password_hash=default_pw, role=UserRole.RECRUITER.value,
                is_active=True, is_verified=True,
            )
            hiring_mgr = User(
                organization_id=org.id, name="Lisa Manager",
                email="manager@recruitflow.dev",
                password_hash=default_pw, role=UserRole.HIRING_MANAGER.value,
                is_active=True, is_verified=True,
            )
            interviewer = User(
                organization_id=org.id, name="David Interviewer",
                email="interviewer@recruitflow.dev",
                password_hash=default_pw, role=UserRole.INTERVIEWER.value,
                is_active=True, is_verified=True,
            )
            db.add_all([admin, recruiter, hiring_mgr, interviewer])
            await db.flush()

            # ───── Candidates ─────
            candidates = []
            candidate_data = [
                ("Alex Johnson", "alex@example.com", "San Francisco, CA", ["Python", "React", "AWS"], 5),
                ("Emma Williams", "emma@example.com", "New York, NY", ["Java", "Spring Boot", "Kubernetes"], 7),
                ("James Brown", "james@example.com", "Austin, TX", ["JavaScript", "Node.js", "MongoDB"], 3),
                ("Olivia Davis", "olivia@example.com", "Seattle, WA", ["Go", "Docker", "PostgreSQL"], 4),
                ("William Garcia", "william@example.com", "Chicago, IL", ["C#", ".NET", "Azure"], 6),
            ]
            for name, email, loc, skills, exp in candidate_data:
                user = User(
                    name=name, email=email, password_hash=default_pw,
                    role=UserRole.CANDIDATE.value, is_active=True, is_verified=True,
                )
                db.add(user)
                await db.flush()

                profile = CandidateProfile(
                    user_id=user.id, location=loc, skills=skills,
                    experience_years=exp,
                    education=[{"degree": "BS Computer Science", "university": "State University", "year": 2020 - exp}],
                    summary=f"Experienced software engineer with {exp} years of expertise in {', '.join(skills[:2])}.",
                )
                db.add(profile)
                candidates.append(user)

            await db.flush()

            # ───── Jobs ─────
            jobs_data = [
                ("Senior Backend Engineer", "Engineering", EmploymentType.FULL_TIME, WorkMode.HYBRID, "San Francisco, CA", 5, 10, 130000, 180000, JobStatus.PUBLISHED),
                ("Frontend Developer", "Engineering", EmploymentType.FULL_TIME, WorkMode.REMOTE, "Remote", 2, 5, 90000, 130000, JobStatus.PUBLISHED),
                ("DevOps Engineer", "Infrastructure", EmploymentType.FULL_TIME, WorkMode.ONSITE, "New York, NY", 3, 7, 120000, 160000, JobStatus.PUBLISHED),
                ("Product Manager", "Product", EmploymentType.FULL_TIME, WorkMode.HYBRID, "Seattle, WA", 4, 8, 140000, 190000, JobStatus.PUBLISHED),
                ("Data Scientist", "Data", EmploymentType.FULL_TIME, WorkMode.REMOTE, "Remote", 3, 6, 110000, 150000, JobStatus.PUBLISHED),
                ("QA Engineer", "Engineering", EmploymentType.CONTRACT, WorkMode.REMOTE, "Remote", 2, 5, 80000, 110000, JobStatus.DRAFT),
                ("UX Designer", "Design", EmploymentType.FULL_TIME, WorkMode.HYBRID, "Austin, TX", 3, 6, 100000, 140000, JobStatus.PUBLISHED),
                ("Technical Writer", "Documentation", EmploymentType.PART_TIME, WorkMode.REMOTE, "Remote", 1, 3, 60000, 80000, JobStatus.CLOSED),
            ]

            jobs = []
            for title, dept, emp_type, wm, loc, exp_min, exp_max, sal_min, sal_max, job_status in jobs_data:
                job = Job(
                    organization_id=org.id, title=title,
                    description=f"We are looking for a talented {title} to join our {dept} team. This is an exciting opportunity to work on cutting-edge projects.",
                    responsibilities=f"• Lead {dept.lower()} initiatives\n• Collaborate with cross-functional teams\n• Drive technical excellence\n• Mentor junior team members",
                    requirements=f"• {exp_min}+ years of relevant experience\n• Strong communication skills\n• Proven track record in {dept.lower()}\n• Bachelor's degree or equivalent",
                    preferred_skills=f"• Experience with agile methodologies\n• Open source contributions\n• Public speaking experience",
                    department=dept, employment_type=emp_type.value, work_mode=wm.value,
                    location=loc, experience_min=exp_min, experience_max=exp_max,
                    salary_min=sal_min, salary_max=sal_max, openings=2,
                    deadline=date.today() + timedelta(days=60),
                    hiring_manager_id=hiring_mgr.id, status=job_status.value,
                )
                db.add(job)
                jobs.append(job)

            await db.flush()

            # ───── Applications ─────
            now = datetime.now(timezone.utc)
            app_configs = [
                (0, 0, ApplicationStatus.INTERVIEW_COMPLETED),
                (0, 1, ApplicationStatus.UNDER_REVIEW),
                (0, 2, ApplicationStatus.SHORTLISTED),
                (1, 0, ApplicationStatus.APPLIED),
                (1, 3, ApplicationStatus.SHORTLISTED),
                (2, 1, ApplicationStatus.INTERVIEW_SCHEDULED),
                (3, 2, ApplicationStatus.APPLIED),
                (4, 0, ApplicationStatus.OFFERED),
                (4, 4, ApplicationStatus.HIRED),
            ]

            applications = []
            for cand_idx, job_idx, app_status in app_configs:
                app_id = str(uuid.uuid4())
                application = Application(
                    id=app_id,
                    job_id=jobs[job_idx].id,
                    candidate_id=candidates[cand_idx].id,
                    status=app_status.value,
                    cover_letter=f"I am very excited to apply for the {jobs[job_idx].title} position. My experience aligns well with your requirements.",
                    applied_at=now - timedelta(days=len(applications) * 3 + 5),
                )
                db.add(application)
                applications.append(application)

                # Add status history
                history = ApplicationStatusHistory(
                    id=str(uuid.uuid4()),
                    application_id=app_id,
                    previous_status=None,
                    new_status=ApplicationStatus.APPLIED.value,
                    changed_by=candidates[cand_idx].id,
                    reason="Application submitted",
                )
                db.add(history)

            await db.flush()

            # ───── Interviews ─────
            interview = Interview(
                application_id=applications[0].id,
                interview_round=1,
                interview_type=InterviewType.VIDEO.value,
                start_time=now + timedelta(days=2, hours=10),
                end_time=now + timedelta(days=2, hours=11),
                timezone="America/Los_Angeles",
                meeting_location="https://meet.google.com/abc-defg-hij",
                status=InterviewStatus.COMPLETED.value,
            )
            db.add(interview)
            await db.flush()

            participant = InterviewParticipant(
                interview_id=interview.id, user_id=interviewer.id, role="interviewer"
            )
            db.add(participant)

            # Scorecard
            feedback = InterviewFeedback(
                interview_id=interview.id,
                interviewer_id=interviewer.id,
                criterion_scores={
                    "technical_skills": 4,
                    "problem_solving": 5,
                    "communication": 4,
                    "experience": 4,
                    "culture_fit": 5,
                },
                strengths="Strong problem-solving abilities. Excellent communication skills. Deep knowledge of distributed systems.",
                concerns="Could improve on system design documentation practices.",
                recommendation="strong_yes",
                overall_notes="Highly recommend for next round. Candidate demonstrated exceptional technical depth.",
            )
            db.add(feedback)

            # Upcoming interview
            interview2 = Interview(
                application_id=applications[5].id,
                interview_round=1,
                interview_type=InterviewType.TECHNICAL.value,
                start_time=now + timedelta(days=5, hours=14),
                end_time=now + timedelta(days=5, hours=15, minutes=30),
                timezone="America/New_York",
                meeting_location="https://zoom.us/j/123456789",
                status=InterviewStatus.SCHEDULED.value,
            )
            db.add(interview2)
            await db.flush()

            participant2 = InterviewParticipant(
                interview_id=interview2.id, user_id=interviewer.id, role="interviewer"
            )
            db.add(participant2)

            # ───── Offer ─────
            offer = Offer(
                application_id=applications[7].id,
                compensation_details={
                    "base_salary": 155000,
                    "currency": "USD",
                    "signing_bonus": 15000,
                    "equity": "0.05%",
                    "benefits": "Health, Dental, Vision, 401k matching, unlimited PTO",
                },
                status=OfferStatus.SENT.value,
                issued_by=recruiter.id,
                approved_by=hiring_mgr.id,
                issued_at=now - timedelta(days=2),
                expires_at=now + timedelta(days=12),
                notes="Competitive offer for Senior Backend Engineer position.",
            )
            db.add(offer)

            await db.commit()
            print("[SUCCESS] Seed data created successfully!")
            print(f"\nDemo Credentials (all accounts use the same password):")
            print(f"   Admin:        {settings.DEMO_ADMIN_EMAIL}")
            print(f"   Recruiter:    recruiter@recruitflow.dev")
            print(f"   Manager:      manager@recruitflow.dev")
            print(f"   Interviewer:  interviewer@recruitflow.dev")
            print(f"   Candidates:   alex@example.com, emma@example.com, etc.")
            print(f"\n   Password:     {settings.DEMO_ADMIN_PASSWORD or 'Demo1234!'}")

        except Exception as e:
            await db.rollback()
            print(f"[ERROR] Seed failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed())
