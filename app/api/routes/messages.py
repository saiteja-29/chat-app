from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.api.rate_limits import message_rate_limit
from app.core.database import get_db
from app.models.user import User
from app.schemas.message import (
    MessageCreate,
    MessageListResponse,
    MessageResponse,
)
from app.services.message_service import create_message, list_messages


router = APIRouter(
    prefix="/conversations/{conversation_id}/messages",
    tags=["Messages"],
)


@router.post(
    "",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(message_rate_limit)],
)
async def send_message(
    conversation_id: UUID,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_message(
        db=db,
        conversation_id=conversation_id,
        sender_id=current_user.id,
        data=data,
    )


@router.get("", response_model=MessageListResponse)
async def get_messages(
    conversation_id: UUID,
    before: datetime | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    messages, next_cursor = await list_messages(
        db=db,
        conversation_id=conversation_id,
        current_user_id=current_user.id,
        before=before,
        limit=limit,
    )

    return MessageListResponse(
        items=messages,
        next_cursor=next_cursor,
    )