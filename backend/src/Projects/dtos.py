from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class CreateProjectRequest(BaseModel):
    title: str
    description: Optional[str] = None


class UpdateProjectRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ChatMessageResponse(BaseModel):
    id: str              # Firestore document ID is a string
    role: str            # 'user' or 'ai'
    message_text: str
    generated_code: Optional[str]
    created_at: Any      # Firestore returns a datetime or timestamp object


class ProjectWithMessagesResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    chat_messages: List[ChatMessageResponse] = []
