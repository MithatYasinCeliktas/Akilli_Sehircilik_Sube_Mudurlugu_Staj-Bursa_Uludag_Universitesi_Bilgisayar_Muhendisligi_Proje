from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from datetime import datetime

class SystemLogBase(BaseModel):
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None

class SystemLogCreate(SystemLogBase):
    user_id: Optional[int] = None

class SystemLogResponse(SystemLogBase):
    id: int
    user_id: Optional[int]
    created_at: datetime
    
    # We can include user details in the response for the admin panel
    user_email: Optional[str] = None
    user_name: Optional[str] = None

    class Config:
        from_attributes = True

class SystemLogList(BaseModel):
    items: List[SystemLogResponse]
    total: int
    page: int
    size: int
    pages: int
