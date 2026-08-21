from enum import Enum
from typing import List, Optional
from sqlalchemy import String, Text, Integer, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class ReportStatus(str, Enum):
    """
    Faaliyet raporu durumu. 
    Kullanıcı girdiğinde PENDING (Onay Bekliyor),
    Yönetici tarafından onaylandığında APPROVED, reddedildiğinde REJECTED olur.
    """
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ItemCategory(str, Enum):
    """
    İş kuralları gereğince 3 sabit faaliyet sınıfı.
    """
    YAPILAN_ISLER = "YAPILAN_ISLER"
    YAPILACAK_ISLER = "YAPILACAK_ISLER"
    KORDINASYON_GEREKTIREN_ISLER = "KORDINASYON_GEREKTIREN_ISLER"


class ActivityReport(BaseModel):
    """
    Kullanıcının aylık faaliyet raporu ana kaydı.
    """
    __tablename__ = "activity_reports"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Raporu oluşturan kullanıcı ID'si"
    )
    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Raporun ait olduğu yıl (örn: 2026)"
    )
    month: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Raporun ait olduğu ay (1-12)"
    )
    status: Mapped[ReportStatus] = mapped_column(
        SQLEnum(ReportStatus, name="reportstatus", create_type=True),
        nullable=False,
        default=ReportStatus.PENDING,
        index=True,
        comment="Raporun durumu (PENDING / APPROVED / REJECTED)"
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Rapor başlığı / özeti"
    )

    yapilan_is_ids: Mapped[Optional[list]] = mapped_column(JSON, default=list, comment="Yapılan işlerin ID'leri")
    yapilacak_is_ids: Mapped[Optional[list]] = mapped_column(JSON, default=list, comment="Yapılacak işlerin ID'leri")
    koordinasyon_is_ids: Mapped[Optional[list]] = mapped_column(JSON, default=list, comment="Kord. işlerin ID'leri")

    # ORM İlişkileri
    user: Mapped["User"] = relationship(
        "User",
        back_populates="reports",
        lazy="selectin"
    )
    items: Mapped[List["ReportItem"]] = relationship(
        "ReportItem",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="ReportItem.display_order",
        lazy="selectin"
    )

class ReportItem(BaseModel):
    """
    Faaliyet raporunun detay satırlarını temsil eden veritabanı modeli.
    3 sabit kategoriden birine ait olmak zorundadır.
    """
    __tablename__ = "report_items"

    report_id: Mapped[int] = mapped_column(
        ForeignKey("activity_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Ait olduğu faaliyet raporunun ID'si"
    )
    category: Mapped[ItemCategory] = mapped_column(
        SQLEnum(ItemCategory, name="itemcategory", create_type=True),
        nullable=False,
        index=True,
        comment="Faaliyet sınıfı (YAPILAN_ISLER, YAPILACAK_ISLER, KORDINASYON_GEREKTIREN_ISLER)"
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Faaliyet detay açıklaması / iş içeriği"
    )
    related_institutions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="İlgili/ilişkili kurum kuruluşlar (Sadece KORDINASYON_GEREKTIREN_ISLER için)"
    )
    solution_proposals: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Çözüm önerileri (Sadece KORDINASYON_GEREKTIREN_ISLER için)"
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Arayüzdeki sıralama düzeni"
    )
    creator_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Bu satırı ekleyen kullanıcının ID'si"
    )
    transfer_manager_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Satırı aktarım yapan yöneticinin ID'si"
    )
    status: Mapped[ReportStatus] = mapped_column(
        SQLEnum(ReportStatus, name="reportstatus", create_type=False),
        nullable=False,
        default=ReportStatus.PENDING,
        index=True,
        comment="Bu satırın durumu (PENDING / APPROVED / REJECTED)"
    )
    rejection_note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Yönetici satırı reddettiğinde girilen red nedeni"
    )
    source_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("report_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Bu satır başka bir rapordan (örneğin alta iletme durumunda) kopyalandıysa orijinal satırın ID'si"
    )

    # ORM İlişkileri
    report: Mapped["ActivityReport"] = relationship(
        "ActivityReport",
        back_populates="items"
    )
    creator: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[creator_id],
        lazy="selectin"
    )

class ProposalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class ReportItemProposal(BaseModel):
    """
    Excel'den alt çalışan adına yüklenen ve alt çalışanın onayını bekleyen taslak satırlar.
    """
    __tablename__ = "report_item_proposals"

    manager_report_id: Mapped[int] = mapped_column(
        ForeignKey("activity_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    target_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    creator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    category: Mapped[ItemCategory] = mapped_column(
        SQLEnum(ItemCategory, name="itemcategory", create_type=False),
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    related_institutions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    solution_proposals: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ProposalStatus] = mapped_column(
        SQLEnum(ProposalStatus, name="proposalstatus", create_type=True),
        nullable=False,
        default=ProposalStatus.PENDING
    )

    manager_report: Mapped["ActivityReport"] = relationship("ActivityReport")
    target_user: Mapped["User"] = relationship("User", foreign_keys=[target_user_id])
    creator: Mapped["User"] = relationship("User", foreign_keys=[creator_id])



# Circular import önleme amaçlı re-export
from app.models.user import User  # noqa: E402, F401