from enum import Enum
from typing import Optional
from sqlalchemy import ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class ShareStatus(str, Enum):
    """
    Rapor paylaşım durumu.
    Kullanıcı paylaşım isteğinde bulunduğunda PENDING (Onay Bekliyor),
    Yöneticisi onayladığında APPROVED, reddettiğinde REJECTED olur.
    Onaylanmış bir paylaşım yetkisi sonradan geri alınırsa REVOKED olur.
    """
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"


class ReportShare(BaseModel):
    """
    Kullanıcıların raporlarını diğer birimler veya kişilerle paylaşım yetkisini ve 
    bu işlemin yönetici onayı sürecini tutan veritabanı modeli.
    """
    __tablename__ = "report_shares"

    report_id: Mapped[int] = mapped_column(
        ForeignKey("activity_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Paylaşılmak istenen rapor ID'si"
    )
    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Paylaşımı talep eden kullanıcı ID'si (Genelde raporun sahibi)"
    )
    manager_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Onay verecek/vermiş yönetici ID'si (Talep edenin yöneticisi)"
    )
    
    # Hedef (Target) - Ya bir kullanıcıya ya da bir birime gönderilir
    target_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Paylaşımın yapılacağı hedef kullanıcı (Varsa)"
    )
    target_unit_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("units.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Paylaşımın yapılacağı hedef birim (Varsa, birim altındakiler görebilir)"
    )
    
    status: Mapped[ShareStatus] = mapped_column(
        SQLEnum(ShareStatus, name="sharestatus", create_type=True),
        nullable=False,
        default=ShareStatus.PENDING,
        index=True,
        comment="Paylaşım onay durumu"
    )
    
    manager_note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Yöneticinin onay/red/iptal işlemi sırasında girdiği not (Opsiyonel)"
    )

    # ORM İlişkileri
    report: Mapped["ActivityReport"] = relationship(
        "ActivityReport",
        lazy="selectin"
    )
    requester: Mapped["User"] = relationship(
        "User",
        foreign_keys=[requester_id],
        lazy="selectin"
    )
    manager: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[manager_id],
        lazy="selectin"
    )
    target_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[target_user_id],
        lazy="selectin"
    )
    target_unit: Mapped[Optional["Unit"]] = relationship(
        "Unit",
        foreign_keys=[target_unit_id],
        lazy="selectin"
    )

# Circular import önleme amaçlı re-export desteği
from app.models.user import User  # noqa: E402, F401
from app.models.unit import Unit  # noqa: E402, F401
from app.models.report import ActivityReport  # noqa: E402, F401
