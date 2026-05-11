from datetime import datetime

from app.models.message import MessageDelivery
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from redis.asyncio import Redis
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, get_db
from app.core.redis import get_redis

from app.schemas.message import MessageCreate

from app.services.presence_service import (
    mark_user_offline,
    mark_user_online,
    refresh_user_presence,
)
from app.services.pubsub_service import (
    publish_message,
    publish_presence_update,
)
from app.websocket.auth import get_user_from_token
from app.websocket.manager import manager
from app.services.message_service import (
    create_message,
    ensure_conversation_member,
    get_conversation_member_ids,
    get_conversation_member_ids_except_user,
    get_undelivered_messages_for_user,
    mark_messages_delivered,
)


router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008)
        return

    user = await get_user_from_token(token=token, db=db)

    if not user:
        await websocket.close(code=1008)
        return

    await manager.connect(user.id, websocket)

    await mark_user_online(redis, user.id)

    await publish_presence_update(
        redis=redis,
        user_id=str(user.id),
        status="online",
    )
    missed_messages = await get_undelivered_messages_for_user(
        db=db,
        user_id=user.id,
    )

    if missed_messages:
        await websocket.send_json({
            "type": "messages.sync",
            "messages": [
                {
                    "id": str(message.id),
                    "conversation_id": str(message.conversation_id),
                    "sender_id": str(message.sender_id),
                    "content": message.content,
                    "message_type": message.message_type,
                    "created_at": message.created_at.isoformat(),
                }
                for message in missed_messages
            ],
        })

        await mark_messages_delivered(
            db=db,
            user_id=user.id,
            message_ids=[message.id for message in missed_messages],
        )

    try:
        while True:
            payload = await websocket.receive_json()

            event_type = payload.get("type")

            if event_type == "heartbeat":
                await refresh_user_presence(redis, user.id)

                await websocket.send_json({
                    "type": "heartbeat.ack",
                })

            elif event_type == "message.send":
                conversation_id = UUID(payload["conversation_id"])

                message_data = MessageCreate(
                    content=payload["content"],
                    message_type=payload.get("message_type", "text"),
                    client_message_id=payload.get("client_message_id"),
                )

                message = await create_message(
                    db=db,
                    conversation_id=conversation_id,
                    sender_id=user.id,
                    data=message_data,
                )

                member_ids = await get_conversation_member_ids(
                    db=db,
                    conversation_id=conversation_id,
                )

                outgoing_event = {
                    "type": "message.new",
                    "message": {
                        "id": str(message.id),
                        "conversation_id": str(message.conversation_id),
                        "sender_id": str(message.sender_id),
                        "content": message.content,
                        "message_type": message.message_type,
                        "created_at": message.created_at.isoformat(),
                    },
                }

                # ✅ 1. SEND IMMEDIATELY BACK TO SENDER
                await websocket.send_json(outgoing_event)

                # ✅ 2. SEND TO OTHER USERS VIA REDIS
                other_user_ids = [uid for uid in member_ids if uid != user.id]

                if other_user_ids:
                    await publish_message(
                        redis=redis,
                        message={
                            "user_ids": [str(uid) for uid in other_user_ids],
                            "payload": outgoing_event,
                        },
                    )
            elif event_type == "message.read":
                message_id = UUID(payload["message_id"])

                async with AsyncSessionLocal() as db:
                    await db.execute(
                        update(MessageDelivery)
                        .where(MessageDelivery.message_id == message_id)
                        .where(MessageDelivery.user_id == user.id)
                        .values(read_at=datetime.utcnow())
                    )

                    await db.commit()

                # notify others
                await publish_message(
                    redis=redis,
                    message={
                        "user_ids": [str(user.id)],
                        "payload": {
                            "type": "message.read",
                            "message_id": str(message_id),
                            "user_id": str(user.id),
                        },
                    },
                )
            elif event_type in ["typing.start", "typing.stop"]:
                print("🔥 Typing event received:", payload)
                conversation_id = UUID(payload["conversation_id"])

                await ensure_conversation_member(
                    db=db,
                    conversation_id=conversation_id,
                    user_id=user.id,
                )

                recipient_ids = await get_conversation_member_ids_except_user(
                    db=db,
                    conversation_id=conversation_id,
                    excluded_user_id=user.id,
                )

                await publish_message(
                    redis=redis,
                    message={
                        "user_ids": [str(uid) for uid in recipient_ids],
                        "payload": {
                            "type": event_type,
                            "conversation_id": str(conversation_id),
                            "user_id": str(user.id),
                            "username": user.username,
                        },
                    },
                )

            else:
                await websocket.send_json({
                    "type": "error",
                    "detail": "Unsupported event type",
                })

    except WebSocketDisconnect:
        manager.disconnect(user.id, websocket)

        await mark_user_offline(redis, user.id)

        await publish_presence_update(
            redis=redis,
            user_id=str(user.id),
            status="offline",
        )