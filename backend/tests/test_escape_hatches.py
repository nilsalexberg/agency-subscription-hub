"""
Tests for the router factory override escape hatches (Step 16).

Verifies:
  - All five CRUD operations accept a non-None callable override that fully
    replaces the default handler.
  - Auth dependencies are enforced at the route level even when an override
    is installed (factory wraps the override, not the other way around).
  - A realistic domain-level create override can perform its own DB work and
    return a custom response without triggering the generic factory handler.
  - None values in the overrides map fall back to the factory default.
"""

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import pytest
from fastapi import FastAPI, HTTPException, status
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel
from sqlalchemy import String, select
from sqlalchemy.orm import Mapped, mapped_column

from app.admin.contracts import ResourceConfig
from app.admin.factory import build_router
from app.core.deps import DB, get_db
from app.core.security import create_access_token
from app.models.base import Base
from app.models.user import Role, User


# ── Test model ─────────────────────────────────────────────────────────────────


class Product(Base):
    """Minimal model used exclusively in this test module."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(50), nullable=True)


class ProductRead(BaseModel):
    id: int
    name: str
    sku: str | None = None

    model_config = {"from_attributes": True}


class ProductWrite(BaseModel):
    name: str
    sku: str | None = None


# ── Helpers ────────────────────────────────────────────────────────────────────


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _make_app(config: ResourceConfig, db_session) -> FastAPI:
    app = FastAPI()
    app.include_router(build_router(config))

    async def _get_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_db
    return app


BASE_CONFIG = ResourceConfig(
    model=Product,
    read_schema=ProductRead,
    write_schema=ProductWrite,
    prefix="/products",
    search_field="name",
)


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
async def admin_user(db_session) -> User:
    user = User(
        email="admin@escapehatches.test",
        hashed_password="x",
        role=Role.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def viewer_user(db_session) -> User:
    user = User(
        email="viewer@escapehatches.test",
        hashed_password="x",
        role=Role.VIEWER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user) -> str:
    return create_access_token(str(admin_user.id))


@pytest.fixture
def viewer_token(viewer_user) -> str:
    return create_access_token(str(viewer_user.id))


# ── Retrieve override ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_retrieve_override_replaces_default(db_session, admin_user):
    """Custom retrieve handler returns a synthesized record; DB is not queried."""
    invocations: list[int] = []

    async def custom_retrieve(record_id: int, db: DB) -> ProductRead:
        invocations.append(record_id)
        return ProductRead(id=record_id, name="from-override", sku="OVERRIDE")

    config = ResourceConfig(
        **{**BASE_CONFIG.__dict__, "overrides": {"retrieve": custom_retrieve}},
    )
    token = create_access_token(str(admin_user.id))

    async with AsyncClient(
        transport=ASGITransport(app=_make_app(config, db_session)),
        base_url="http://test",
    ) as c:
        res = await c.get("/products/42", headers=auth(token))

    assert res.status_code == 200
    assert res.json()["name"] == "from-override"
    assert res.json()["sku"] == "OVERRIDE"
    assert invocations == [42]


@pytest.mark.asyncio
async def test_retrieve_override_auth_enforced(db_session):
    """Auth dependency is applied even when retrieve is overridden."""
    async def custom_retrieve(record_id: int) -> ProductRead:  # pragma: no cover
        return ProductRead(id=record_id, name="should-not-reach")

    config = ResourceConfig(
        **{**BASE_CONFIG.__dict__, "overrides": {"retrieve": custom_retrieve}},
    )

    async with AsyncClient(
        transport=ASGITransport(app=_make_app(config, db_session)),
        base_url="http://test",
    ) as c:
        res = await c.get("/products/1")

    assert res.status_code == 401


# ── Update override ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_override_replaces_default(db_session, admin_user, admin_token):
    """Custom update handler runs instead of generic PUT; DB remains unchanged."""
    product = Product(name="original", sku="SKU-001")
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    update_calls: list[dict] = []

    async def custom_update(record_id: int, db: DB) -> ProductRead:
        update_calls.append({"id": record_id})
        return ProductRead(id=record_id, name="custom-updated")

    config = ResourceConfig(
        **{**BASE_CONFIG.__dict__, "overrides": {"update": custom_update}},
    )

    async with AsyncClient(
        transport=ASGITransport(app=_make_app(config, db_session)),
        base_url="http://test",
    ) as c:
        res = await c.put(
            f"/products/{product.id}",
            json={"name": "attempted-change"},
            headers=auth(admin_token),
        )

    assert res.status_code == 200
    assert res.json()["name"] == "custom-updated"
    assert update_calls == [{"id": product.id}]

    # Default handler never ran — DB record unchanged.
    db_product = (
        await db_session.execute(select(Product).where(Product.id == product.id))
    ).scalar_one()
    assert db_product.name == "original"


@pytest.mark.asyncio
async def test_update_override_requires_admin(db_session, viewer_token):
    """Admin-only auth is enforced on update even with override installed."""
    async def custom_update(record_id: int) -> ProductRead:  # pragma: no cover
        return ProductRead(id=record_id, name="unreachable")

    config = ResourceConfig(
        **{**BASE_CONFIG.__dict__, "overrides": {"update": custom_update}},
    )

    async with AsyncClient(
        transport=ASGITransport(app=_make_app(config, db_session)),
        base_url="http://test",
    ) as c:
        res = await c.put(
            "/products/1",
            json={"name": "x"},
            headers=auth(viewer_token),
        )

    assert res.status_code == 403


# ── Delete override ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_override_replaces_default(db_session, admin_user, admin_token):
    """Custom delete handler runs instead of the default; record survives in DB."""
    product = Product(name="survivor", sku="SKU-SURVIVE")
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    delete_calls: list[int] = []

    async def custom_delete(record_id: int) -> None:
        # Intentionally does NOT delete from DB — simulates soft-delete, audit, etc.
        delete_calls.append(record_id)

    config = ResourceConfig(
        **{**BASE_CONFIG.__dict__, "overrides": {"delete": custom_delete}},
    )

    async with AsyncClient(
        transport=ASGITransport(app=_make_app(config, db_session)),
        base_url="http://test",
    ) as c:
        res = await c.delete(f"/products/{product.id}", headers=auth(admin_token))

    assert res.status_code == 204
    assert delete_calls == [product.id]

    # Default handler never ran — record still in DB.
    surviving = (
        await db_session.execute(select(Product).where(Product.id == product.id))
    ).scalar_one_or_none()
    assert surviving is not None


@pytest.mark.asyncio
async def test_delete_override_requires_admin(db_session, viewer_token):
    """Admin-only auth is enforced on delete even with override installed."""
    async def custom_delete(record_id: int) -> None:  # pragma: no cover
        pass

    config = ResourceConfig(
        **{**BASE_CONFIG.__dict__, "overrides": {"delete": custom_delete}},
    )

    async with AsyncClient(
        transport=ASGITransport(app=_make_app(config, db_session)),
        base_url="http://test",
    ) as c:
        res = await c.delete("/products/1", headers=auth(viewer_token))

    assert res.status_code == 403


# ── None value falls back to factory default ───────────────────────────────────


@pytest.mark.asyncio
async def test_none_override_uses_factory_default(db_session, admin_token):
    """
    Explicit None in the overrides map is equivalent to the key being absent
    — the factory default handler is used for that operation.
    """
    config = ResourceConfig(
        **{**BASE_CONFIG.__dict__, "overrides": {"create": None}},
    )

    async with AsyncClient(
        transport=ASGITransport(app=_make_app(config, db_session)),
        base_url="http://test",
    ) as c:
        res = await c.post(
            "/products/",
            json={"name": "created-via-default", "sku": "DEF-001"},
            headers=auth(admin_token),
        )

    assert res.status_code == 201
    assert res.json()["name"] == "created-via-default"

    # Factory default DID run — record is in DB.
    product = (
        await db_session.execute(
            select(Product).where(Product.name == "created-via-default")
        )
    ).scalar_one_or_none()
    assert product is not None
    assert product.sku == "DEF-001"


# ── Domain-level create override (Efí-style pattern) ──────────────────────────


@pytest.mark.asyncio
async def test_domain_create_override_performs_custom_logic_and_persists(
    db_session, admin_token
):
    """
    A realistic override: validates input, derives a field value (simulating
    an external API call that returns a checkout URL), inserts the record
    with the derived value, and returns the enriched response.

    This mirrors the Efí client-create pattern described in Step 16.
    """
    created_skus: list[str] = []

    async def domain_create(db: DB) -> ProductRead:
        # Simulate external service call: derive SKU from a naming scheme.
        derived_sku = "EFI-" + "CHECKOUT-12345"
        created_skus.append(derived_sku)

        product = Product(name="Checkout Product", sku=derived_sku)
        db.add(product)
        await db.commit()
        await db.refresh(product)
        return ProductRead.model_validate(product, from_attributes=True)

    config = ResourceConfig(
        **{**BASE_CONFIG.__dict__, "overrides": {"create": domain_create}},
    )

    async with AsyncClient(
        transport=ASGITransport(app=_make_app(config, db_session)),
        base_url="http://test",
    ) as c:
        res = await c.post(
            "/products/",
            json={"name": "ignored-by-override"},
            headers=auth(admin_token),
        )

    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "Checkout Product"
    assert body["sku"] == "EFI-CHECKOUT-12345"
    assert created_skus == ["EFI-CHECKOUT-12345"]

    # Record persisted by the override handler.
    product = (
        await db_session.execute(
            select(Product).where(Product.sku == "EFI-CHECKOUT-12345")
        )
    ).scalar_one_or_none()
    assert product is not None
    assert product.name == "Checkout Product"


@pytest.mark.asyncio
async def test_domain_create_override_auth_enforced(db_session, viewer_token):
    """Admin-only guard is applied even when create is replaced by domain logic."""
    async def domain_create() -> ProductRead:  # pragma: no cover
        return ProductRead(id=1, name="unreachable")

    config = ResourceConfig(
        **{**BASE_CONFIG.__dict__, "overrides": {"create": domain_create}},
    )

    async with AsyncClient(
        transport=ASGITransport(app=_make_app(config, db_session)),
        base_url="http://test",
    ) as c:
        res = await c.post(
            "/products/",
            json={},
            headers=auth(viewer_token),
        )

    assert res.status_code == 403


# ── Override raises HTTP exception ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_override_can_raise_http_exception(db_session, admin_token):
    """Override handlers that raise HTTPException are handled correctly by FastAPI."""
    async def strict_retrieve(record_id: int) -> ProductRead:
        if record_id != 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only record 1 allowed",
            )
        return ProductRead(id=1, name="allowed")

    config = ResourceConfig(
        **{**BASE_CONFIG.__dict__, "overrides": {"retrieve": strict_retrieve}},
    )

    async with AsyncClient(
        transport=ASGITransport(app=_make_app(config, db_session)),
        base_url="http://test",
    ) as c:
        allowed = await c.get("/products/1", headers=auth(admin_token))
        denied = await c.get("/products/2", headers=auth(admin_token))

    assert allowed.status_code == 200
    assert allowed.json()["name"] == "allowed"
    assert denied.status_code == 403
    assert denied.json()["detail"] == "Only record 1 allowed"
