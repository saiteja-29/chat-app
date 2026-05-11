from fastapi import Depends, HTTPException, status
from redis.asyncio import Redis

from app.core.redis import get_redis
from app.models.user import User
from app.api.dependencies import get_current_user
from app.services.rate_limit_service import (
    RateLimitExceeded,
    check_rate_limit,
)


async def message_rate_limit(
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> None:
    minute_key = f"rate_limit:messages:minute:{current_user.id}"
    burst_key = f"rate_limit:messages:burst:{current_user.id}"

    try:
        await check_rate_limit(
            redis=redis,
            key=burst_key,
            limit=5,
            window_seconds=5,
        )

        await check_rate_limit(
            redis=redis,
            key=minute_key,
            limit=30,
            window_seconds=60,
        )

    except RateLimitExceeded:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many messages. Please slow down.",
        )