from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """
    Tüm Pydantic v2 DTO'ları için temel sınıf.
    SQLAlchemy ORM nesnelerinden otomatik dönüşüm (from_attributes=True) sağlar.
    """
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class PaginationParams(BaseModel):
    """
    API isteklerinde sayfalama parametrelerini doğrulayan ve hesaplayan şema.
    """
    page: int = Field(default=1, ge=1, description="Sayfa numarası (1'den başlar)")
    page_size: int = Field(default=10, ge=1, le=100, description="Sayfa başına düşen kayıt sayısı")

    @property
    def skip(self) -> int:
        """
        SQL Query için 'offset' değerini hesaplar.
        """
        return (self.page - 1) * self.page_size


class PaginatedData(BaseSchema, Generic[T]):
    """
    Sayfalanmış veri yanıtları için jenerik (generic) veri yapısı.
    """
    items: List[T] = Field(..., description="Mevcut sayfadaki öğelerin listesi")
    total: int = Field(..., description="Veritabanındaki toplam kayıt sayısı")
    page: int = Field(..., description="Mevcut sayfa numarası")
    page_size: int = Field(..., description="Sayfa başına kayıt sayısı")
    total_pages: int = Field(..., description="Toplam sayfa sayısı")


class DateRangeFilter(BaseModel):
    """
    Tarih aralığı bazlı sorgulamalarda kullanılan filtre şeması.
    """
    start_date: Optional[str] = Field(None, description="Başlangıç tarihi (YYYY-MM-DD formatında)")
    end_date: Optional[str] = Field(None, description="Bitiş tarihi (YYYY-MM-DD formatında)")