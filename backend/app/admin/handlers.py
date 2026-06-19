from fastapi import HTTPException, status

from app.core.deps import DB
from app.schemas.client import ClientRead, ClientWrite
from app.services.client import create_client_with_checkout_token


async def create_client_with_checkout_token_handler(db: DB, body: ClientWrite) -> ClientRead:
    record = await create_client_with_checkout_token(db, body)
    return ClientRead.model_validate(record, from_attributes=True)


async def method_not_allowed_handler() -> None:
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Method not allowed",
    )


# Shared override map for read-only resources — write operations return 405.
READ_ONLY_OVERRIDES = {
    "create": method_not_allowed_handler,
    "update": method_not_allowed_handler,
    "delete": method_not_allowed_handler,
}
