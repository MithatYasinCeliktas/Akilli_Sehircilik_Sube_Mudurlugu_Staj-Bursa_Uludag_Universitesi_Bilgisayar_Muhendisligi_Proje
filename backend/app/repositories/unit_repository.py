from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.unit import Unit
from app.schemas.unit import UnitCreate, UnitUpdate
from app.repositories.base import BaseRepository


class UnitRepository(BaseRepository[Unit, UnitCreate, UnitUpdate]):
    """
    Birim hiyerarşisi ve ağaç yapısı (Daire Başkanlığı, Şube Müdürlüğü vb.) 
    veritabanı sorgularını yöneten repository sınıfı.
    """

    def __init__(self, db: AsyncSession):
        super().__init__(model=Unit, db=db)

    async def get_by_code(self, code: str) -> Optional[Unit]:
        """
        Birim koduna göre tek bir birim getirir.
        """
        query = select(Unit).where(Unit.code == code)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_root_units(self) -> List[Unit]:
        """
        Kök seviyedeki (parent_id is NULL olan) tüm üst birimleri (Daire Başkanlıkları vb.) 
        alt hiyerarşik birimleriyle birlikte getirir.
        """
        query = (
            select(Unit)
            .where(Unit.parent_id.is_(None))
            .options(selectinload(Unit.children))
            .order_by(Unit.name.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_unit_tree(self) -> List[dict]:
        """
        Tüm birim hiyerarşisini alt birim ilişkileriyle (children) ve birim kullanıcılarıyla (unit_users) birlikte ağaç yapısında döndürür.
        """
        query = (
            select(Unit)
            .options(selectinload(Unit.unit_users))
            .order_by(Unit.name.asc())
        )
        result = await self.db.execute(query)
        all_units = list(result.scalars().all())

        unit_dict = {}
        for u in all_units:
            unit_dict[u.id] = {
                "id": u.id,
                "name": u.name,
                "code": u.code,
                "description": u.description,
                "parent_id": u.parent_id,
                "created_at": u.created_at,
                "updated_at": u.updated_at,
                "unit_users": [
                    {
                        "id": user.id,
                        "email": user.email,
                        "full_name": user.full_name,
                        "title": user.title,
                        "role": user.role,
                        "is_active": user.is_active
                    } for user in u.unit_users
                ],
                "children": []
            }

        tree = []
        for u in all_units:
            if u.parent_id is None:
                tree.append(unit_dict[u.id])
            else:
                if u.parent_id in unit_dict:
                    unit_dict[u.parent_id]["children"].append(unit_dict[u.id])
                    
        return tree

    async def get_children_by_parent_id(self, parent_id: int) -> List[Unit]:
        """
        Belirli bir üst birime ait doğrudan alt birimleri getirir.
        """
        query = (
            select(Unit)
            .where(Unit.parent_id == parent_id)
            .order_by(Unit.name.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())