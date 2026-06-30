from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.Projects.models import ProjectModel, ChatMessageModel
from src.Projects.dtos import CreateProjectRequest, UpdateProjectRequest
from src.Projects import db_queries


def get_all_projects_for_user(user_id: int, db: Session):
    """Fetch all projects for the logged-in user."""
    return db_queries.get_all_projects_by_user(user_id, db)


def get_single_project_with_messages(project_id: int, user_id: int, db: Session):
    """
    Fetch one project by ID, including all its chat messages.
    Raises 404 if the project doesn't exist.
    Raises 403 if the project belongs to a different user.
    """
    project = db_queries.get_project_by_id(project_id, db)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )

    if project.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this project."
        )

    return project


def create_project_for_user(project_data: CreateProjectRequest, user_id: int, db: Session):
    """Create a new project for the logged-in user."""
    new_project = ProjectModel(
        user_id=user_id,
        title=project_data.title,
        description=project_data.description
    )
    return db_queries.create_new_project(new_project, db)


def delete_project_for_user(project_id: int, user_id: int, db: Session):
    """
    Delete a project if it belongs to the logged-in user.
    Raises 403 if the project belongs to someone else.
    """
    project = db_queries.get_project_by_id(project_id, db)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )

    if project.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this project."
        )

    return db_queries.delete_project_by_id(project_id, db)


def save_user_message_to_project(project_id: int, message_text: str, db: Session):
    """Save the user's chat message into the project's history."""
    user_message = ChatMessageModel(
        project_id=project_id,
        role="user",
        message_text=message_text
    )
    return db_queries.save_chat_message(user_message, db)


def save_ai_response_to_project(
    project_id: int,
    ai_response_text: str,
    generated_code: str,
    db: Session
):
    """Save the AI's response (text + generated code) into the project's history."""
    ai_message = ChatMessageModel(
        project_id=project_id,
        role="ai",
        message_text=ai_response_text,
        generated_code=generated_code
    )
    return db_queries.save_chat_message(ai_message, db)
