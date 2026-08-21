from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, BadRequestException
from app.repositories.unit_repository import UnitRepository
from app.schemas.unit import UnitCreate, UnitUpdate, UnitResponse, UnitTreeResponse


class UnitService:
    """
    Birim hiyerarşisi (Daire Başkanlıkları, Şube Müdürlükleri vb.) ve 
    organizasyon ağacı işlemlerini yürüten servis sınıfı.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.unit_repo = UnitRepository(db)

    async def get_unit_by_id(self, unit_id: int) -> UnitResponse:
        """
        ID değerine göre birim detayını getirir.
        """
        unit = await self.unit_repo.get(unit_id)
        if not unit:
            raise NotFoundException(detail=f"{unit_id} ID'li birim bulunamadı.")
        return UnitResponse.model_validate(unit)

    async def get_unit_tree(self) -> List[UnitTreeResponse]:
        """
        Tüm birim organizasyon yapısını hiyerarşik ağaç biçiminde getirir.
        """
        tree_units = await self.unit_repo.get_unit_tree()
        return [UnitTreeResponse(**u) for u in tree_units]

    async def create_unit(self, unit_in: UnitCreate) -> UnitResponse:
        """
        Yeni birim ekler. Eğer üst birim (parent_id) belirtilmişse varlığını kontrol eder.
        """
        if unit_in.code:
            existing = await self.unit_repo.get_by_code(unit_in.code)
            if existing:
                raise BadRequestException(detail=f"'{unit_in.code}' koduna sahip bir birim zaten mevcut.")

        if unit_in.parent_id is not None:
            parent = await self.unit_repo.get(unit_in.parent_id)
            if not parent:
                raise BadRequestException(detail=f"Üst birim ID ({unit_in.parent_id}) veritabanında bulunamadı.")

        created_unit = await self.unit_repo.create(unit_in)
        await self.db.commit()
        return UnitResponse.model_validate(created_unit)

    async def update_unit(self, unit_id: int, unit_in: UnitUpdate) -> UnitResponse:
        """
        Mevcut birim bilgilerini günceller.
        """
        unit = await self.unit_repo.get(unit_id)
        if not unit:
            raise NotFoundException(detail=f"{unit_id} ID'li birim bulunamadı.")

        update_data = unit_in.model_dump(exclude_unset=True)

        if "code" in update_data and update_data["code"] != unit.code:
            existing = await self.unit_repo.get_by_code(update_data["code"])
            if existing and existing.id != unit_id:
                raise BadRequestException(detail=f"'{update_data['code']}' koduna sahip başka bir birim mevcut.")

        if "parent_id" in update_data and update_data["parent_id"] is not None:
            if update_data["parent_id"] == unit_id:
                raise BadRequestException(detail="Birim kendisinin üst birimi olamaz.")
            parent = await self.unit_repo.get(update_data["parent_id"])
            if not parent:
                raise BadRequestException(detail=f"Üst birim ID ({update_data['parent_id']}) bulunamadı.")

        updated_unit = await self.unit_repo.update(unit, update_data)
        await self.db.commit()
        return UnitResponse.model_validate(updated_unit)

    async def delete_unit(self, unit_id: int) -> bool:
        """
        Birim kaydını siler. Alt birimleri varsa silme işlemini engeller.
        """
        unit = await self.unit_repo.get(unit_id)
        if not unit:
            raise NotFoundException(detail=f"{unit_id} ID'li birim bulunamadı.")

        children = await self.unit_repo.get_children_by_parent_id(unit_id)
        if children:
            raise BadRequestException(detail="Alt birimleri bulunan bir birim doğrudan silinemez. Önce alt birimleri taşıyın veya silin.")

        await self.unit_repo.remove(unit_id)
        await self.db.commit()
        return True