from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """
    Kullanıcı işlemlerini ve yetki/hiyerarşi odaklı veritabanı sorgularını
    yöneten repository sınıfı.
    """

    def __init__(self, db: AsyncSession):
        super().__init__(model=User, db=db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        E-posta adresine göre kullanıcı kaydını ilişkili birim ve yönetici bilgileriyle getirir.
        """
        query = (
            select(User)
            .where(func.lower(User.email) == func.lower(email))
            .options(
                selectinload(User.unit),
                selectinload(User.manager)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_with_relations(self, user_id: int) -> Optional[User]:
        """
        ID değerine göre kullanıcıyı ilişkili birimler ve yönetici bilgisiyle birlikte getirir.
        """
        query = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.unit),
                selectinload(User.manager)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_users_filtered(
        self,
        search_text: Optional[str] = None,
        department_id: Optional[int] = None,
        directorate_id: Optional[int] = None,
        manager_id: Optional[int] = None,
        unit_id: Optional[int] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        allowed_user_ids: Optional[List[int]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[User], int]:
        """
        Arama metni (Ad/E-posta/Ünvan ILIKE), birim ve aktiflik kriterlerine göre 
        kullanıcıları sayfalı olarak filtreler ve [liste, toplam_sayı] ikilisini döndürür.
        """
        query = select(User).options(
            selectinload(User.unit),
            selectinload(User.manager)
        )
        count_query = select(func.count()).select_from(User)

        conditions = []

        if search_text:
            search_pattern = f"%{search_text}%"
            conditions.append(
                or_(
                    User.full_name.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.title.ilike(search_pattern)
                )
            )

        if department_id is not None:
            # department_id is deprecated, map to unit_id for backwards compatibility
            conditions.append(User.unit_id == department_id)

        if directorate_id is not None:
            # directorate_id is deprecated, map to unit_id for backwards compatibility
            conditions.append(User.unit_id == directorate_id)

        if manager_id is not None:
            conditions.append(User.manager_id == manager_id)

        if unit_id is not None:
            conditions.append(User.unit_id == unit_id)

        if role is not None:
            conditions.append(User.role == role)

        if is_active is not None:
            conditions.append(User.is_active == is_active)

        if allowed_user_ids is not None:
            conditions.append(User.id.in_(allowed_user_ids))

        if conditions:
            query = query.where(*conditions)
            count_query = count_query.where(*conditions)

        # Toplam kayıt sayısı
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Sayfalanmış liste
        query = query.offset(skip).limit(limit).order_by(User.id.desc())
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total