"""
Tests for the central admin resource registry (app/resources.py).

Verifies registry structure, /admin prefix mounting, read-only 405 enforcement,
and that all list endpoints exist and require authentication.
"""

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import pytest

from app.core.security import create_access_token
from app.models.user import Role, User
from app.resources import RESOURCE_CONFIGS

_EXPECTED_PREFIXES = {
    "/recipients",
    "/split-configs",
    "/plans",
    "/clients",
    "/payments",
    "/audit-logs",
    "/users",
}

_READ_ONLY_PREFIXES = {"/payments", "/audit-logs"}


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Registry structure ─────────────────────────────────────────────────────────


def test_resource_config_count():
    assert len(RESOURCE_CONFIGS) == 7


def test_all_expected_prefixes_registered():
    registered = {c.prefix for c in RESOURCE_CONFIGS}
    assert registered == _EXPECTED_PREFIXES


def test_all_configs_have_required_fields():
    for config in RESOURCE_CONFIGS:
        assert config.model is not None, f"{config.prefix}: model missing"
        assert config.read_schema is not None, f"{config.prefix}: read_schema missing"
        assert config.write_schema is not None, f"{config.prefix}: write_schema missing"
        assert config.prefix.startswith("/"), f"{config.prefix}: must start with '/'"


def test_read_only_resources_override_all_write_operations():
    read_only = [c for c in RESOURCE_CONFIGS if c.prefix in _READ_ONLY_PREFIXES]
    assert len(read_only) == 2
    for config in read_only:
        for op in ("create", "update", "delete"):
            assert config.overrides.get(op) is not None, (
                f"{config.prefix}: missing override for '{op}'"
            )


def test_user_resource_overrides_create():
    user_config = next(c for c in RESOURCE_CONFIGS if c.prefix == "/users")
    assert user_config.overrides.get("create") is not None


def test_writable_resources_have_no_write_overrides():
    writable_prefixes = _EXPECTED_PREFIXES - _READ_ONLY_PREFIXES - {"/users"}
    writable = [c for c in RESOURCE_CONFIGS if c.prefix in writable_prefixes]
    assert len(writable) == 4
    for config in writable:
        for op in ("create", "update", "delete"):
            assert config.overrides.get(op) is None, (
                f"{config.prefix}: unexpected override for '{op}'"
            )


# ── Route mounting and auth ────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "/api/admin/recipients/",
        "/api/admin/split-configs/",
        "/api/admin/plans/",
        "/api/admin/clients/",
        "/api/admin/payments/",
        "/api/admin/audit-logs/",
        "/api/admin/users/",
    ],
)
async def test_list_route_mounted_and_requires_auth(client, path):
    """401 confirms route exists and auth is enforced; 404 would mean not mounted."""
    res = await client.get(path)
    assert res.status_code == 401, (
        f"{path}: expected 401 (auth required), got {res.status_code}"
    )


# ── Read-only 405 enforcement ──────────────────────────────────────────────────


@pytest.fixture
async def admin_token(db_session) -> str:
    user = User(
        email="admin@resources.test",
        hashed_password="x",
        role=Role.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return create_access_token(str(user.id))


@pytest.mark.asyncio
@pytest.mark.parametrize("prefix", ["/api/admin/payments", "/api/admin/audit-logs"])
async def test_read_only_create_returns_405(client, admin_token, prefix):
    res = await client.post(f"{prefix}/", json={}, headers=_auth(admin_token))
    assert res.status_code == 405


@pytest.mark.asyncio
@pytest.mark.parametrize("prefix", ["/api/admin/payments", "/api/admin/audit-logs"])
async def test_read_only_update_returns_405(client, admin_token, prefix):
    res = await client.put(f"{prefix}/1", json={}, headers=_auth(admin_token))
    assert res.status_code == 405


@pytest.mark.asyncio
@pytest.mark.parametrize("prefix", ["/api/admin/payments", "/api/admin/audit-logs"])
async def test_read_only_delete_returns_405(client, admin_token, prefix):
    res = await client.delete(f"{prefix}/1", headers=_auth(admin_token))
    assert res.status_code == 405


@pytest.mark.asyncio
async def test_user_create_returns_405(client, admin_token):
    res = await client.post(
        "/api/admin/users/",
        json={"email": "new@test.com", "role": "viewer", "is_active": True},
        headers=_auth(admin_token),
    )
    assert res.status_code == 405


@pytest.mark.asyncio
async def test_read_only_list_and_retrieve_still_work(client, admin_token):
    """Read-only means no writes — list and retrieve must still function."""
    res = await client.get("/api/admin/payments/", headers=_auth(admin_token))
    assert res.status_code == 200
    body = res.json()
    assert body["items"] == []
    assert body["total"] == 0
