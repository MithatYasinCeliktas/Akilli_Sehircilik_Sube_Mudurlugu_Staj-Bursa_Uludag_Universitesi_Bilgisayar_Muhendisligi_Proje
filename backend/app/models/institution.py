from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from app.models.base import BaseModel

class Institution(BaseModel):
    """
    Koordinasyon gerektiren işlerdeki ilgili kurum/kuruluşları temsil eder.
    """
    __tablename__ = "institutions"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Kurum / Kuruluş Adı"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Aktif / Pasif durumu"
    )
    created_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Kurumu ekleyen kullanıcının ID'si"
    )
