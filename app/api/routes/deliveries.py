from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.message import MessageDelivery


router = APIRouter(tags=["Delivery"])

@router.post("/messages/{message_id}/read")
async def mark_message_read(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await db.execute(
        update(MessageDelivery)
        .where(MessageDelivery.message_id == message_id)
        .where(MessageDelivery.user_id == current_user.id)
        .values(read_at=datetime.utcnow())
    )

    await db.commit()

    return {"status": "read"}