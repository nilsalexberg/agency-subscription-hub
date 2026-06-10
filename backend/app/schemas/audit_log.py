from datetime import datetime

from pydantic import BaseModel

from app.models.audit_log import AuditAction


class AuditLogRead(BaseModel):
    id: int
    user_id: int | None = None
    action: AuditAction
    entity_type: str
    entity_id: int
    description: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# Placeholder only — all write operations are overridden to 405 in the registry.
class AuditLogWrite(BaseModel):
    pass
