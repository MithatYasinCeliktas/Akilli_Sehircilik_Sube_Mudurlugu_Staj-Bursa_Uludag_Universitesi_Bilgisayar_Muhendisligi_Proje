from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.report_share import ShareStatus

class UserInfo(BaseModel):
    id: int
    full_name: str
    title: Optional[str] = None
    email: str

    model_config = ConfigDict(from_attributes=True)

class UnitInfo(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class ReportInfo(BaseModel):
    id: int
    title: Optional[str] = None
    year: int
    month: int

    model_config = ConfigDict(from_attributes=True)

class ReportShareCreate(BaseModel):
    report_id: int
    target_user_id: Optional[int] = None
    target_unit_id: Optional[int] = None

class ReportShareAction(BaseModel):
    note: Optional[str] = None

class ReportShareResponse(BaseModel):
    id: int
    report_id: int
    requester_id: int
    manager_id: Optional[int]
    target_user_id: Optional[int]
    target_unit_id: Optional[int]
    status: ShareStatus
    manager_note: Optional[str]
    created_at: datetime
    updated_at: datetime

    report: Optional[ReportInfo] = None
    requester: Optional[UserInfo] = None
    manager: Optional[UserInfo] = None
    target_user: Optional[UserInfo] = None
    target_unit: Optional[UnitInfo] = None

    model_config = ConfigDict(from_attributes=True)
