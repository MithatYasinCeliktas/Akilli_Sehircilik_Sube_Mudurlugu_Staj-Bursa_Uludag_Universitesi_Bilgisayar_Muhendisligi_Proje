from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class NotificationBase(BaseModel):
    message: str
    type: str
    reference_id: Optional[int] = None

class NotificationCreate(NotificationBase):
    user_id: int

class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
