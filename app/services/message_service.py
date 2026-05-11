from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.conversation import Conversation, ConversationMember
from app.models.message import Message, MessageDelivery
from app.schemas.message import MessageCreate

from sqlalchemy import update
from sqlalchemy.orm import selectinload



async def ensure_conversation_member(
    db: AsyncSession,
    conversation_id: UUID,
    user_id: UUID,
) -> None:
    result = await db.execute(
        select(ConversationMember).where(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.user_id == user_id,
        )
    )

    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this conversation",
        )
    
async def create_message(
    db: AsyncSession,
    conversation_id: UUID,
    sender_id: UUID,
    data: MessageCreate,
) -> Message:
    await ensure_conversation_member(
        db=db,
        conversation_id=conversation_id,
        user_id=sender_id,
    )

    message = Message(
        conversation_id=conversation_id,
        sender_id=sender_id,
        content=data.content,
        message_type=data.message_type,
        client_message_id=data.client_message_id,
    )

    db.add(message)

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()

        if data.client_message_id is not None:
            result = await db.execute(
                select(Message).where(
                    Message.sender_id == sender_id,
                    Message.client_message_id == data.client_message_id,
                )
            )
            existing_message = result.scalar_one_or_none()

            if existing_message:
                return existing_message

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate message request",
        )

    members_result = await db.execute(
        select(ConversationMember.user_id).where(
            ConversationMember.conversation_id == conversation_id
        )
    )

    member_ids = members_result.scalars().all()

    for member_id in member_ids:
        if member_id == sender_id:
            continue

        delivery = MessageDelivery(
            message_id=message.id,
            user_id=member_id,
        )
        db.add(delivery)

    conversation = await db.get(Conversation, conversation_id)

    if conversation:
        conversation.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(message)

    return message

async def list_messages(
    db: AsyncSession,
    conversation_id: UUID,
    current_user_id: UUID,
    before: datetime | None = None,
    limit: int = 20,
) -> tuple[list[Message], datetime | None]:
    await ensure_conversation_member(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user_id,
    )

    query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .where(Message.deleted_at.is_(None))
        .order_by(Message.created_at.desc())
        .limit(limit + 1)
    )

    if before:
        query = query.where(Message.created_at < before)

    result = await db.execute(query)
    messages = list(result.scalars().all())

    next_cursor = None

    if len(messages) > limit:
        extra_message = messages.pop()
        next_cursor = extra_message.created_at

    messages.reverse()

    return messages, next_cursor

async def get_conversation_member_ids(
    db: AsyncSession,
    conversation_id: UUID,
) -> list[UUID]:
    result = await db.execute(
        select(ConversationMember.user_id).where(
            ConversationMember.conversation_id == conversation_id
        )
    )

    return list(result.scalars().all())

async def get_conversation_member_ids_except_user(
    db: AsyncSession,
    conversation_id: UUID,
    excluded_user_id: UUID,
) -> list[UUID]:
    result = await db.execute(
        select(ConversationMember.user_id).where(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.user_id != excluded_user_id,
        )
    )

    return list(result.scalars().all())

async def get_undelivered_messages_for_user(
    db: AsyncSession,
    user_id: UUID,
) -> list[Message]:
    result = await db.execute(
        select(MessageDelivery)
        .options(selectinload(MessageDelivery.message))
        .where(MessageDelivery.user_id == user_id)
        .where(MessageDelivery.delivered_at.is_(None))
        .order_by(MessageDelivery.id.asc())
    )

    deliveries = result.scalars().all()

    return [delivery.message for delivery in deliveries]

async def mark_messages_delivered(
    db: AsyncSession,
    user_id: UUID,
    message_ids: list[UUID],
) -> None:
    if not message_ids:
        return

    await db.execute(
        update(MessageDelivery)
        .where(MessageDelivery.user_id == user_id)
        .where(MessageDelivery.message_id.in_(message_ids))
        .where(MessageDelivery.delivered_at.is_(None))
        .values(delivered_at=datetime.utcnow())
    )

    await db.commit()