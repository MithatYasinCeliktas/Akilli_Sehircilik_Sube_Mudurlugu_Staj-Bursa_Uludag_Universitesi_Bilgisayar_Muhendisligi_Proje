from datetime import datetime
from typing import Optional
from pydantic import EmailStr, Field
from app.models.user import UserRole
from app.schemas.common import BaseSchema
from app.schemas.unit import UnitResponse


class UserBase(BaseSchema):
    """
    Kullanıcı verileri için temel Pydantic şeması.
    """
    email: EmailStr = Field(..., description="Kullanıcı e-posta adresi")
    full_name: str = Field(..., max_length=255, description="Ad Soyad")
    title: Optional[str] = Field(None, max_length=150, description="Ünvan / Görev")
    role: UserRole = Field(default=UserRole.USER, description="Kullanıcı rolü (ADMIN, MANAGER, USER)")
    is_active: bool = Field(default=True, description="Kullanıcı aktiflik durumu")
    is_superuser: bool = Field(default=False, description="Sistem yöneticisi yetkisi")
    unit_id: Optional[int] = Field(None, description="Birim ID")
    manager_id: Optional[int] = Field(None, description="Yönetici ID")
    ui_settings: Optional[dict] = Field(None, description="Arayüz ayarları")


class UserCreate(UserBase):
    """
    Yeni kullanıcı oluşturma isteği için kullanılan DTO şeması.
    """
    password: str = Field(..., min_length=6, max_length=128, description="Kullanıcı şifresi")


class UserUpdate(BaseSchema):
    """
    Mevcut kullanıcı bilgilerini güncelleme DTO şeması.
    """
    email: Optional[EmailStr] = Field(None, description="E-posta adresi")
    full_name: Optional[str] = Field(None, max_length=255, description="Ad Soyad")
    title: Optional[str] = Field(None, max_length=150, description="Ünvan / Görev")
    role: Optional[UserRole] = Field(None, description="Kullanıcı rolü")
    is_active: Optional[bool] = Field(None, description="Aktiflik durumu")
    is_superuser: Optional[bool] = Field(None, description="Sistem yöneticisi yetkisi")
    unit_id: Optional[int] = Field(None, description="Birim ID")
    manager_id: Optional[int] = Field(None, description="Yönetici ID")
    password: Optional[str] = Field(None, min_length=6, max_length=128, description="Yeni şifre (Değiştirilmek istenirse)")
    ui_settings: Optional[dict] = Field(None, description="Arayüz ayarları")


class UserResponse(UserBase):
    """
    API yanıtlarında kullanıcı detaylarını dönmek için DTO şeması.
    """
    id: int
    created_at: datetime
    updated_at: datetime
    unit: Optional[UnitResponse] = None


class UserLogin(BaseSchema):
    """
    Kullanıcı giriş isteği DTO şeması.
    """
    email: EmailStr = Field(..., description="E-posta adresi")
    password: str = Field(..., description="Şifre")


class Token(BaseSchema):
    """
    Giriş başarılı olduğunda döndürülen JWT erişim belirteci DTO şeması.
    """
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseSchema):
    """
    JWT Token çözümlendiğinde içerikte taşınan kullanıcı kimlik bilgisini temsil eder.
    """
    sub: Optional[str] = None