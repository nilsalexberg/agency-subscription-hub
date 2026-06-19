from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.client import Client


async def get_client_by_checkout_token(db: AsyncSession, token: str) -> Client | None:
    result = await db.execute(
        select(Client)
        .options(selectinload(Client.plan))
        .where(Client.checkout_token == token)
    )
    return result.scalar_one_or_none()
