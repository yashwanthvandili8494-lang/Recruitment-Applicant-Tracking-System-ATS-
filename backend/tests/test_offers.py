"""
Tests for offer workflow (/api/v1/offers).
"""

from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient
from app.models.job import Job


@pytest.mark.asyncio
async def test_offer_lifecycle(
    client: AsyncClient,
    published_job: Job,
    candidate_headers: dict,
    recruiter_headers: dict,
    admin_headers: dict,
):
    """Test full offer lifecycle: create -> approve -> send -> candidate accepts."""
    # 1. Candidate applies
    apply_res = await client.post(
        f"/api/v1/applications/jobs/{published_job.id}/apply",
        json={"cover_letter": "Applying for offer test"},
        headers=candidate_headers,
    )
    assert apply_res.status_code == 201
    app_id = apply_res.json()["id"]

    # 2. Recruiter creates draft offer
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    offer_payload = {
        "compensation_details": {
            "base_salary": 145000,
            "currency": "USD",
            "equity_shares": 5000,
            "signing_bonus": 15000,
        },
        "notes": "Offer subject to standard background checks.",
        "expires_at": expires.isoformat(),
    }
    create_offer_res = await client.post(
        f"/api/v1/offers/applications/{app_id}/offers",
        json=offer_payload,
        headers=recruiter_headers,
    )
    assert create_offer_res.status_code == 201
    offer_data = create_offer_res.json()
    offer_id = offer_data["id"]
    assert offer_data["status"] == "draft"

    # 3. Recruiter sends offer for approval
    submit_res = await client.post(
        f"/api/v1/offers/{offer_id}/send",
        headers=recruiter_headers,
    )
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] == "pending_approval"

    # 4. Admin approves offer (status becomes sent)
    approve_res = await client.post(
        f"/api/v1/offers/{offer_id}/approve",
        headers=admin_headers,
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "sent"

    # 5. Candidate responds: accepts offer
    respond_res = await client.post(
        f"/api/v1/offers/{offer_id}/respond",
        json={"accepted": True},
        headers=candidate_headers,
    )
    assert respond_res.status_code == 200
    assert respond_res.json()["status"] == "accepted"
