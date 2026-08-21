from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.institution import Institution
from app.schemas.institution import InstitutionCreate, InstitutionUpdate
from app.core.exceptions import AppException


class InstitutionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_institutions(self, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[Institution]:
        query = select(Institution).order_by(Institution.name)
        if active_only:
            query = query.where(Institution.is_active == True)
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_institution_by_id(self, institution_id: int) -> Optional[Institution]:
        return await self.db.get(Institution, institution_id)

    async def get_institution_by_name(self, name: str) -> Optional[Institution]:
        result = await self.db.execute(select(Institution).where(Institution.name == name))
        return result.scalar_one_or_none()

    async def create_institution(self, inst_in: InstitutionCreate) -> Institution:
        existing = await self.get_institution_by_name(inst_in.name)
        if existing:
            raise AppException(status_code=400, detail="Bu isimde bir kurum zaten mevcut.")
            
        new_inst = Institution(
            name=inst_in.name,
            is_active=inst_in.is_active,
            created_by_id=inst_in.created_by_id
        )
        self.db.add(new_inst)
        await self.db.commit()
        await self.db.refresh(new_inst)
        return new_inst

    async def update_institution(self, institution_id: int, inst_in: InstitutionUpdate) -> Institution:
        inst = await self.get_institution_by_id(institution_id)
        if not inst:
            raise AppException(status_code=404, detail="Kurum bulunamadı.")

        if inst_in.name is not None and inst_in.name != inst.name:
            existing = await self.get_institution_by_name(inst_in.name)
            if existing:
                raise AppException(status_code=400, detail="Bu isimde başka bir kurum zaten mevcut.")
            inst.name = inst_in.name
            
        if inst_in.is_active is not None:
            inst.is_active = inst_in.is_active

        await self.db.commit()
        await self.db.refresh(inst)
        return inst

    async def delete_institution(self, institution_id: int) -> bool:
        inst = await self.get_institution_by_id(institution_id)
        if not inst:
            raise AppException(status_code=404, detail="Kurum bulunamadı.")
            
        await self.db.delete(inst)
        await self.db.commit()
        return True
