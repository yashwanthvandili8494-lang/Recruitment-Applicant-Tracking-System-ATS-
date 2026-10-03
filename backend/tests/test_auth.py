"""
Tests for authentication endpoints (/api/v1/auth).
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_candidate_success(client: AsyncClient):
    """Test candidate self-registration."""
    payload = {
        "name": "Jane Doe",
        "email": "janedoe@example.com",
        "password": "SecurePassword123!",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["email"] == "janedoe@example.com"
    assert data["role"] == "candidate"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test that registering duplicate email returns 409 Conflict."""
    payload = {
        "name": "First User",
        "email": "duplicate@example.com",
        "password": "Password123!",
    }
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test login with valid credentials."""
    # First register
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Login User", "email": "login@example.com", "password": "Secret123!"},
    )

    # Login
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "Secret123!"},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["expires_in"] > 0
    # Also verify cookies
    assert "access_token" in login_res.cookies


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """Test login with wrong password returns 401."""
    await client.post(
        "/api/v1/auth/register",
        json={"name": "User", "email": "wrongpass@example.com", "password": "CorrectPassword123!"},
    )

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpass@example.com", "password": "WrongPassword!"},
    )
    assert login_res.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_me(client: AsyncClient, candidate_headers: dict):
    """Test getting profile of logged-in user."""
    response = await client.get("/api/v1/auth/me", headers=candidate_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "candidate@test.com"
    assert data["role"] == "candidate"


@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(client: AsyncClient):
    """Test that protected endpoint without token returns 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
