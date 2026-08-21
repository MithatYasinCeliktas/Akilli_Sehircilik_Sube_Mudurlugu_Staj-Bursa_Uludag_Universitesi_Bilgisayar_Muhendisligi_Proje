from enum import Enum
from typing import List, Optional
from sqlalchemy import String, Boolean, ForeignKey, Enum as SQLEnum, JSON, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class UserRole(str, Enum):
    """
    Kullanıcı erişim yetkilerini belirleyen RBAC rol tanımları.
    """
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    USER = "USER"
    USER_MANAGER = "USER_MANAGER"


class User(BaseModel):
    """
    Bursa Büyükşehir Belediyesi çalışan ve yönetici verilerini temsil eden veritabanı modeli.
    RBAC rollerini, birim hiyerarşisi bağlamını ve doğrudan yönetici ilişkisini barındırır.
    """
    __tablename__ = "users"
    __table_args__ = (
        Index(
            "ix_unique_unit_manager",
            "unit_id",
            unique=True,
            postgresql_where=text("role = 'MANAGER'")
        ),
    )

    emaill: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
        comment="Kullanıcı e-posta adresi / Giriş kullanıcı adı"
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Kullanıcı e-posta adresi / Giriş kullanıcı adı"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Bcrypt ile şifrelenmiş parola"
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Ad Soyad"
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        comment="Ünvan / Görev Tanımı (Örn: Yazılım Uzmanı, Şube Müdürü)"
    )
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="userrole", create_type=True),
        nullable=False,
        default=UserRole.USER,
        index=True,
        comment="Sistem yetki rolü (ADMIN, MANAGER, USER)"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Kullanıcı hesabı aktif/pasif durumu"
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Sistem yöneticisi (superuser) yetkisi"
    )
    ui_settings: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Kullanıcıya özel arayüz ayarları (JSON)"
    )
    active_token_jti: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Aktif oturum token kimliği (Çoklu oturumu engellemek için)"
    )

    # Birim İlişkileri
    unit_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("units.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Bağlı olunan Birim ID'si"
    )

    # Yönetici Hiyerarşisi (Self-referencing FK)
    manager_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Doğrudan yönetici ID'si"
    )

    # ORM İlişki Tanımlamaları
    unit: Mapped[Optional["Unit"]] = relationship(
        "Unit",
        foreign_keys=[unit_id],
        back_populates="unit_users",
        lazy="selectin"
    )
    manager: Mapped[Optional["User"]] = relationship(
        "User",
        remote_side="User.id",
        back_populates="subordinates",
        lazy="selectin"
    )
    subordinates: Mapped[List["User"]] = relationship(
        "User",
        back_populates="manager"
    )
    reports: Mapped[List["ActivityReport"]] = relationship(
        "ActivityReport",
        back_populates="user",
        cascade="all, delete-orphan"
    )


# Circular import önleme amaçlı re-export desteği
from app.models.unit import Unit  # noqa: E402, F401
from app.models.report import ActivityReport  # noqa: E402, F401