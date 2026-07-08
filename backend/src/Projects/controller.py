from sqlalchemy.orm import Session
from src.Projects.dtos import CreateProjectRequest, UpdateProjectRequest
from src.Projects import services


def get_all_projects(user_id: int, db: Session):
    """Controller: get all projects for the current user."""
    return services.get_all_projects_for_user(user_id, db)


def get_project_with_chat_history(project_id: int, user_id: int, db: Session):
    """Controller: get one project with all its chat messages."""
    return services.get_single_project_with_messages(project_id, user_id, db)


def create_project(project_data: CreateProjectRequest, user_id: int, db: Session):
    """Controller: create a new project for the current user."""
    return services.create_project_for_user(project_data, user_id, db)


def delete_project(project_id: int, user_id: int, db: Session):
    """Controller: delete a project owned by the current user."""
    return services.delete_project_for_user(project_id, user_id, db)


def rename_project(project_id: int, new_title: str, user_id: int, db: Session):
    """Controller: rename a project owned by the current user."""
    return services.rename_project_for_user(project_id, new_title, user_id, db)
