from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.exceptions import ForbiddenException
from app.models.user import User, UserRole
from app.schemas.institution import InstitutionCreate, InstitutionUpdate, InstitutionResponse
from app.core.response import DataResponse
from app.services.institution_service import InstitutionService
from app.services.log_service import LogService

router = APIRouter()


@router.get(
    "",
    response_model=DataResponse[List[InstitutionResponse]],
    summary="Tüm Kurumları Listele",
    description="Sistemdeki tüm kurumları döndürür. (Oturum açmış herkes görebilir)"
)
async def list_institutions(
    active_only: bool = Query(False, description="Sadece aktif kurumları getir"),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    service = InstitutionService(db)
    institutions = await service.get_institutions(active_only=active_only)
    return DataResponse(
        data=institutions,
        message="Kurumlar başarıyla listelendi."
    )


@router.post(
    "",
    response_model=DataResponse[InstitutionResponse],
    summary="Yeni Kurum Ekle",
    description="Sisteme yeni bir kurum/kuruluş ekler. (Herkes ekleyebilir)"
)
async def create_institution(
    inst_in: InstitutionCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    inst_in.created_by_id = current_user.id
    service = InstitutionService(db)
    new_inst = await service.create_institution(inst_in)
    
    await LogService.create_log(
        db=db,
        action="CREATE_INSTITUTION",
        user_id=current_user.id,
        entity_type="INSTITUTION",
        entity_id=new_inst.id,
        details={"name": inst_in.name}
    )
    await db.commit()
    
    return DataResponse(
        data=new_inst,
        message="Kurum başarıyla eklendi."
    )



from pydantic import BaseModel
class InstitutionRequestSchema(BaseModel):
    name: str

@router.post(
    "/request",
    response_model=DataResponse[bool],
    summary="Yeni Kurum Talebi Gönder",
    description="Personel rolündeki kullanıcıların yöneticisine kurum ekleme talebi göndermesini sağlar."
)
async def request_institution(
    req: InstitutionRequestSchema,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    from app.services.notification_service import NotificationService
    if not current_user.manager_id:
        raise ForbiddenException(detail="Yöneticiniz bulunmadığı için talep gönderilemiyor.")
        
    notification_service = NotificationService(db)
    message = f"{current_user.full_name}, sisteme yeni bir kurum/kuruluş eklenmesini talep ediyor: '{req.name}'"
    
    await notification_service.create_notification(
        user_id=current_user.manager_id,
        message=message,
        type="INSTITUTION_REQUEST",
        reference_id=None
    )
    await db.commit()
    
    return DataResponse(
        data=True,
        message="Kurum talebi yöneticinize başarıyla iletildi."
    )

@router.put(
    "/{institution_id}",
    response_model=DataResponse[InstitutionResponse],
    summary="Kurum Güncelle",
    description="Mevcut bir kurumun bilgilerini günceller. (Sadece oluşturan kişi veya ADMIN)"
)
async def update_institution(
    institution_id: int,
    inst_in: InstitutionUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    service = InstitutionService(db)
    inst = await service.get_institution_by_id(institution_id)
    if not inst:
        raise ForbiddenException(detail="Kurum bulunamadı.")
        
    # Yetki Kontrolü
    if current_user.role != UserRole.ADMIN and not current_user.is_superuser:
        if inst.created_by_id != current_user.id:
            raise ForbiddenException(detail="Sadece kendi eklediğiniz kurumları düzenleyebilirsiniz.")

    updated_inst = await service.update_institution(institution_id, inst_in)
    
    await LogService.create_log(
        db=db,
        action="UPDATE_INSTITUTION",
        user_id=current_user.id,
        entity_type="INSTITUTION",
        entity_id=institution_id,
        details=inst_in.model_dump(exclude_unset=True)
    )
    await db.commit()
    
    return DataResponse(
        data=updated_inst,
        message="Kurum başarıyla güncellendi."
    )


@router.delete(
    "/{institution_id}",
    response_model=DataResponse[bool],
    summary="Kurum Sil",
    description="Bir kurumu tamamen siler. (Sadece oluşturan kişi veya ADMIN)"
)
async def delete_institution(
    institution_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    service = InstitutionService(db)
    inst = await service.get_institution_by_id(institution_id)
    if not inst:
        raise ForbiddenException(detail="Kurum bulunamadı.")
        
    # Yetki Kontrolü
    if current_user.role != UserRole.ADMIN and not current_user.is_superuser:
        if inst.created_by_id != current_user.id:
            raise ForbiddenException(detail="Sadece kendi eklediğiniz kurumları silebilirsiniz.")

    await service.delete_institution(institution_id)
    
    await LogService.create_log(
        db=db,
        action="DELETE_INSTITUTION",
        user_id=current_user.id,
        entity_type="INSTITUTION",
        entity_id=institution_id,
        details={}
    )
    await db.commit()
    
    return DataResponse(data=True, message="Kurum başarıyla silindi.")
