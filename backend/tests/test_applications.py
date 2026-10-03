"""
Tests for application workflows (/api/v1/applications).
"""

import pytest
from httpx import AsyncClient
from app.models.job import Job


@pytest.mark.asyncio
async def test_apply_for_job_success(
    client: AsyncClient, published_job: Job, candidate_headers: dict
):
    """Test candidate successfully applies for a published job."""
    payload = {
        "cover_letter": "I am thrilled to apply for this backend position.",
    }
    response = await client.post(
        f"/api/v1/applications/jobs/{published_job.id}/apply",
        json=payload,
        headers=candidate_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["job_id"] == published_job.id
    assert data["status"] == "applied"
    assert data["cover_letter"] == payload["cover_letter"]


@pytest.mark.asyncio
async def test_duplicate_application_prevented(
    client: AsyncClient, published_job: Job, candidate_headers: dict
):
    """Test that applying twice to the same job returns 409 Conflict."""
    payload = {"cover_letter": "First submission"}
    res1 = await client.post(
        f"/api/v1/applications/jobs/{published_job.id}/apply",
        json=payload,
        headers=candidate_headers,
    )
    assert res1.status_code == 201

    res2 = await client.post(
        f"/api/v1/applications/jobs/{published_job.id}/apply",
        json=payload,
        headers=candidate_headers,
    )
    assert res2.status_code == 409
    assert "already applied" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_candidate_cannot_apply_to_draft_job(
    client: AsyncClient, recruiter_headers: dict, candidate_headers: dict
):
    """Test applying to non-published job returns 404."""
    create_res = await client.post(
        "/api/v1/jobs",
        json={"title": "Internal Draft Job", "description": "Not yet public."},
        headers=recruiter_headers,
    )
    draft_job_id = create_res.json()["id"]

    response = await client.post(
        f"/api/v1/applications/jobs/{draft_job_id}/apply",
        json={"cover_letter": "Hello"},
        headers=candidate_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_application_status_transition_and_history(
    client: AsyncClient, published_job: Job, candidate_headers: dict, recruiter_headers: dict
):
    """Test status pipeline transitions and status history audit."""
    # 1. Apply
    apply_res = await client.post(
        f"/api/v1/applications/jobs/{published_job.id}/apply",
        json={"cover_letter": "Test"},
        headers=candidate_headers,
    )
    app_id = apply_res.json()["id"]

    # 2. Transition applied -> under_review
    update_res = await client.patch(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "under_review", "reason": "Resume looks promising"},
        headers=recruiter_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "under_review"

    # 3. Transition under_review -> shortlisted
    update_res2 = await client.patch(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "shortlisted", "reason": "Matches all criteria"},
        headers=recruiter_headers,
    )
    assert update_res2.status_code == 200
    assert update_res2.json()["status"] == "shortlisted"

    # 4. Check status history
    hist_res = await client.get(
        f"/api/v1/applications/{app_id}/history",
        headers=recruiter_headers,
    )
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) >= 2


@pytest.mark.asyncio
async def test_candidate_withdraw_application(
    client: AsyncClient, published_job: Job, candidate_headers: dict
):
    """Test candidate can withdraw their application."""
    apply_res = await client.post(
        f"/api/v1/applications/jobs/{published_job.id}/apply",
        json={"cover_letter": "Test"},
        headers=candidate_headers,
    )
    app_id = apply_res.json()["id"]

    withdraw_res = await client.post(
        f"/api/v1/applications/{app_id}/withdraw",
        headers=candidate_headers,
    )
    assert withdraw_res.status_code == 200
    assert "withdrawn" in withdraw_res.json()["message"].lower()
