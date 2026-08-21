from datetime import datetime
from typing import List, Optional
from pydantic import Field, field_validator, model_validator
from app.models.report import ItemCategory, ReportStatus
from app.schemas.common import BaseSchema
from app.schemas.user import UserResponse


class ReportItemBase(BaseSchema):
    """
    Faaliyet raporu satırı için temel Pydantic şeması.
    """
    category: ItemCategory = Field(
        ..., 
        description="Faaliyet kategorisi (YAPILAN_ISLER, YAPILACAK_ISLER, KORDINASYON_GEREKTIREN_ISLER)"
    )
    content: str = Field(..., min_length=1, description="Faaliyet detay açıklaması")
    related_institutions: Optional[str] = Field(None, description="İlgili/ilişkili kurum kuruluşlar (KORDINASYON_GEREKTIREN_ISLER için)")
    solution_proposals: Optional[str] = Field(None, description="Çözüm önerileri (KORDINASYON_GEREKTIREN_ISLER için)")
    display_order: int = Field(default=0, ge=0, description="Görüntülenme sıralaması")


class ReportItemCreate(ReportItemBase):
    """
    Yeni faaliyet satırı ekleme DTO şeması.
    """
    @model_validator(mode='after')
    def validate_kordinasyon_fields(self) -> 'ReportItemCreate':
        if self.category == ItemCategory.KORDINASYON_GEREKTIREN_ISLER:
            if not self.related_institutions or not self.related_institutions.strip():
                raise ValueError("Koordinasyon gerektiren işlerde 'İlgili/İlişkili Kurum Kuruluşlar' alanı zorunludur.")
            if not self.solution_proposals or not self.solution_proposals.strip():
                raise ValueError("Koordinasyon gerektiren işlerde 'Çözüm Önerileri' alanı zorunludur.")
        return self


class ReportItemUpdate(BaseSchema):
    """
    Mevcut faaliyet satırını güncelleme DTO şeması.
    """
    id: Optional[int] = Field(None, description="Güncellenecek veya korunacak satır ID'si (Yeni satır ise NULL)")
    category: Optional[ItemCategory] = Field(None, description="Faaliyet kategorisi")
    content: Optional[str] = Field(None, min_length=1, description="Faaliyet açıklaması")
    related_institutions: Optional[str] = Field(None, description="İlgili/ilişkili kurum kuruluşlar")
    solution_proposals: Optional[str] = Field(None, description="Çözüm önerileri")
    display_order: Optional[int] = Field(None, ge=0, description="Sıralama düzeni")


class ReportItemResponse(ReportItemBase):
    """
    API yanitlarinda dondurulen faaliyet satiri DTO semasi.
    """
    id: int
    report_id: int
    creator_id: Optional[int] = None
    creator: Optional[UserResponse] = None
    transfer_manager: Optional[UserResponse] = None
    status: ReportStatus = Field(default=ReportStatus.PENDING, description="Satırın onay durumu")
    rejection_note: Optional[str] = Field(None, description="Reddedilme gerekçesi")
    source_item_id: Optional[int] = Field(None, description="Eğer bu satır alt çalışandan aktarıldıysa kaynak satırın ID'si")
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ReportItemReview(BaseSchema):
    """
    Yöneticinin bir satırı onaylama/reddetme şeması.
    """
    status: ReportStatus = Field(..., description="Satırın yeni onay durumu (APPROVED / REJECTED)")
    rejection_note: Optional[str] = Field(None, description="Eğer reddedildiyse sebebi")

    @model_validator(mode='after')
    def validate_rejection(self) -> 'ReportItemReview':
        if self.status == ReportStatus.REJECTED:
            if not self.rejection_note or not self.rejection_note.strip():
                raise ValueError("Reddedilen satırlar için reddetme nedeni (rejection_note) zorunludur.")
        return self


class ActivityReportBase(BaseSchema):
    """
    Faaliyet raporu ana kaydı için temel Pydantic şeması.
    """
    year: int = Field(..., ge=2000, le=2100, description="Raporun ait olduğu yıl")
    month: int = Field(..., ge=1, le=12, description="Raporun ait olduğu ay (1-12)")
    title: Optional[str] = Field(None, max_length=255, description="Rapor başlığı veya özeti")
    status: ReportStatus = Field(default=ReportStatus.PENDING, description="Raporun durumu (PENDING / APPROVED / REJECTED)")


class ActivityReportCreate(ActivityReportBase):
    """
    Yeni faaliyet raporu oluşturma isteği DTO şeması.
    """
    pass


class ActivityReportUpdate(BaseSchema):
    """
    Mevcut faaliyet raporunu güncelleme isteği DTO şeması.
    """
    year: Optional[int] = Field(None, ge=2000, le=2100, description="Yıl")
    month: Optional[int] = Field(None, ge=1, le=12, description="Ay")
    title: Optional[str] = Field(None, max_length=255, description="Başlık")
    status: Optional[ReportStatus] = Field(None, description="Durum (PENDING / APPROVED / REJECTED)")


class ActivityReportResponse(ActivityReportBase):
    """
    API yanıtlarında döndürülen detaylı faaliyet raporu DTO şeması.
    """
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    user: Optional[UserResponse] = None
    yapilan_isler: List[ReportItemResponse] = Field(default_factory=list)
    yapilacak_isler: List[ReportItemResponse] = Field(default_factory=list)
    koordinasyon_isleri: List[ReportItemResponse] = Field(default_factory=list)


class ReportFilter(BaseSchema):
    """
    Arama, sorgulama ve filtreleme parametreleri için kullanılan DTO şeması.
    """
    year: Optional[int] = Field(None, description="Yıla göre filtrele")
    month: Optional[int] = Field(None, description="Aya göre filtrele")
    status: Optional[ReportStatus] = Field(None, description="Statüye göre filtrele (PENDING / APPROVED / REJECTED)")
    category: Optional[ItemCategory] = Field(None, description="Faaliyet kategorisine göre filtrele")
    search_text: Optional[str] = Field(None, description="İçerik veya başlıkta geçen kelime araması (ILIKE)")
    user_ids: Optional[List[int]] = Field(None, description="Kullanıcı ID listesi (Yöneticiler için)")
    unit_id: Optional[int] = Field(None, description="Birim ID (Yöneticiler için)")
    start_date: Optional[str] = Field(None, description="Başlangıç tarihi (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="Bitiş tarihi (YYYY-MM-DD)")
    allowed_user_ids: Optional[List[int]] = Field(None, description="Yetkili olunan kullanıcı ID listesi")
    report_ids: Optional[List[int]] = Field(None, description="Spesifik rapor ID listesi")

class ProposalRespondRequest(BaseSchema):
    is_approved: bool
    content: Optional[str] = None
    related_institutions: Optional[str] = None
    solution_proposals: Optional[str] = None

class ReportItemProposalResponse(BaseSchema):
    id: int
    manager_report_id: int
    target_user_id: int
    creator_id: int
    category: ItemCategory
    content: str
    related_institutions: Optional[str] = None
    solution_proposals: Optional[str] = None
    status: str
    created_at: datetime
    creator: Optional[UserResponse] = None

class UnitReportItemResponse(BaseSchema):
    """
    Yöneticilerin kendi raporlarındaki ast satırlarını görmek için kullandığı DTO şeması.
    """
    id: int
    report_id: int
    report_title: Optional[str] = None
    report_year: int
    report_month: int
    content: str
    category: ItemCategory
    status: ReportStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    creator_id: Optional[int] = None
    creator_name: Optional[str] = None
    creator: Optional[UserResponse] = None
    related_institutions: Optional[str] = None
    solution_proposals: Optional[str] = None


class MergeItemsRequest(BaseSchema):
    item_ids: List[int]
    title: Optional[str] = None

class MergeReportsRequest(BaseSchema):
    report_ids: List[int]
    title: Optional[str] = None
