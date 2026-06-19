from fastapi import APIRouter, HTTPException, status

from app.core.deps import DB
from app.schemas.checkout import CheckoutRead
from app.services.checkout import get_client_by_checkout_token

router = APIRouter(prefix="/checkout", tags=["checkout"])


@router.get("/{token}", response_model=CheckoutRead)
async def get_checkout(token: str, db: DB) -> CheckoutRead:
    client = await get_client_by_checkout_token(db, token)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checkout not found",
        )
    return CheckoutRead(
        client_name=client.name,
        client_email=client.email,
        client_document=client.document,
        plan_name=client.plan.name,
        plan_description=client.plan.description,
        plan_price=client.plan.price,
        plan_billing_cycle=client.plan.billing_cycle,
    )

