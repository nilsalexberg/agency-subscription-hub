from decimal import Decimal

from pydantic import BaseModel

from app.models.plan import BillingCycle


class CheckoutRead(BaseModel):
    client_name: str
    client_email: str
    client_document: str
    plan_name: str
    plan_description: str | None
    plan_price: Decimal
    plan_billing_cycle: BillingCycle
