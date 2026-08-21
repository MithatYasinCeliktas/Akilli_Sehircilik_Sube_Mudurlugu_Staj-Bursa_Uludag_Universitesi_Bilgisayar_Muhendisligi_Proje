from typing import Any, Dict, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.models.system_log import SystemLog
from app.models.user import User
from app.schemas.system_log import SystemLogCreate, SystemLogResponse

class LogService:
    @staticmethod
    async def create_log(
        db: AsyncSession,
        action: str,
        user_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> SystemLog:
        """
        Sistem logu oluşturur ve veritabanına kaydeder.
        """
        log_obj = SystemLog(
            action=action,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address
        )
        db.add(log_obj)
        # Commit işlemi genelde çağıran servis tarafından yapılır,
        # Ancak sadece log atan bağımsız yerlerde manuel commit gerekebilir.
        # Biz session'a ekleyip flush yapalım, ana işlem commit edilince bu da gider.
        await db.flush()
        return log_obj

    @staticmethod
    async def get_logs(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        search: Optional[str] = None
    ):
        """
        Filtrelenmiş ve sayfalanmış logları getirir.
        """
        query = select(SystemLog).options(selectinload(SystemLog.user))
        
        if action:
            query = query.filter(SystemLog.action == action)
        if user_id:
            query = query.filter(SystemLog.user_id == user_id)
        if entity_type:
            query = query.filter(SystemLog.entity_type == entity_type)
            
        if search:
            # Search over action, entity_type or user info
            # Just simple ILIKE for demonstration
            query = query.join(User, SystemLog.user_id == User.id, isouter=True)
            search_term = f"%{search}%"
            query = query.filter(
                SystemLog.action.ilike(search_term) |
                SystemLog.entity_type.ilike(search_term) |
                User.full_name.ilike(search_term) |
                User.email.ilike(search_term)
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)

        # Get data
        query = query.order_by(desc(SystemLog.created_at)).offset(skip).limit(limit)
        result = await db.execute(query)
        logs = result.scalars().all()
        
        # Transform for response
        items = []
        for log in logs:
            items.append(SystemLogResponse(
                id=log.id,
                action=log.action,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                details=log.details,
                ip_address=log.ip_address,
                user_id=log.user_id,
                created_at=log.created_at,
                user_email=log.user.email if log.user else None,
                user_name=log.user.full_name if log.user else None
            ))

        return {
            "items": items,
            "total": total,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "size": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }

    @staticmethod
    async def get_logs_paginated(
        db: AsyncSession,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ):
        query = select(SystemLog).options(selectinload(SystemLog.user))
        
        if user_id:
            query = query.filter(SystemLog.user_id == user_id)
        if action:
            query = query.filter(SystemLog.action == action)
        if entity_type:
            query = query.filter(SystemLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(SystemLog.entity_id == entity_id)
            
        if start_date:
            from datetime import datetime
            query = query.filter(SystemLog.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        if end_date:
            from datetime import datetime, timedelta
            query = query.filter(SystemLog.created_at < datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)

        # Get data
        query = query.order_by(desc(SystemLog.created_at)).offset(skip).limit(limit)
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return logs, total
