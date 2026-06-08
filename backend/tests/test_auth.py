import pytest
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Role, User


# ── POST /auth/login ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_login_success(client, db_session: AsyncSession):
    # Create user in database with mocked hash
    user = User(
        email="admin@test.com",
        hashed_password="hashed_pass123",  # Mocked hash
        role=Role.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    with patch("app.api.auth.verify_password", return_value=True):
        res = await client.post("/auth/login", json={"email": "admin@test.com", "password": "pass123"})
    assert res.status_code == 200
    assert "access_token" in res.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client, db_session: AsyncSession):
    user = User(
        email="admin@test.com",
        hashed_password="hashed_correct",
        role=Role.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    with patch("app.api.auth.verify_password", return_value=False):
        res = await client.post("/auth/login", json={"email": "admin@test.com", "password": "wrong"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client):
    res = await client.post("/auth/login", json={"email": "ghost@test.com", "password": "x"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(client, db_session: AsyncSession):
    user = User(
        email="inactive@test.com",
        hashed_password="hashed_pass123",
        role=Role.ADMIN,
        is_active=False,
    )
    db_session.add(user)
    await db_session.commit()

    with patch("app.api.auth.verify_password", return_value=True):
        res = await client.post("/auth/login", json={"email": "inactive@test.com", "password": "pass123"})
    assert res.status_code == 403


# ── POST /auth/register ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_first_user_becomes_admin(client, db_session: AsyncSession):
    # Database is empty at start of test
    with patch("app.services.user.hash_password", return_value="hashed_pass123"):
        res = await client.post(
            "/auth/register",
            json={"email": "admin@test.com", "password": "pass123"},
        )
    assert res.status_code == 201
    data = res.json()
    assert data["role"] == "admin"
    assert data["email"] == "admin@test.com"
    assert data["is_active"] is True

    # Verify user was actually created in database
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "admin@test.com"))
    db_user = result.scalar_one_or_none()
    assert db_user is not None
    assert db_user.role == Role.ADMIN


@pytest.mark.asyncio
async def test_register_closed_when_user_exists(client, db_session: AsyncSession):
    # Create first user
    user = User(
        email="first@test.com",
        hashed_password="hashed_pass123",
        role=Role.ADMIN,
    )
    db_session.add(user)
    await db_session.commit()

    # Try to register second user
    res = await client.post(
        "/auth/register",
        json={"email": "second@test.com", "password": "pass123"},
    )
    assert res.status_code == 403
    assert "Registration closed" in res.json()["detail"]
