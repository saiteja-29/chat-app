from uuid import UUID

from redis.asyncio import Redis


PRESENCE_TTL_SECONDS = 60


def presence_key(user_id: UUID) -> str:
    return f"presence:{user_id}"


async def mark_user_online(redis: Redis, user_id: UUID) -> None:
    await redis.set(
        presence_key(user_id),
        "online",
        ex=PRESENCE_TTL_SECONDS,
    )


async def refresh_user_presence(redis: Redis, user_id: UUID) -> None:
    await redis.expire(
        presence_key(user_id),
        PRESENCE_TTL_SECONDS,
    )


async def mark_user_offline(redis: Redis, user_id: UUID) -> None:
    await redis.delete(presence_key(user_id))


async def is_user_online(redis: Redis, user_id: UUID) -> bool:
    exists = await redis.exists(presence_key(user_id))
    return exists == 1