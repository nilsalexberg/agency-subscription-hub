"""
Resource registration contract for the schema-driven admin panel.

Each admin resource is declared once as a ResourceConfig. The router factory
(Step 2) reads this config to generate five standard CRUD routes. The resource
registry (Step 3) iterates a list of configs to mount all generated routers.

Frontend resource configs are designed in parallel against this same contract:
the field names, prefix, and relation display fields are shared vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Optional, Type

from pydantic import BaseModel

# The five operations the router factory generates routes for.
Operation = Literal["list", "retrieve", "create", "update", "delete"]

# Maps an operation to either None (use factory default) or a custom FastAPI
# path function that fully replaces the default for that operation.
# Custom handlers must accept the same dependency-injected arguments as the
# defaults would (AsyncSession via Depends, current user, etc.).
OverrideMap = dict[Operation, Optional[Callable[..., Any]]]


@dataclass(frozen=True)
class RelationLoadConfig:
    """
    Specifies a relationship to eager-load in list responses.

    The factory uses selectinload on `attribute` and serializes `display_field`
    from the related object alongside the raw foreign key. This avoids a
    separate round-trip from the frontend to resolve FK labels.

    Example: RelationLoadConfig(attribute="plan", display_field="name")
    adds a "plan_name" key to each row in the list response.
    """

    attribute: str
    display_field: str


@dataclass
class ResourceConfig:
    """
    Declarative specification for one admin CRUD resource.

    Fields
    ------
    model
        SQLAlchemy model class. The factory uses this for all ORM operations
        and never imports from resource-specific modules directly.
    read_schema
        Pydantic model returned by GET /  and GET /{id}.
    write_schema
        Pydantic model accepted by POST / and PUT /{id}.
    prefix
        URL prefix for all generated routes, e.g. "/plans". Must start with "/".
    search_field
        Optional column name. When present, GET / accepts a ?q= param and
        filters rows with an ilike match on this column.
    relations
        Relationships to eager-load and serialize display fields for in list
        responses. See RelationLoadConfig.
    overrides
        Per-operation replacements. Absent keys and None values both mean
        "use the factory default". A non-None callable fully replaces the
        default handler for that operation.
    """

    model: Type[Any]
    read_schema: Type[BaseModel]
    write_schema: Type[BaseModel]
    prefix: str
    search_field: Optional[str] = None
    relations: list[RelationLoadConfig] = field(default_factory=list)
    overrides: OverrideMap = field(default_factory=dict)
