from typing import Generic, TypeVar, Type, Optional, List, Any, Union, Dict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.models.base import BaseModel as DBBaseModel

ModelType = TypeVar("ModelType", bound=DBBaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Tüm veritabanı repository sınıfları için jenerik (generic) CRUD işlemlerini sağlayan taban sınıf.
    SQLAlchemy 2.0 async standartlarına uygun olarak tasarlanmıştır.
    """

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: Any) -> Optional[ModelType]:
        """
        Primary key (ID) değerine göre tek bir kaydı getirir.
        """
        query = select(self.model).where(self.model.id == id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Belirtilen aralıkta (offset/limit) birden fazla kaydı getirir.
        """
        query = select(self.model).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(self) -> int:
        """
        Tablodaki toplam kayıt sayısını döndürür.
        """
        query = select(func.count()).select_from(self.model)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def create(self, obj_in: Union[CreateSchemaType, Dict[str, Any]]) -> ModelType:
        """
        Yeni bir veritabanı kaydı oluşturur.
        """
        if isinstance(obj_in, dict):
            create_data = obj_in
        else:
            create_data = obj_in.model_dump(exclude_unset=True)

        db_obj = self.model(**create_data)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Var olan bir veritabanı kaydını günceller.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def remove(self, id: Any) -> Optional[ModelType]:
        """
        ID değerine göre kaydı veritabanından siler ve silinen kaydı döndürür.
        """
        db_obj = await self.get(id)
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.flush()
        return db_obj