from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.database import get_db
from app.core.redis import get_redis


router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check():
    return {
        "status": "ok",
        "service": "chat-backend",
    }


@router.get("/db")
async def database_health_check(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "database": result.scalar(),
    }


@router.get("/redis")
async def redis_health_check(redis: Redis = Depends(get_redis)):
    pong = await redis.ping()
    return {
        "status": "ok",
        "redis": pong,
    }