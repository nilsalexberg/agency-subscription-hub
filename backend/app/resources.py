"""
Central admin resource registry.

Single source of truth for all admin-managed CRUD resources. Each resource is
declared once as a ResourceConfig; build_router generates the five standard routes.
register_admin_resources() mounts all generated routers on the FastAPI app under
the /admin prefix.

Custom endpoints outside the factory (e.g. checkout-link generation for clients)
are imported and mounted separately in main.py alongside the generated router.
"""

from fastapi import FastAPI

from app.admin.contracts import RelationLoadConfig, ResourceConfig
from app.admin.factory import build_router
from app.admin.handlers import (
    READ_ONLY_OVERRIDES,
    create_client_with_checkout_token_handler,
    method_not_allowed_handler,
)
from app.models.audit_log import AuditLog
from app.models.client import Client
from app.models.payment import Payment
from app.models.plan import Plan
from app.models.recipient import Recipient
from app.models.split_config import SplitConfig
from app.models.user import User
from app.schemas.audit_log import AuditLogRead, AuditLogWrite
from app.schemas.client import ClientRead, ClientWrite
from app.schemas.payment import PaymentRead, PaymentWrite
from app.schemas.plan import PlanRead, PlanWrite
from app.schemas.recipient import RecipientRead, RecipientWrite
from app.schemas.split_config import SplitConfigRead, SplitConfigWrite
from app.schemas.user import UserAdminWrite, UserRead


RESOURCE_CONFIGS: list[ResourceConfig] = [
    ResourceConfig(
        model=Recipient,
        read_schema=RecipientRead,
        write_schema=RecipientWrite,
        prefix="/recipients",
        search_field="name",
    ),
    ResourceConfig(
        model=SplitConfig,
        read_schema=SplitConfigRead,
        write_schema=SplitConfigWrite,
        prefix="/split-configs",
        search_field="name",
    ),
    ResourceConfig(
        model=Plan,
        read_schema=PlanRead,
        write_schema=PlanWrite,
        prefix="/plans",
        search_field="name",
        relations=[RelationLoadConfig(attribute="split_config", display_field="name")],
    ),
    ResourceConfig(
        model=Client,
        read_schema=ClientRead,
        write_schema=ClientWrite,
        prefix="/clients",
        search_field="name",
        relations=[RelationLoadConfig(attribute="plan", display_field="name")],
        overrides={"create": create_client_with_checkout_token_handler},
    ),
    ResourceConfig(
        model=Payment,
        read_schema=PaymentRead,
        write_schema=PaymentWrite,
        prefix="/payments",
        overrides=READ_ONLY_OVERRIDES,
    ),
    ResourceConfig(
        model=AuditLog,
        read_schema=AuditLogRead,
        write_schema=AuditLogWrite,
        prefix="/audit-logs",
        search_field="entity_type",
        overrides=READ_ONLY_OVERRIDES,
    ),
    ResourceConfig(
        model=User,
        read_schema=UserRead,
        write_schema=UserAdminWrite,
        prefix="/users",
        search_field="email",
        # User creation with a password is handled by the auth module, not the factory.
        overrides={"create": method_not_allowed_handler},
    ),
]


def register_admin_resources(app: FastAPI) -> None:
    """Mount all admin CRUD routers on the app under the /api/admin prefix."""
    for config in RESOURCE_CONFIGS:
        app.include_router(build_router(config), prefix="/api/admin")
