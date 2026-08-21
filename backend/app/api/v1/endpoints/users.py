from typing import Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.response import DataResponse
from app.models.user import User
from app.schemas.common import PaginatedData
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService
from app.services.log_service import LogService

router = APIRouter()


@router.get(
    "",
    response_model=DataResponse[PaginatedData[UserResponse]],
    summary="Kullanıcı Listesi ve Filtreleme",
    description="Arama metni, birim, müdürlük ve aktiflik durumuna göre kullanıcıları sayfalanmış olarak getirir."
)
async def read_users(
    search_text: Optional[str] = Query(None, description="Ad, soyad veya e-posta ile arama"),
    department_id: Optional[int] = Query(None, description="Daire Başkanlığı ID"),
    directorate_id: Optional[int] = Query(None, description="Şube Müdürlüğü ID"),
    manager_id: Optional[int] = Query(None, description="Yönetici ID"),
    unit_id: Optional[int] = Query(None, description="Birim ID"),
    role: Optional[str] = Query(None, description="Kullanıcı Rolü"),
    is_active: Optional[bool] = Query(None, description="Aktif/Pasif filtresi"),
    page: int = Query(1, ge=1, description="Sayfa numarası"),
    page_size: int = Query(10, ge=1, le=1000, description="Sayfa başına kayıt sayısı"),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    user_service = UserService(db)
    paginated_users = await user_service.get_users_paginated(
        search_text=search_text,
        department_id=department_id,
        directorate_id=directorate_id,
        manager_id=manager_id,
        unit_id=unit_id,
        role=role,
        is_active=is_active,
        page=page,
        page_size=page_size,
        current_user=current_user
    )
    return DataResponse(
        data=paginated_users,
        message="Kullanıcı listesi başarıyla getirildi."
    )


@router.get(
    "/{user_id}",
    response_model=DataResponse[UserResponse],
    summary="Kullanıcı Detayı",
    description="ID değerine göre kullanıcı profil ve birim detaylarını getirir."
)
async def read_user_by_id(
    user_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    user_service = UserService(db)
    user_data = await user_service.get_user_by_id(user_id)
    return DataResponse(
        data=user_data,
        message="Kullanıcı detayı başarıyla getirildi."
    )


@router.get(
    "/managers/valid/{unit_id}",
    response_model=DataResponse[list[UserResponse]],
    summary="Geçerli Yöneticileri Listele",
    description="Seçilen birim ve onun üst birimlerindeki yöneticileri listeler."
)
async def get_valid_managers(
    unit_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    user_service = UserService(db)
    managers = await user_service.get_valid_managers_for_unit(unit_id)
    return DataResponse(
        data=managers,
        message="Geçerli yöneticiler başarıyla getirildi."
    )



@router.post(
    "",
    response_model=DataResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Yeni Kullanıcı Oluşturma (Admin)",
    description="Sistem yöneticisi yetkisi ile yeni kullanıcı hesabı oluşturur."
)
async def create_user(
    user_in: UserCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    if not current_user.is_superuser and current_user.role.value not in ["ADMIN", "USER_MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için Admin veya Kullanıcı Yöneticisi yetkisi gereklidir."
        )

    user_service = UserService(db)
    # Servis katmanında current_user parametresi olmadığından oradaki mantık için burada kontrol yapıyoruz
    if current_user.role.value == "USER_MANAGER":
        if user_in.role.value == "ADMIN" or user_in.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Kullanıcı Yöneticisi (USER_MANAGER) rolü Admin veya Süper Yetkili oluşturamaz."
            )

    created_user = await user_service.create_user(user_in)
    
    await LogService.create_log(
        db=db,
        action="CREATE_USER",
        user_id=current_user.id,
        entity_type="USER",
        entity_id=created_user.id,
        details={"email": user_in.email, "role": user_in.role.value if hasattr(user_in.role, 'value') else user_in.role}
    )
    await db.commit()
    
    return DataResponse(
        data=created_user,
        message="Kullanıcı başarıyla oluşturuldu."
    )


@router.put(
    "/{user_id}",
    response_model=DataResponse[UserResponse],
    summary="Kullanıcı Güncelleme",
    description="Mevcut kullanıcının profil, birim veya rol bilgilerini günceller."
)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    if current_user.id != user_id and current_user.role.value not in ["ADMIN", "USER_MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Yalnızca kendi profilinizi güncelleyebilirsiniz."
        )

    user_service = UserService(db)
    
    if current_user.role.value == "USER_MANAGER" and current_user.id != user_id:
        if user_in.role and user_in.role.value == "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Kullanıcı Yöneticisi rolü Admin yetkisi veremez."
            )
        if getattr(user_in, 'is_superuser', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Kullanıcı Yöneticisi rolü Süper Yetki veremez."
            )
            
        target_user = await user_service.get_user_by_id(user_id)
        if target_user.role.value == "ADMIN" or target_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Kullanıcı Yöneticisi rolü Admin veya Süper Yetkilileri düzenleyemez."
            )

    updated_user = await user_service.update_user(user_id, user_in)
    
    await LogService.create_log(
        db=db,
        action="UPDATE_USER",
        user_id=current_user.id,
        entity_type="USER",
        entity_id=user_id,
        details=user_in.model_dump(exclude_unset=True)
    )
    await db.commit()
    
    return DataResponse(
        data=updated_user,
        message="Kullanıcı bilgileri başarıyla güncellendi."
    )


@router.delete(
    "/{user_id}",
    response_model=DataResponse[bool],
    summary="Kullanıcı Silme (Admin)",
    description="Sistem yöneticisi yetkisi ile kullanıcı kaydını siler."
)
async def delete_user(
    user_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    if not current_user.is_superuser and current_user.role.value != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kullanıcı silmek için Admin veya Sistem Yöneticisi yetkisi gereklidir."
        )
    user_service = UserService(db)
    result = await user_service.delete_user(user_id)
    
    await LogService.create_log(
        db=db,
        action="DELETE_USER",
        user_id=current_user.id,
        entity_type="USER",
        entity_id=user_id,
        details={}
    )
    await db.commit()
    
    return DataResponse(
        data=result,
        message="Kullanıcı kaydı başarıyla silindi."
    )