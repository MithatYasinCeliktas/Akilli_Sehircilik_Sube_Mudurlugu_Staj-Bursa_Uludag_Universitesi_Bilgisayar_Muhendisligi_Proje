from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class TimestampMixin:
    """
    Tüm veritabanı modellerine otomatik olarak 'created_at' ve 'updated_at'
    zaman damgalarını kazandıran mixin sınıfı.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Kaydın oluşturulma tarihi"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Kaydın son güncellenme tarihi"
    )


class BaseModel(Base, TimestampMixin):
    """
    Tüm veritabanı tabloları için birincil anahtar (ID) ve zaman damgalarını
    içeren soyut (abstract) temel model sınıfı.
    """
    __abstract__ = True

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        index=True,
        comment="Benzersiz kayıt kimliği"
    )