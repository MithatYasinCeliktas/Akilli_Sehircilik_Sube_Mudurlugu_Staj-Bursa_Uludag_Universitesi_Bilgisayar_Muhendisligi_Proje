from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.models.user import User
from app.schemas.notification import NotificationResponse
from app.services.notification_service import NotificationService

router = APIRouter()

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    service = NotificationService(db)
    return await service.get_user_notifications(current_user.id)

@router.get("/unread-count", response_model=int)
async def get_unread_count(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    service = NotificationService(db)
    return await service.get_unread_count(current_user.id)

@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    service = NotificationService(db)
    return await service.mark_as_read(notification_id, current_user.id)

@router.post("/read-all")
async def mark_all_as_read(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    service = NotificationService(db)
    await service.mark_all_as_read(current_user.id)
    return {"success": True}
