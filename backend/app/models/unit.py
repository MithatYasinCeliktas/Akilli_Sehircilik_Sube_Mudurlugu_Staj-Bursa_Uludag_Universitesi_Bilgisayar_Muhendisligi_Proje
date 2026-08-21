from enum import Enum
from typing import List, Optional
from sqlalchemy import String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class UnitType(str, Enum):
    DEPARTMENT = "DEPARTMENT"
    DIRECTORATE = "DIRECTORATE"
    SUB_UNIT = "SUB_UNIT"


class Unit(BaseModel):
    """
    Bursa Büyükşehir Belediyesi birim hiyerarşisini temsil eden veritabanı modeli.
    Self-referencing FK (parent_id) sayesinde Daire Başkanlığı, Şube Müdürlüğü, 
    Şeflik vb. ağaç yapısında esnek bir biçimde kurgulanabilir.
    """
    __tablename__ = "units"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Birim adı (Örn: Bilgi İşlem Dairesi Başkanlığı)"
    )
    code: Mapped[Optional[str]] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
        index=True,
        comment="Birim kod tanımlayıcısı"
    )
    unit_type: Mapped[UnitType] = mapped_column(
        SQLEnum(UnitType, name="unittype", create_type=True),
        nullable=False,
        default=UnitType.SUB_UNIT,
        index=True,
        server_default="SUB_UNIT",
        comment="Birim Tipi (DEPARTMENT, DIRECTORATE, SUB_UNIT)"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Birim hakkında açıklama"
    )
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("units.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Üst birim ID'si (Root birimlerde NULL)"
    )

    # Self-referencing Hiyerarşi İlişkileri
    parent: Mapped[Optional["Unit"]] = relationship(
        "Unit",
        remote_side="Unit.id",
        back_populates="children",
        lazy="selectin"
    )
    children: Mapped[List["Unit"]] = relationship(
        "Unit",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Kullanıcı İlişkileri
    unit_users: Mapped[List["User"]] = relationship(
        "User",
        foreign_keys="User.unit_id",
        back_populates="unit"
    )


# Circular import önleme amaçlı re-export desteği
from app.models.user import User  # noqa: E402, F401