from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetailResponse,
    ConversationResponse,
    ConversationListItemResponse,
    
)
from app.services.conversation_service import (
    create_conversation,
    get_conversation_for_user,
    list_user_conversations,
    list_user_conversations_with_unread,
)


router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_new_conversation(
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_conversation(
        db=db,
        current_user_id=current_user.id,
        data=data,
    )


@router.get("", response_model=list[ConversationResponse])
async def get_my_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await list_user_conversations(
        db=db,
        current_user_id=current_user.id,
    )

@router.get("/with-unread", response_model=list[ConversationListItemResponse])
async def get_my_conversations_with_unread(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await list_user_conversations_with_unread(
        db=db,
        current_user_id=current_user.id,
    )

@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_conversation_for_user(
        db=db,
        conversation_id=conversation_id,
        current_user_id=current_user.id,
    )

