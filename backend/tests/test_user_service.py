import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import Role, User
from app.services.user import get_user_by_email, create_user, any_user_exists
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    user_data = UserCreate(email="test@example.com", password="password123")
    user = await create_user(db_session, user_data)
    
    assert user.email == "test@example.com"
    assert user.role == Role.VIEWER  # Default role
    assert user.is_active is True


@pytest.mark.asyncio
async def test_get_user_by_email(db_session: AsyncSession):
    email = "test@example.com"
    not_found = await get_user_by_email(db_session, email)
    assert not_found is None

    user = User(email=email, hashed_password="hash", role=Role.VIEWER)
    db_session.add(user)
    await db_session.commit()
    
    found = await get_user_by_email(db_session, email)
    assert found is not None
    assert found.email == email


@pytest.mark.asyncio
async def test_any_user_exists(db_session: AsyncSession):
    # Initially no users
    assert await any_user_exists(db_session) is False
    
    # Add a user
    user = User(email="test@example.com", hashed_password="hash", role=Role.VIEWER)
    db_session.add(user)
    await db_session.commit()
    
    assert await any_user_exists(db_session) is True