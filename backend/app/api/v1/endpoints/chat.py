from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from app.services.chat_service import ChatService

router = APIRouter()

@router.post("/message", response_model=ChatMessageResponse)
async def process_chat_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    chat_service = ChatService(db)
    response = await chat_service.process_message(current_user, request.message)
    return response
