from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.models.user import User


async def get_user_from_token(
    token: str,
    db: AsyncSession,
) -> User | None:
    user_id = decode_access_token(token)

    if not user_id:
        return None

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        return None

    result = await db.execute(
        select(User).where(User.id == user_uuid)
    )

    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        return None

    return user