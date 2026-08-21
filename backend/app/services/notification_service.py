from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException
from app.models.notification import Notification
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import NotificationCreate, NotificationResponse

class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = NotificationRepository(db)

    async def get_user_notifications(self, user_id: int) -> List[NotificationResponse]:
        notifications = await self.repo.get_by_user_id(user_id)
        return [NotificationResponse.model_validate(n) for n in notifications]

    async def get_unread_count(self, user_id: int) -> int:
        return await self.repo.get_unread_count(user_id)

    async def create_notification(self, data: NotificationCreate) -> NotificationResponse:
        notification = Notification(
            user_id=data.user_id,
            message=data.message,
            type=data.type,
            reference_id=data.reference_id
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return NotificationResponse.model_validate(notification)

    async def mark_as_read(self, notification_id: int, user_id: int) -> NotificationResponse:
        notification = await self.repo.get(notification_id)
        if not notification or notification.user_id != user_id:
            raise NotFoundException("Bildirim bulunamadı.")
        
        if not notification.is_read:
            notification.is_read = True
            await self.db.commit()
            await self.db.refresh(notification)
            
        return NotificationResponse.model_validate(notification)

    async def mark_all_as_read(self, user_id: int):
        await self.repo.mark_all_as_read(user_id)
