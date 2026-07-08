from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.Projects.models import ProjectModel
from src.Projects.dtos import CreateProjectRequest
from src.Projects import db_queries
from src.utils import supabase_client


def get_all_projects_for_user(user_id: int, db: Session):
    return db_queries.get_all_projects_by_user(user_id, db)


def get_single_project_with_messages(project_id: int, user_id: int, db: Session):
    project = db_queries.get_project_by_id(project_id, db)

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    if project.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    chat_messages = supabase_client.get_all_messages_in_project(project_id)

    return {
        "id": project.id,
        "user_id": project.user_id,
        "title": project.title,
        "description": project.description,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "chat_messages": chat_messages,
    }


def create_project_for_user(project_data: CreateProjectRequest, user_id: int, db: Session):
    new_project = ProjectModel(
        user_id=user_id,
        title=project_data.title,
        description=project_data.description,
    )
    return db_queries.create_new_project(new_project, db)


def delete_project_for_user(project_id: int, user_id: int, db: Session):
    project = db_queries.get_project_by_id(project_id, db)

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    if project.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    supabase_client.delete_all_messages_in_project(project_id)
    return db_queries.delete_project_by_id(project_id, db)


def rename_project_for_user(project_id: int, new_title: str, user_id: int, db: Session):
    project = db_queries.get_project_by_id(project_id, db)

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    if project.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return db_queries.update_project_title(project_id, new_title, db)

def save_user_message_to_project(project_id: int, message_text: str) -> dict:
    return supabase_client.save_message_to_project(
        project_id=project_id,
        role="user",
        message_text=message_text,
    )


def save_ai_response_to_project(
    project_id: int,
    ai_response_text: str,
    generated_code: str,
) -> dict:
    return supabase_client.save_message_to_project(
        project_id=project_id,
        role="ai",
        message_text=ai_response_text,
        generated_code=generated_code,
    )
