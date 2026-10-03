"""
Tests for jobs management endpoints (/api/v1/jobs).
"""

import pytest
from httpx import AsyncClient
from app.models.job import Job


@pytest.mark.asyncio
async def test_list_public_jobs(client: AsyncClient, published_job: Job):
    """Test public careers endpoint returns only published jobs."""
    response = await client.get("/api/v1/jobs/public")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(j["id"] == published_job.id for j in data["jobs"])


@pytest.mark.asyncio
async def test_get_public_job_by_id(client: AsyncClient, published_job: Job):
    """Test getting single published job by ID."""
    response = await client.get(f"/api/v1/jobs/public/{published_job.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == published_job.id
    assert data["title"] == published_job.title


@pytest.mark.asyncio
async def test_create_job_as_recruiter(client: AsyncClient, recruiter_headers: dict):
    """Test recruiter can create a new job."""
    payload = {
        "title": "Full Stack Engineer",
        "description": "Develop modern web applications.",
        "responsibilities": "Code, review, deploy.",
        "requirements": "3+ years React and Python.",
        "department": "Engineering",
        "employment_type": "full_time",
        "work_mode": "remote",
        "location": "Remote",
    }
    response = await client.post("/api/v1/jobs", json=payload, headers=recruiter_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Full Stack Engineer"
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_candidate_cannot_create_job(client: AsyncClient, candidate_headers: dict):
    """Test candidate gets 403 when attempting to create a job."""
    payload = {
        "title": "Unauthorized Job",
        "description": "Should fail.",
    }
    response = await client.post("/api/v1/jobs", json=payload, headers=candidate_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_publish_and_close_job(client: AsyncClient, recruiter_headers: dict):
    """Test job lifecycle: draft -> publish -> close."""
    # 1. Create job
    create_res = await client.post(
        "/api/v1/jobs",
        json={"title": "DevOps Engineer", "description": "Manage cloud infra."},
        headers=recruiter_headers,
    )
    assert create_res.status_code == 201
    job_id = create_res.json()["id"]
    assert create_res.json()["status"] == "draft"

    # 2. Publish job
    pub_res = await client.post(f"/api/v1/jobs/{job_id}/publish", headers=recruiter_headers)
    assert pub_res.status_code == 200
    assert pub_res.json()["status"] == "published"

    # 3. Close job
    close_res = await client.post(f"/api/v1/jobs/{job_id}/close", headers=recruiter_headers)
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "closed"


@pytest.mark.asyncio
async def test_filter_jobs_by_department(client: AsyncClient, recruiter_headers: dict):
    """Test filtering jobs by department."""
    await client.post(
        "/api/v1/jobs",
        json={"title": "Marketing Lead", "description": "Lead campaigns.", "department": "Marketing"},
        headers=recruiter_headers,
    )

    response = await client.get("/api/v1/jobs?department=Marketing", headers=recruiter_headers)
    assert response.status_code == 200
    data = response.json()
    assert all(j["department"] == "Marketing" for j in data["jobs"])
