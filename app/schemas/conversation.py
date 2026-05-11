from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    type: str = Field(pattern="^(direct|group)$")
    name: str | None = None
    member_ids: list[UUID]


class ConversationMemberResponse(BaseModel):
    user_id: UUID
    role: str
    joined_at: datetime

    model_config = {
        "from_attributes": True,
    }


class ConversationResponse(BaseModel):
    id: UUID
    type: str
    name: str | None
    created_by: UUID
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class ConversationDetailResponse(ConversationResponse):
    members: list[ConversationMemberResponse]

class ConversationWithUnreadResponse(ConversationResponse):
    unread_count: int

class ConversationMemberUserResponse(BaseModel):
    id: UUID
    username: str
    display_name: str | None

    model_config = {
        "from_attributes": True,
    }


class ConversationListItemResponse(ConversationResponse):
    unread_count: int
    members: list[ConversationMemberUserResponse]