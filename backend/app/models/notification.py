from datetime import datetime
from sqlalchemy import String, Text, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel

class Notification(BaseModel):
    """
    Sistem içi bildirim modeli.
    """
    __tablename__ = "notifications"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Bildirimin gönderildiği kullanıcı"
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Bildirim içeriği"
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Bildirimin okunma durumu"
    )
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Bildirim tipi (Örn: REJECTED_ITEM, MISSING_REPORT)"
    )
    reference_id: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        comment="İlgili kaydın ID'si (Örn: report_id veya report_item_id)"
    )

    user: Mapped["User"] = relationship(
        "User",
        lazy="selectin"
    )
