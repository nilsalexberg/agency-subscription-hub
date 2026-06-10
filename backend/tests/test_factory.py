"""
Tests for the admin router factory (build_router).

Uses two test-only SQLAlchemy models (Tag, Widget) with minimal Pydantic schemas to
exercise all five CRUD operations, auth enforcement, pagination, search, sort, override
map behavior, and relation display field serialization.
"""

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel
from sqlalchemy import ForeignKey, String, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.admin.contracts import RelationLoadConfig, ResourceConfig
from app.admin.factory import build_router
from app.core.deps import get_db
from app.core.security import create_access_token
from app.models.base import Base, TimestampMixin
from app.models.user import Role, User


# ── Test models ────────────────────────────────────────────────────────────────
# Registered with the shared Base so conftest's create_all includes these tables.


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)


class Widget(Base, TimestampMixin):
    __tablename__ = "widgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tag_id: Mapped[int | None] = mapped_column(ForeignKey("tags.id"), nullable=True)

    tag: Mapped[Tag | None] = relationship()


# ── Pydantic schemas ───────────────────────────────────────────────────────────


class WidgetRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    tag_id: int | None = None

    model_config = {"from_attributes": True}


class WidgetWrite(BaseModel):
    name: str
    description: str | None = None
    tag_id: int | None = None


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


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def base_config() -> ResourceConfig:
    return ResourceConfig(
        model=Widget,
        read_schema=WidgetRead,
        write_schema=WidgetWrite,
        prefix="/widgets",
        search_field="name",
    )


@pytest.fixture
def relation_config() -> ResourceConfig:
    return ResourceConfig(
        model=Widget,
        read_schema=WidgetRead,
        write_schema=WidgetWrite,
        prefix="/widgets",
        relations=[RelationLoadConfig(attribute="tag", display_field="label")],
    )


@pytest.fixture
async def factory_client(db_session, base_config):
    async with AsyncClient(
        transport=ASGITransport(app=_make_app(base_config, db_session)),
        base_url="http://test",
    ) as c:
        yield c


@pytest.fixture
async def relation_client(db_session, relation_config):
    async with AsyncClient(
        transport=ASGITransport(app=_make_app(relation_config, db_session)),
        base_url="http://test",
    ) as c:
        yield c


@pytest.fixture
async def admin_user(db_session) -> User:
    user = User(email="admin@factory.test", hashed_password="x", role=Role.ADMIN, is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def viewer_user(db_session) -> User:
    user = User(email="viewer@factory.test", hashed_password="x", role=Role.VIEWER, is_active=True)
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


# ── Auth enforcement ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_requires_auth(factory_client):
    res = await factory_client.get("/widgets/")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_retrieve_requires_auth(factory_client):
    res = await factory_client.get("/widgets/1")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_create_requires_admin(factory_client, viewer_token):
    res = await factory_client.post("/widgets/", json={"name": "w"}, headers=auth(viewer_token))
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_update_requires_admin(factory_client, viewer_token):
    res = await factory_client.put("/widgets/1", json={"name": "w"}, headers=auth(viewer_token))
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_delete_requires_admin(factory_client, viewer_token):
    res = await factory_client.delete("/widgets/1", headers=auth(viewer_token))
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_viewer_can_list(factory_client, viewer_token):
    res = await factory_client.get("/widgets/", headers=auth(viewer_token))
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_viewer_can_retrieve(factory_client, db_session, viewer_token):
    widget = Widget(name="readable")
    db_session.add(widget)
    await db_session.commit()
    await db_session.refresh(widget)

    res = await factory_client.get(f"/widgets/{widget.id}", headers=auth(viewer_token))
    assert res.status_code == 200


# ── List ───────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_empty(factory_client, admin_token):
    res = await factory_client.get("/widgets/", headers=auth(admin_token))
    assert res.status_code == 200
    body = res.json()
    assert body["items"] == []
    assert body["total"] == 0


@pytest.mark.asyncio
async def test_list_returns_records(factory_client, db_session, admin_token):
    db_session.add_all([Widget(name="Alpha"), Widget(name="Beta"), Widget(name="Gamma")])
    await db_session.commit()

    res = await factory_client.get("/widgets/", headers=auth(admin_token))
    body = res.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3
    assert {item["name"] for item in body["items"]} == {"Alpha", "Beta", "Gamma"}


@pytest.mark.asyncio
async def test_list_pagination_skip_limit(factory_client, db_session, admin_token):
    db_session.add_all([Widget(name=f"W{i}") for i in range(5)])
    await db_session.commit()

    res = await factory_client.get("/widgets/?skip=2&limit=2", headers=auth(admin_token))
    body = res.json()
    assert body["total"] == 5       # total is unaffected by pagination
    assert len(body["items"]) == 2


@pytest.mark.asyncio
async def test_list_search_filters_by_search_field(factory_client, db_session, admin_token):
    db_session.add_all([Widget(name="Foo"), Widget(name="Bar"), Widget(name="FooBar")])
    await db_session.commit()

    res = await factory_client.get("/widgets/?q=foo", headers=auth(admin_token))
    body = res.json()
    assert body["total"] == 2
    assert {item["name"] for item in body["items"]} == {"Foo", "FooBar"}


@pytest.mark.asyncio
async def test_list_sort_desc(factory_client, db_session, admin_token):
    db_session.add_all([Widget(name="A"), Widget(name="B"), Widget(name="C")])
    await db_session.commit()

    res = await factory_client.get("/widgets/?sort_by=name&sort_dir=desc", headers=auth(admin_token))
    names = [item["name"] for item in res.json()["items"]]
    assert names == ["C", "B", "A"]


@pytest.mark.asyncio
async def test_list_sort_invalid_column_falls_back_to_pk(factory_client, db_session, admin_token):
    db_session.add_all([Widget(name="A"), Widget(name="B")])
    await db_session.commit()

    # Invalid sort column must not crash — factory falls back to primary key order.
    res = await factory_client.get("/widgets/?sort_by=__class__", headers=auth(admin_token))
    assert res.status_code == 200
    assert res.json()["total"] == 2


# ── Retrieve ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_retrieve_returns_record(factory_client, db_session, admin_token):
    widget = Widget(name="target", description="details")
    db_session.add(widget)
    await db_session.commit()
    await db_session.refresh(widget)

    res = await factory_client.get(f"/widgets/{widget.id}", headers=auth(admin_token))
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == widget.id
    assert body["name"] == "target"
    assert body["description"] == "details"


@pytest.mark.asyncio
async def test_retrieve_not_found(factory_client, admin_token):
    res = await factory_client.get("/widgets/9999", headers=auth(admin_token))
    assert res.status_code == 404


# ── Create ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_persists_and_returns_record(factory_client, admin_token):
    res = await factory_client.post(
        "/widgets/", json={"name": "new widget", "description": "hi"}, headers=auth(admin_token)
    )
    assert res.status_code == 201
    body = res.json()
    assert isinstance(body["id"], int)
    assert body["name"] == "new widget"
    assert body["description"] == "hi"


@pytest.mark.asyncio
async def test_create_returns_422_for_invalid_body(factory_client, admin_token):
    res = await factory_client.post(
        "/widgets/", json={"description": "no name field"}, headers=auth(admin_token)
    )
    assert res.status_code == 422


# ── Update ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_modifies_record(factory_client, db_session, admin_token):
    widget = Widget(name="old", description="old desc")
    db_session.add(widget)
    await db_session.commit()
    await db_session.refresh(widget)

    res = await factory_client.put(
        f"/widgets/{widget.id}",
        json={"name": "new", "description": "new desc"},
        headers=auth(admin_token),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["name"] == "new"
    assert body["description"] == "new desc"


@pytest.mark.asyncio
async def test_update_not_found(factory_client, admin_token):
    res = await factory_client.put("/widgets/9999", json={"name": "x"}, headers=auth(admin_token))
    assert res.status_code == 404


# ── Delete ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_removes_record(factory_client, db_session, admin_token):
    widget = Widget(name="doomed")
    db_session.add(widget)
    await db_session.commit()
    await db_session.refresh(widget)

    res = await factory_client.delete(f"/widgets/{widget.id}", headers=auth(admin_token))
    assert res.status_code == 204

    result = await db_session.execute(select(Widget).where(Widget.id == widget.id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_not_found(factory_client, admin_token):
    res = await factory_client.delete("/widgets/9999", headers=auth(admin_token))
    assert res.status_code == 404


# ── Override map ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_override_replaces_default(db_session, admin_user):
    async def custom_list():
        return {"items": [{"id": 0, "name": "injected"}], "total": 1}

    config = ResourceConfig(
        model=Widget,
        read_schema=WidgetRead,
        write_schema=WidgetWrite,
        prefix="/widgets",
        overrides={"list": custom_list},
    )
    token = create_access_token(str(admin_user.id))

    async with AsyncClient(
        transport=ASGITransport(app=_make_app(config, db_session)),
        base_url="http://test",
    ) as c:
        res = await c.get("/widgets/", headers=auth(token))
        assert res.status_code == 200
        assert res.json()["items"][0]["name"] == "injected"


@pytest.mark.asyncio
async def test_create_override_replaces_default(db_session, admin_user):
    async def custom_create() -> WidgetRead:
        return WidgetRead(id=999, name="from override")

    config = ResourceConfig(
        model=Widget,
        read_schema=WidgetRead,
        write_schema=WidgetWrite,
        prefix="/widgets",
        overrides={"create": custom_create},
    )
    token = create_access_token(str(admin_user.id))

    async with AsyncClient(
        transport=ASGITransport(app=_make_app(config, db_session)),
        base_url="http://test",
    ) as c:
        res = await c.post("/widgets/", json={"name": "ignored"}, headers=auth(token))
        assert res.status_code == 201
        assert res.json()["id"] == 999
        assert res.json()["name"] == "from override"

        # Default handler was not called — nothing in the actual DB.
        result = await db_session.execute(select(Widget))
        assert result.scalars().all() == []


# ── Relation display fields ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_includes_relation_display_field(relation_client, db_session, admin_token):
    tag = Tag(label="python")
    db_session.add(tag)
    await db_session.commit()
    await db_session.refresh(tag)

    db_session.add(Widget(name="sdk", tag_id=tag.id))
    await db_session.commit()

    res = await relation_client.get("/widgets/", headers=auth(admin_token))
    assert res.status_code == 200
    assert res.json()["items"][0]["tag_label"] == "python"


@pytest.mark.asyncio
async def test_list_relation_display_field_is_null_when_fk_is_null(
    relation_client, db_session, admin_token
):
    db_session.add(Widget(name="untagged"))
    await db_session.commit()

    res = await relation_client.get("/widgets/", headers=auth(admin_token))
    assert res.json()["items"][0]["tag_label"] is None
