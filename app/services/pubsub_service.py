import json

from redis.asyncio import Redis


CHAT_MESSAGES_CHANNEL = "chat_messages"
PRESENCE_CHANNEL = "presence_updates"


async def publish_message(
    redis: Redis,
    message: dict,
) -> None:
    await redis.publish(
        CHAT_MESSAGES_CHANNEL,
        json.dumps(message),
    )


async def publish_presence_update(
    redis: Redis,
    user_id: str,
    status: str,
) -> None:
    await redis.publish(
        PRESENCE_CHANNEL,
        json.dumps({
            "user_id": user_id,
            "status": status,
        }),
    )