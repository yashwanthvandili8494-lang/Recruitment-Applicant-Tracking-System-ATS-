"""
Tests for dashboard metrics and reporting (/api/v1/dashboard).
"""

import pytest
from httpx import AsyncClient
from app.models.job import Job


@pytest.mark.asyncio
async def test_dashboard_overview(
    client: AsyncClient, published_job: Job, recruiter_headers: dict
):
    """Test dashboard overview metrics reflect database state."""
    response = await client.get("/api/v1/dashboard/overview", headers=recruiter_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_open_jobs" in data
    assert "total_applications" in data
    assert "applications_awaiting_review" in data
    assert "interviews_scheduled" in data
    assert "offers_pending" in data
    assert "candidates_hired" in data
    assert data["total_open_jobs"] >= 1


@pytest.mark.asyncio
async def test_dashboard_funnel(
    client: AsyncClient, published_job: Job, candidate_headers: dict, recruiter_headers: dict
):
    """Test recruitment funnel endpoint returns stage counts."""
    # Apply to have data in funnel
    await client.post(
        f"/api/v1/applications/jobs/{published_job.id}/apply",
        json={"cover_letter": "Funnel test application"},
        headers=candidate_headers,
    )

    response = await client.get("/api/v1/dashboard/recruitment-funnel", headers=recruiter_headers)
    assert response.status_code == 200
    stages = response.json()
    assert isinstance(stages, list)
    stage_names = [s["stage"] for s in stages]
    assert "applied" in stage_names


@pytest.mark.asyncio
async def test_dashboard_forbidden_for_candidates(
    client: AsyncClient, candidate_headers: dict
):
    """Test that candidate user cannot access internal recruiter dashboard."""
    response = await client.get("/api/v1/dashboard/overview", headers=candidate_headers)
    assert response.status_code == 403
