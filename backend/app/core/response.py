from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """
    Tüm API endpoint'leri için standart zarf (Custom Response Wrapper) yapısı.
    """
    success: bool = Field(default=True, description="İşlemin başarı durumu")
    data: Optional[T] = Field(default=None, description="Yanıt verisi")
    message: str = Field(default="", description="İşlem veya bilgilendirme mesajı")
    errors: Optional[Any] = Field(default=None, description="Hata detayları")


DataResponse = APIResponse


def create_response(
    success: bool,
    data: Optional[Any] = None,
    message: str = "",
    errors: Optional[Any] = None
) -> dict:
    """
    Standart yanıt sözlüğü oluşturan yardımcı fonksiyon.
    """
    return {
        "success": success,
        "data": data,
        "message": message,
        "errors": errors
    }


def success_response(
    data: Optional[Any] = None,
    message: str = "İşlem başarıyla tamamlandı."
) -> dict:
    """
    Başarılı API yanıtı için standart zarf üretir.
    """
    return create_response(success=True, data=data, message=message, errors=None)


def error_response(
    message: str = "Bir işlem hatası oluştu.",
    errors: Optional[Any] = None
) -> dict:
    """
    Hatalı API yanıtı için standart zarf üretir.
    """
    return create_response(success=False, data=None, message=message, errors=errors)