from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.security import create_access_token, verify_password
from app.models.user import Role
from app.schemas.token import Token
from app.schemas.user import LoginRequest, UserCreate, UserRead
from app.services.user import any_user_exists, create_user, get_user_by_email

router = APIRouter(prefix="/auth", tags=["auth"])

DB = Annotated[AsyncSession, Depends(get_db)]


@router.post("/login", response_model=Token)
async def login(body: LoginRequest, db: DB) -> Token:
    user = await get_user_by_email(db, body.email)
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return Token(access_token=create_access_token(str(user.id)))


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate, db: DB) -> UserRead:
    """Bootstrap first admin. Locked after first user exists."""
    if await any_user_exists(db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration closed. Use admin panel to create users.",
        )

    body.role = Role.ADMIN
    return UserRead.model_validate(await create_user(db, body))
