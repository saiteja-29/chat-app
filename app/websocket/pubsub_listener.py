from redis.asyncio import Redis
import json
from uuid import UUID

from datetime import datetime
from sqlalchemy import update
from app.core.database import AsyncSessionLocal
from app.models.message import MessageDelivery

from app.core.redis import redis_client
from app.services.pubsub_service import (
    CHAT_MESSAGES_CHANNEL,
    PRESENCE_CHANNEL,
)
from app.websocket.manager import manager


async def start_pubsub_listener():
    pubsub = redis_client.pubsub()

    await pubsub.subscribe(
        CHAT_MESSAGES_CHANNEL,
        PRESENCE_CHANNEL,
    )

    print("Redis Pub/Sub listener started")

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue

        channel = message["channel"]
        data = json.loads(message["data"])

        if channel == CHAT_MESSAGES_CHANNEL:
            user_ids = [UUID(uid) for uid in data["user_ids"]]
            payload = data["payload"]

            await manager.broadcast_to_users(
                user_ids=user_ids,
                message=payload,
            )

            connected_user_ids = [
                user_id for user_id in user_ids
                if manager.is_user_connected(user_id)
            ]

            if connected_user_ids and payload["type"] == "message.new":
                async with AsyncSessionLocal() as db:
                    message_id = UUID(payload["message"]["id"])

                    await db.execute(
                        update(MessageDelivery)
                        .where(MessageDelivery.message_id == message_id)
                        .where(MessageDelivery.user_id.in_(connected_user_ids))
                        .where(MessageDelivery.delivered_at.is_(None))
                        .values(delivered_at=datetime.utcnow())
                    )

                    await db.commit()

        elif channel == PRESENCE_CHANNEL:
            payload = {
                "type": "presence.update",
                "user_id": data["user_id"],
                "status": data["status"],
            }

            await manager.broadcast_all(payload)