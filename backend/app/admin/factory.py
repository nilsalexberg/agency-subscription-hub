"""
Router factory for the schema-driven admin panel.

Accepts one ResourceConfig and returns an APIRouter with five standard CRUD routes.
Each operation checks the override map first; a non-None callable replaces the default
handler for that operation. Auth is always enforced at the route level, even for
override handlers.

Must not import any resource-specific module — operates purely on the model class
and Pydantic schemas passed through ResourceConfig.

Note: "from __future__ import annotations" is intentionally absent. Handler factories
patch __annotations__ at runtime to inject dynamic Pydantic body types (e.g. the
write_schema captured from config). Lazy string annotations would break that mechanism.
"""

from typing import Any, Literal, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy import inspect as sa_inspect
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import DB, get_current_user, require_admin
from .contracts import ResourceConfig


def build_router(config: ResourceConfig) -> APIRouter:
    """
    Return an APIRouter for one admin resource.

    Five routes are registered: list, retrieve, create, update, delete.
    Entries in config.overrides with a non-None callable replace the corresponding
    default handler. Auth dependencies are always applied at the route level.
    """
    tag = config.prefix.strip("/")
    router = APIRouter(prefix=config.prefix, tags=[tag])
    overrides = config.overrides

    router.add_api_route(
        "/",
        overrides.get("list") or _make_list_handler(config),
        methods=["GET"],
        dependencies=[Depends(get_current_user)],
        summary=f"List {tag}",
    )
    router.add_api_route(
        "/{record_id}",
        overrides.get("retrieve") or _make_retrieve_handler(config),
        methods=["GET"],
        dependencies=[Depends(get_current_user)],
        response_model=config.read_schema,
        summary=f"Get {tag}",
    )
    router.add_api_route(
        "/",
        overrides.get("create") or _make_create_handler(config),
        methods=["POST"],
        dependencies=[Depends(require_admin)],
        response_model=config.read_schema,
        status_code=status.HTTP_201_CREATED,
        summary=f"Create {tag}",
    )
    router.add_api_route(
        "/{record_id}",
        overrides.get("update") or _make_update_handler(config),
        methods=["PUT"],
        dependencies=[Depends(require_admin)],
        response_model=config.read_schema,
        summary=f"Update {tag}",
    )
    router.add_api_route(
        "/{record_id}",
        overrides.get("delete") or _make_delete_handler(config),
        methods=["DELETE"],
        dependencies=[Depends(require_admin)],
        status_code=status.HTTP_204_NO_CONTENT,
        summary=f"Delete {tag}",
    )

    return router


# ── Handler factories ──────────────────────────────────────────────────────────


def _make_list_handler(config: ResourceConfig):
    model = config.model
    read_schema = config.read_schema
    search_field = config.search_field
    relations = list(config.relations)

    # Computed once at factory time — avoids per-request mapper inspection.
    mapper = sa_inspect(model)
    sortable_columns = frozenset(attr.key for attr in mapper.column_attrs)
    pk_attr_name = next(
        attr.key
        for attr in mapper.column_attrs
        if any(col.primary_key for col in attr.columns)
    )

    async def list_handler(
        db: DB,
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=200),
        q: Optional[str] = Query(None),
        sort_by: Optional[str] = Query(None),
        sort_dir: Literal["asc", "desc"] = Query("asc"),
    ) -> dict[str, Any]:
        where_clauses = []
        if q and search_field:
            where_clauses.append(getattr(model, search_field).ilike(f"%{q}%"))

        # Separate count query — keeps the total independent of pagination/relations.
        count_stmt = select(func.count()).select_from(model)
        if where_clauses:
            count_stmt = count_stmt.where(*where_clauses)
        total: int = (await db.execute(count_stmt)).scalar_one()

        data_stmt = select(model)
        for rel in relations:
            data_stmt = data_stmt.options(selectinload(getattr(model, rel.attribute)))
        if where_clauses:
            data_stmt = data_stmt.where(*where_clauses)

        effective_sort = sort_by if sort_by in sortable_columns else pk_attr_name
        sort_col = getattr(model, effective_sort)
        data_stmt = data_stmt.order_by(
            sort_col.asc() if sort_dir == "asc" else sort_col.desc()
        )
        data_stmt = data_stmt.offset(skip).limit(limit)

        records = (await db.execute(data_stmt)).scalars().all()

        items = []
        for record in records:
            item = read_schema.model_validate(record, from_attributes=True).model_dump()
            for rel in relations:
                related_obj = getattr(record, rel.attribute, None)
                item[f"{rel.attribute}_{rel.display_field}"] = (
                    getattr(related_obj, rel.display_field, None)
                    if related_obj is not None
                    else None
                )
            items.append(item)

        return {"items": items, "total": total}

    return list_handler


def _make_retrieve_handler(config: ResourceConfig):
    model = config.model
    read_schema = config.read_schema
    pk_attr = _get_pk_attr(model)

    async def retrieve_handler(record_id: int, db: DB) -> Any:
        record = (
            await db.execute(select(model).where(pk_attr == record_id))
        ).scalar_one_or_none()
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
        return read_schema.model_validate(record, from_attributes=True)

    return retrieve_handler


def _make_create_handler(config: ResourceConfig):
    model = config.model
    read_schema = config.read_schema
    write_schema = config.write_schema

    async def create_handler(db: DB, body=Body(...)) -> Any:
        record = model(**body.model_dump())
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return read_schema.model_validate(record, from_attributes=True)

    # Patch the body annotation post-definition so FastAPI resolves the correct
    # Pydantic schema for request body parsing and OpenAPI documentation.
    create_handler.__annotations__["body"] = write_schema
    return create_handler


def _make_update_handler(config: ResourceConfig):
    model = config.model
    read_schema = config.read_schema
    write_schema = config.write_schema
    pk_attr = _get_pk_attr(model)

    async def update_handler(record_id: int, db: DB, body=Body(...)) -> Any:
        record = (
            await db.execute(select(model).where(pk_attr == record_id))
        ).scalar_one_or_none()
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
        for key, value in body.model_dump().items():
            setattr(record, key, value)
        await db.commit()
        await db.refresh(record)
        return read_schema.model_validate(record, from_attributes=True)

    update_handler.__annotations__["body"] = write_schema
    return update_handler


def _make_delete_handler(config: ResourceConfig):
    model = config.model
    pk_attr = _get_pk_attr(model)

    async def delete_handler(record_id: int, db: DB) -> None:
        record = (
            await db.execute(select(model).where(pk_attr == record_id))
        ).scalar_one_or_none()
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
        await db.delete(record)
        await db.commit()

    return delete_handler


# ── Utilities ─────────────────────────────────────────────────────────────────


def _get_pk_attr(model: type) -> Any:
    """Return the SQLAlchemy instrumented attribute for the model's primary key."""
    mapper = sa_inspect(model)
    pk_prop = next(
        attr for attr in mapper.column_attrs
        if any(col.primary_key for col in attr.columns)
    )
    return getattr(model, pk_prop.key)
