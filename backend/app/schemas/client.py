from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.client import SubscriptionStatus


class ClientRead(BaseModel):
    id: int
    name: str
    email: str
    document: str
    plan_id: int
    efi_subscription_id: str | None = None
    checkout_url: str | None = None
    status: SubscriptionStatus
    cancelled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClientWrite(BaseModel):
    name: str
    email: EmailStr
    document: str
    plan_id: int
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
