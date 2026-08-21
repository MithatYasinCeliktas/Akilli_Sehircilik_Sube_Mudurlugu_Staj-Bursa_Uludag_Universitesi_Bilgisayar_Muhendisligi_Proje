from datetime import datetime
from typing import List, Optional
from pydantic import Field
from app.schemas.common import BaseSchema
from app.models.unit import UnitType


class UnitBase(BaseSchema):
    """
    Birim verileri için temel Pydantic şeması.
    """
    name: str = Field(..., max_length=255, description="Birim adı (Örn: Bilgi İşlem Dairesi Başkanlığı)")
    code: Optional[str] = Field(None, max_length=50, description="Birim kod tanımlayıcısı")
    description: Optional[str] = Field(None, max_length=500, description="Birim açıklaması")
    unit_type: UnitType = Field(default=UnitType.SUB_UNIT, description="Birim Tipi")
    parent_id: Optional[int] = Field(None, description="Üst birim ID'si")


class UnitCreate(UnitBase):
    """
    Yeni birim oluşturma isteği için kullanılan DTO şeması.
    """
    pass


class UnitUpdate(BaseSchema):
    """
    Mevcut birim bilgilerini güncelleme isteği için kullanılan DTO şeması.
    """
    name: Optional[str] = Field(None, max_length=255, description="Birim adı")
    code: Optional[str] = Field(None, max_length=50, description="Birim koda göre güncelleme")
    description: Optional[str] = Field(None, max_length=500, description="Açıklama")
    unit_type: Optional[UnitType] = Field(None, description="Birim Tipi")
    parent_id: Optional[int] = Field(None, description="Üst birim ID'si")


class UnitResponse(UnitBase):
    """
    API yanıtlarında tekil birim bilgisini dönmek için kullanılan DTO şeması.
    """
    id: int
    created_at: datetime
    updated_at: datetime


class UnitUserResponse(BaseSchema):
    """
    Birimlerin içinde listelenecek kullanıcıların sadeleştirilmiş DTO şeması.
    """
    id: int
    email: str
    full_name: Optional[str] = None
    title: Optional[str] = None
    role: str
    is_active: bool


class UnitTreeResponse(UnitResponse):
    """
    Birimlerin hiyerarşik ağaç yapısında sunulması için kullanılan özyinelemeli (recursive) DTO şeması.
    """
    children: List["UnitTreeResponse"] = Field(default_factory=list, description="Alt birimler listesi")
    unit_users: List[UnitUserResponse] = Field(default_factory=list, description="Birimde bulunan kullanıcılar")


# Pydantic v2 self-referencing (özyinelemeli) model yapısını çözümleme
UnitTreeResponse.model_rebuild()