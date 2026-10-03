"""
Tests for interview scheduling and scorecards (/api/v1/interviews).
"""

from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient
from app.models.job import Job
from app.models.user import User


@pytest.mark.asyncio
async def test_schedule_interview_and_submit_feedback(
    client: AsyncClient,
    published_job: Job,
    candidate_headers: dict,
    recruiter_headers: dict,
    interviewer_headers: dict,
    interviewer_user: User,
):
    """Test full interview flow: scheduling, listing, and scorecard feedback submission."""
    # 1. Candidate applies
    apply_res = await client.post(
        f"/api/v1/applications/jobs/{published_job.id}/apply",
        json={"cover_letter": "Applying for interview test"},
        headers=candidate_headers,
    )
    assert apply_res.status_code == 201
    app_id = apply_res.json()["id"]

    # 2. Recruiter schedules interview
    start = datetime.now(timezone.utc) + timedelta(days=2)
    end = start + timedelta(hours=1)
    sched_payload = {
        "interview_round": 1,
        "interview_type": "video",
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "timezone": "UTC",
        "meeting_location": "https://meet.google.com/abc-defg-hij",
        "notes": "Round 1 Technical Architecture Screen",
        "interviewer_ids": [interviewer_user.id],
    }
    sched_res = await client.post(
        f"/api/v1/interviews/applications/{app_id}/schedule",
        json=sched_payload,
        headers=recruiter_headers,
    )
    assert sched_res.status_code == 201
    interview_data = sched_res.json()
    interview_id = interview_data["id"]
    assert interview_data["interview_round"] == 1
    assert interview_data["status"] == "scheduled"

    # 3. Interviewer submits scorecard feedback
    feedback_payload = {
        "criterion_scores": {
            "technical_competence": 5,
            "problem_solving": 4,
            "system_design": 5,
            "communication": 4,
        },
        "strengths": "Strong knowledge of async I/O and PostgreSQL concurrency models.",
        "concerns": "Could be more familiar with Kubernetes operators.",
        "recommendation": "strong_yes",
        "overall_notes": "Exceeded expectations for technical depth.",
    }
    fb_res = await client.post(
        f"/api/v1/interviews/{interview_id}/feedback",
        json=feedback_payload,
        headers=interviewer_headers,
    )
    assert fb_res.status_code == 201
    fb_data = fb_res.json()
    assert fb_data["recommendation"] == "strong_yes"
    assert fb_data["criterion_scores"]["technical_competence"] == 5

    # 4. View feedback list
    view_fb_res = await client.get(
        f"/api/v1/interviews/{interview_id}/feedback",
        headers=recruiter_headers,
    )
    assert view_fb_res.status_code == 200
    all_fb = view_fb_res.json()
    assert len(all_fb) == 1
    assert all_fb[0]["interviewer_id"] == interviewer_user.id
