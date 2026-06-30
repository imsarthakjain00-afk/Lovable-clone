from sqlalchemy.orm import Session
from src.Projects.models import ProjectModel, ChatMessageModel


# ─── Project Queries ──────────────────────────────────────────────────────────

def get_all_projects_by_user(user_id: int, db: Session):
    """Return all projects belonging to a specific user."""
    return (
        db.query(ProjectModel)
        .filter(ProjectModel.user_id == user_id)
        .order_by(ProjectModel.created_at.desc())
        .all()
    )


def get_project_by_id(project_id: int, db: Session):
    """Return a single project by its ID."""
    return db.query(ProjectModel).filter(ProjectModel.id == project_id).first()


def create_new_project(project: ProjectModel, db: Session):
    """Save a new project to the database and return it."""
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def delete_project_by_id(project_id: int, db: Session):
    """Delete a project and all its chat messages (cascade)."""
    project = get_project_by_id(project_id, db)
    if project:
        db.delete(project)
        db.commit()
    return project


# ─── Chat Message Queries ─────────────────────────────────────────────────────

def get_all_messages_in_project(project_id: int, db: Session):
    """Return all chat messages in a project, oldest first."""
    return (
        db.query(ChatMessageModel)
        .filter(ChatMessageModel.project_id == project_id)
        .order_by(ChatMessageModel.created_at.asc())
        .all()
    )


def save_chat_message(chat_message: ChatMessageModel, db: Session):
    """Save a new chat message to the database and return it."""
    db.add(chat_message)
    db.commit()
    db.refresh(chat_message)
    return chat_message
