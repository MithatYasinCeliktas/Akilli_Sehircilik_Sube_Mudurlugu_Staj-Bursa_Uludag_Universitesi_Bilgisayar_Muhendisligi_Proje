from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, BadRequestException
from app.core.security import get_password_hash
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedData
from app.schemas.user import UserCreate, UserUpdate, UserResponse


class UserService:
    """
    Kullanıcı yönetimi, filtreleme, güncelleme ve silme işlemlerini
    yürüten servis sınıfı.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def get_subordinate_ids_recursive(self, manager_id: int) -> list[int]:
        """
        Yöneticinin altındaki tüm çalışanların ID listesini recursive olarak sorgular.
        """
        from sqlalchemy import select
        from app.models.user import User

        allowed_ids = {manager_id}
        current_check_ids = [manager_id]

        while current_check_ids:
            query = select(User.id).where(User.manager_id.in_(current_check_ids))
            result = await self.db.execute(query)
            new_ids = [row[0] for row in result.all()]
            
            new_unseen_ids = [nid for nid in new_ids if nid not in allowed_ids]
            if not new_unseen_ids:
                break
                
            allowed_ids.update(new_unseen_ids)
            current_check_ids = new_unseen_ids

        return list(allowed_ids)

    async def get_ancestor_unit_ids(self, unit_id: int) -> list[int]:
        from app.models.unit import Unit
        ancestor_ids = []
        current_id = unit_id
        
        while current_id:
            unit = await self.db.get(Unit, current_id)
            if not unit or not unit.parent_id:
                break
            ancestor_ids.append(unit.parent_id)
            current_id = unit.parent_id
            
        return ancestor_ids

    async def get_valid_managers_for_unit(self, unit_id: int) -> list[UserResponse]:
        from sqlalchemy import select
        from app.models.user import User

        # Seçili birim ve onun tüm üst birimlerinin ID'lerini alıyoruz
        ancestor_ids = await self.get_ancestor_unit_ids(unit_id)
        valid_unit_ids = [unit_id] + ancestor_ids

        query = select(User).where(
            User.unit_id.in_(valid_unit_ids),
            User.role.in_(["MANAGER", "USER_MANAGER", "ADMIN"]),
            User.is_active == True
        )
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        return [UserResponse.model_validate(u) for u in users]

    async def _validate_manager_hierarchy(self, manager_id: Optional[int], unit_id: Optional[int]):
        if not manager_id or not unit_id:
            return
            
        manager = await self.user_repo.get(manager_id)
        if not manager:
            raise BadRequestException(detail="Atanan yönetici bulunamadı.")
            
        if not manager.unit_id:
            raise BadRequestException(detail="Yöneticinin bağlı olduğu bir birim (unit_id) yok, hiyerarşi doğrulanamıyor.")
            
        if manager.unit_id == unit_id:
            return
            
        ancestor_ids = await self.get_ancestor_unit_ids(unit_id)
        if manager.unit_id not in ancestor_ids:
            raise BadRequestException(detail="Seçilen yönetici, kullanıcının birim hiyerarşisine uygun değil. Yöneticinin birimi, kullanıcının birimiyle aynı veya hiyerarşik olarak daha üst bir birim olmalıdır.")

    async def get_user_by_id(self, user_id: int) -> UserResponse:
        """
        ID değerine göre kullanıcı bilgilerini getirir.
        """
        user = await self.user_repo.get_with_relations(user_id)
        if not user:
            raise NotFoundException(detail=f"{user_id} ID'li kullanıcı bulunamadı.")
        return UserResponse.model_validate(user)

    async def get_users_paginated(
        self,
        search_text: Optional[str] = None,
        department_id: Optional[int] = None,
        directorate_id: Optional[int] = None,
        manager_id: Optional[int] = None,
        unit_id: Optional[int] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 10,
        current_user: Optional[any] = None
    ) -> PaginatedData[UserResponse]:
        """
        Kullanıcıları arama, birim ve aktiflik kriterlerine göre sayfalı olarak listeler.
        Eğer current_user sağlanmışsa ve ADMIN değilse, sadece kendisini ve astlarını görebilir.
        """
        skip = (page - 1) * page_size
        
        allowed_user_ids = None
        current_role = getattr(current_user.role, 'value', current_user.role) if current_user else None
        if current_user and not (current_user.is_superuser or current_role in ["ADMIN", "USER_MANAGER"]):
            allowed_user_ids = await self.get_subordinate_ids_recursive(current_user.id)
        users, total = await self.user_repo.get_users_filtered(
            search_text=search_text,
            department_id=department_id,
            directorate_id=directorate_id,
            manager_id=manager_id,
            unit_id=unit_id,
            role=role,
            is_active=is_active,
            allowed_user_ids=allowed_user_ids,
            skip=skip,
            limit=page_size
        )

        items = [UserResponse.model_validate(user) for user in users]
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return PaginatedData[UserResponse](
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    async def create_user(self, user_in: UserCreate) -> UserResponse:
        """
        Yeni kullanıcı oluşturur.
        """
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise BadRequestException(detail="Bu e-posta adresi zaten kullanımda.")

        if user_in.is_superuser and user_in.role != "ADMIN":
            raise BadRequestException(detail="Süper yetkili olabilmek için kullanıcı rolü ADMIN olmalıdır.")
            
        await self._validate_manager_hierarchy(user_in.manager_id, user_in.unit_id)

        user_dict = user_in.model_dump()
        raw_password = user_dict.pop("password")
        user_dict["hashed_password"] = get_password_hash(raw_password)

        created_user = await self.user_repo.create(user_dict)
        await self.db.commit()

        full_user = await self.user_repo.get_with_relations(created_user.id)
        return UserResponse.model_validate(full_user)

    async def update_user(self, user_id: int, user_in: UserUpdate) -> UserResponse:
        """
        Var olan kullanıcının bilgilerini günceller.
        """
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundException(detail=f"{user_id} ID'li kullanıcı bulunamadı.")

        update_data = user_in.model_dump(exclude_unset=True)

        # Rol ADMIN değilse is_superuser True olamaz kontrolü
        new_role = update_data.get("role", user.role)
        role_str = new_role.value if hasattr(new_role, "value") else str(new_role)
        is_su = update_data.get("is_superuser", user.is_superuser)
        if is_su and role_str != "ADMIN":
            raise BadRequestException(detail="Süper yetkili olabilmek için kullanıcı rolü ADMIN olmalıdır.")

        if "email" in update_data and update_data["email"] != user.email:
            existing_user = await self.user_repo.get_by_email(update_data["email"])
            if existing_user and existing_user.id != user_id:
                raise BadRequestException(detail="Bu e-posta adresi başka bir kullanıcı tarafından kullanılmaktadır.")
                
        # Hiyerarşi doğrulaması
        manager_id = update_data.get("manager_id", user.manager_id)
        unit_id = update_data.get("unit_id", user.unit_id)
        if manager_id != user.manager_id or unit_id != user.unit_id:
            await self._validate_manager_hierarchy(manager_id, unit_id)

        if "password" in update_data and update_data["password"]:
            raw_password = update_data.pop("password")
            update_data["hashed_password"] = get_password_hash(raw_password)

        updated_user = await self.user_repo.update(user, update_data)
        await self.db.commit()

        full_user = await self.user_repo.get_with_relations(updated_user.id)
        return UserResponse.model_validate(full_user)

    async def delete_user(self, user_id: int) -> bool:
        """
        Kullanıcı kaydını siler.
        """
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundException(detail=f"{user_id} ID'li kullanıcı bulunamadı.")

        await self.user_repo.remove(user_id)
        await self.db.commit()
        return True