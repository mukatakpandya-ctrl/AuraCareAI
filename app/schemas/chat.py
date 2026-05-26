from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.chat import MessageRole


class ChatMessageOut(BaseModel):
    id: int
    session_id: int
    role: MessageRole
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionOut(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessageOut] = []

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None   # None = start a new session
