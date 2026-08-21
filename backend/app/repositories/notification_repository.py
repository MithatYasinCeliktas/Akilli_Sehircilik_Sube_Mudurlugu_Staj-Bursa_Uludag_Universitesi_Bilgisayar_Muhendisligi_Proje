from typing import List
from sqlalchemy import select, update
from app.repositories.base import BaseRepository
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate

class NotificationRepository(BaseRepository[Notification, NotificationCreate, NotificationCreate]):
    def __init__(self, db):
        super().__init__(Notification, db)

    async def get_by_user_id(self, user_id: int) -> List[Notification]:
        query = select(Notification).where(
            Notification.user_id == user_id
        ).order_by(Notification.created_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_unread_count(self, user_id: int) -> int:
        from sqlalchemy import func
        query = select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def mark_all_as_read(self, user_id: int):
        stmt = update(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).values(is_read=True)
        await self.db.execute(stmt)
        await self.db.commit()
