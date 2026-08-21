from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.response import DataResponse
from app.models.user import User
from app.schemas.unit import UnitCreate, UnitUpdate, UnitResponse, UnitTreeResponse
from app.services.unit_service import UnitService
from app.services.log_service import LogService

router = APIRouter()


@router.get(
    "/tree",
    response_model=DataResponse[List[UnitTreeResponse]],
    summary="Birim Hiyerarşisi Ağaç Yapısı",
    description="Tüm belediye birimlerini (Daire Başkanlığı, Şube Müdürlüğü, Şeflik) hiyerarşik ağaç biçiminde getirir."
)
async def read_unit_tree(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    unit_service = UnitService(db)
    tree_data = await unit_service.get_unit_tree()
    return DataResponse(
        data=tree_data,
        message="Birim ağaç yapısı başarıyla getirildi."
    )


@router.get(
    "/{unit_id}",
    response_model=DataResponse[UnitResponse],
    summary="Birim Detayı",
    description="ID değerine göre birim bilgilerini getirir."
)
async def read_unit_by_id(
    unit_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    unit_service = UnitService(db)
    unit_data = await unit_service.get_unit_by_id(unit_id)
    return DataResponse(
        data=unit_data,
        message="Birim bilgisi başarıyla getirildi."
    )


@router.post(
    "",
    response_model=DataResponse[UnitResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Yeni Birim Oluşturma (Admin)",
    description="Sistem yöneticisi yetkisi ile organizasyon şemasına yeni birim ekler."
)
async def create_unit(
    unit_in: UnitCreate,
    current_user: User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
):
    unit_service = UnitService(db)
    created_unit = await unit_service.create_unit(unit_in)
    
    await LogService.create_log(
        db=db,
        action="CREATE_UNIT",
        user_id=current_user.id,
        entity_type="UNIT",
        entity_id=created_unit.id,
        details={"name": unit_in.name, "parent_id": unit_in.parent_id}
    )
    await db.commit()
    
    return DataResponse(
        data=created_unit,
        message="Birim başarıyla oluşturuldu."
    )


@router.put(
    "/{unit_id}",
    response_model=DataResponse[UnitResponse],
    summary="Birim Güncelleme (Admin)",
    description="Sistem yöneticisi yetkisi ile var olan bir birimin adını, kodunu veya üst birimini günceller."
)
async def update_unit(
    unit_id: int,
    unit_in: UnitUpdate,
    current_user: User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
):
    unit_service = UnitService(db)
    updated_unit = await unit_service.update_unit(unit_id, unit_in)
    
    await LogService.create_log(
        db=db,
        action="UPDATE_UNIT",
        user_id=current_user.id,
        entity_type="UNIT",
        entity_id=unit_id,
        details=unit_in.model_dump(exclude_unset=True)
    )
    await db.commit()
    
    return DataResponse(
        data=updated_unit,
        message="Birim bilgileri başarıyla güncellendi."
    )


@router.delete(
    "/{unit_id}",
    response_model=DataResponse[bool],
    summary="Birim Silme (Admin)",
    description="Sistem yöneticisi yetkisi ile alt birimi bulunmayan bir birimi siler."
)
async def delete_unit(
    unit_id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db)
):
    unit_service = UnitService(db)
    result = await unit_service.delete_unit(unit_id)
    
    await LogService.create_log(
        db=db,
        action="DELETE_UNIT",
        user_id=current_user.id,
        entity_type="UNIT",
        entity_id=unit_id,
        details={}
    )
    await db.commit()
    
    return DataResponse(
        data=result,
        message="Birim başarıyla silindi."
    )