from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.schemas.client import ClientWrite


async def create_client_with_checkout_token(db: AsyncSession, body: ClientWrite) -> Client:
    token = str(uuid4())
    record = Client(**body.model_dump(), checkout_token=token, checkout_url=f"/checkout/{token}")
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record
