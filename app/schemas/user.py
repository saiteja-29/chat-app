from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    display_name: str | None = None


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    display_name: str | None
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }