from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.plan import BillingCycle


class PlanRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: Decimal
    billing_cycle: BillingCycle
    efi_plan_id: str | None = None
    split_config_id: int | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlanWrite(BaseModel):
    name: str
    description: str | None = None
    price: Decimal
    billing_cycle: BillingCycle
    efi_plan_id: str | None = None
    split_config_id: int | None = None
    is_active: bool = True
