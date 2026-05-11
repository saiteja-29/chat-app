import json

from redis.asyncio import Redis
class RateLimitExceeded(Exception):
    pass

async def check_rate_limit(
    redis: Redis,
    key: str,
    limit: int,
    window_seconds: int,
) -> None:
    current_count = await redis.incr(key)

    if current_count == 1:
        await redis.expire(key, window_seconds)

    if current_count > limit:
        raise RateLimitExceeded()
    
CHAT_MESSAGES_CHANNEL = "chat_messages"
PRESENCE_CHANNEL = "presence_updates"


async def publish_message(
    redis: Redis,
    message: dict,
):
    await redis.publish(CHAT_MESSAGES_CHANNEL, json.dumps(message))


async def publish_presence_update(
    redis: Redis,
    user_id: str,
    status: str,
):
    await redis.publish(
        PRESENCE_CHANNEL,
        json.dumps({
            "user_id": user_id,
            "status": status,
        }),
    )