from typing import Optional, Any, Dict
from sqlalchemy import String, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel

class SystemLog(BaseModel):
    __tablename__ = "system_logs"

    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="İşlemi yapan kullanıcı ID'si"
    )
    
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="İşlem tipi (örn: LOGIN, LOGOUT, CREATE_REPORT)"
    )
    
    entity_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Etkilenen varlık tipi (örn: REPORT, USER, vb.)"
    )
    
    entity_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="Etkilenen varlık ID'si"
    )
    
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="İşlem ile ilgili JSON formatında detaylar"
    )
    
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Kullanıcı IP adresi"
    )

    user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[user_id]
    )
