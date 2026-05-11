from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, ConversationMember
from app.models.user import User
from app.schemas.conversation import ConversationCreate

from sqlalchemy import func
from app.models.message import Message, MessageDelivery


async def validate_users_exist(
    db: AsyncSession,
    user_ids: list[UUID],
) -> None:
    result = await db.execute(
        select(User.id).where(User.id.in_(user_ids))
    )
    existing_user_ids = set(result.scalars().all())

    missing_ids = set(user_ids) - existing_user_ids

    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Users not found: {list(missing_ids)}",
        )


async def find_existing_direct_conversation(
    db: AsyncSession,
    user_a: UUID,
    user_b: UUID,
) -> Conversation | None:
    result = await db.execute(
        select(Conversation)
        .join(ConversationMember)
        .where(Conversation.type == "direct")
        .where(ConversationMember.user_id.in_([user_a, user_b]))
    )

    possible_conversations = result.scalars().unique().all()

    for conversation in possible_conversations:
        member_result = await db.execute(
            select(ConversationMember.user_id).where(
                ConversationMember.conversation_id == conversation.id
            )
        )
        members = set(member_result.scalars().all())

        if members == {user_a, user_b}:
            return conversation

    return None


async def create_conversation(
    db: AsyncSession,
    current_user_id: UUID,
    data: ConversationCreate,
) -> Conversation:
    member_ids = set(data.member_ids)
    member_ids.add(current_user_id)

    if data.type == "direct":
        if len(member_ids) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Direct conversation must have exactly 2 users",
            )

        other_user_id = next(uid for uid in member_ids if uid != current_user_id)

        existing = await find_existing_direct_conversation(
            db=db,
            user_a=current_user_id,
            user_b=other_user_id,
        )

        if existing:
            return existing

    if data.type == "group" and len(member_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group conversation must have at least 2 users",
        )

    await validate_users_exist(db, list(member_ids))

    conversation = Conversation(
        type=data.type,
        name=data.name if data.type == "group" else None,
        created_by=current_user_id,
    )

    db.add(conversation)
    await db.flush()

    for user_id in member_ids:
        member = ConversationMember(
            conversation_id=conversation.id,
            user_id=user_id,
            role="admin" if user_id == current_user_id else "member",
        )
        db.add(member)

    await db.commit()
    await db.refresh(conversation)

    return conversation


async def list_user_conversations(
    db: AsyncSession,
    current_user_id: UUID,
) -> list[Conversation]:
    result = await db.execute(
        select(Conversation)
        .join(ConversationMember)
        .where(ConversationMember.user_id == current_user_id)
        .order_by(Conversation.updated_at.desc())
    )

    return list(result.scalars().unique().all())


async def get_conversation_for_user(
    db: AsyncSession,
    conversation_id: UUID,
    current_user_id: UUID,
) -> Conversation:
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.members))
        .join(ConversationMember)
        .where(
            and_(
                Conversation.id == conversation_id,
                ConversationMember.user_id == current_user_id,
            )
        )
    )

    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return conversation

async def list_user_conversations_with_unread(
    db: AsyncSession,
    current_user_id: UUID,
) -> list[dict]:
    result = await db.execute(
        select(
            Conversation,
            func.count(MessageDelivery.id).label("unread_count"),
        )
        .join(
            ConversationMember,
            ConversationMember.conversation_id == Conversation.id,
        )
        .outerjoin(
            Message,
            Message.conversation_id == Conversation.id,
        )
        .outerjoin(
            MessageDelivery,
            (MessageDelivery.message_id == Message.id)
            & (MessageDelivery.user_id == current_user_id)
            & (MessageDelivery.read_at.is_(None)),
        )
        .options(
            selectinload(Conversation.members)
        )
        .where(ConversationMember.user_id == current_user_id)
        .group_by(Conversation.id)
        .order_by(Conversation.updated_at.desc())
    )

    conversations = []

    for conversation, unread_count in result.all():
        member_ids = [member.user_id for member in conversation.members]

        users_result = await db.execute(
            select(User).where(User.id.in_(member_ids))
        )

        users = list(users_result.scalars().all())

        conversations.append({
            "id": conversation.id,
            "type": conversation.type,
            "name": conversation.name,
            "created_by": conversation.created_by,
            "created_at": conversation.created_at,
            "unread_count": unread_count,
            "members": users,
        })

    return conversations