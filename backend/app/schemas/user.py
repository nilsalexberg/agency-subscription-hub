from pydantic import BaseModel, EmailStr

from app.models.user import Role


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Role = Role.VIEWER


class UserRead(BaseModel):
    id: int
    email: str
    role: Role
    is_active: bool

    model_config = {"from_attributes": True}


class UserAdminWrite(BaseModel):
    """Write schema for admin panel user management. Password changes are handled separately."""

    email: EmailStr
    role: Role
    is_active: bool
