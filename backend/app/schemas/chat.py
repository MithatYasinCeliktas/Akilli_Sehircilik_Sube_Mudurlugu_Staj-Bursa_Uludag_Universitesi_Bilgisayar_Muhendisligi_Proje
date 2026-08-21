from pydantic import BaseModel
from typing import Optional

class ChatMessageRequest(BaseModel):
    message: str

class ChatMessageResponse(BaseModel):
    intent: str
    message: str
    route: Optional[str] = None
    action_trigger: Optional[str] = None
