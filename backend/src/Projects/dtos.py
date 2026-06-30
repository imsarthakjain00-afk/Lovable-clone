from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ─── Project Schemas ──────────────────────────────────────────────────────────

class CreateProjectRequest(BaseModel):
    """Data needed to create a new project."""
    title: str
    description: Optional[str] = None


class UpdateProjectRequest(BaseModel):
    """Data allowed when updating an existing project."""
    title: Optional[str] = None
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    """Shape of a project returned to the frontend."""
    id: int
    user_id: int
    title: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── Chat Message Schemas ─────────────────────────────────────────────────────

class ChatMessageResponse(BaseModel):
    """Shape of a single chat message returned to the frontend."""
    id: int
    project_id: int
    role: str             # 'user' or 'ai'
    message_text: str
    generated_code: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectWithMessagesResponse(ProjectResponse):
    """A project with all its chat messages included."""
    chat_messages: List[ChatMessageResponse] = []

    class Config:
        from_attributes = True
