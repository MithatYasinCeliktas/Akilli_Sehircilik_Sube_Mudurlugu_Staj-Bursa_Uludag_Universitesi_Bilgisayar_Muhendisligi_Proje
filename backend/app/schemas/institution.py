from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class InstitutionBase(BaseModel):
    name: str = Field(..., max_length=255, description="Kurum / Kuruluş Adı")
    is_active: bool = Field(default=True, description="Aktif / Pasif durumu")


class InstitutionCreate(InstitutionBase):
    created_by_id: Optional[int] = None

class InstitutionUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255, description="Kurum / Kuruluş Adı")
    is_active: Optional[bool] = Field(None, description="Aktif / Pasif durumu")

class InstitutionResponse(InstitutionBase):
    id: int
    created_by_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
