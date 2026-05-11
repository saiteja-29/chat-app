from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    message_type: str = "text"
    client_message_id: UUID | None = None


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_id: UUID
    content: str
    message_type: str
    created_at: datetime
    edited_at: datetime | None
    deleted_at: datetime | None

    model_config = {
        "from_attributes": True,
    }


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    next_cursor: datetime | None