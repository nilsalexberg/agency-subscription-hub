from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.payment import PaymentStatus


class PaymentRead(BaseModel):
    id: int
    client_id: int
    plan_id: int
    amount: Decimal
    status: PaymentStatus
    transaction_id: str | None = None
    paid_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# Placeholder only — all write operations are overridden to 405 in the registry.
class PaymentWrite(BaseModel):
    pass
