from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from typing import List
from src.Projects.dtos import (
    CreateProjectRequest,
    ProjectResponse,
    ProjectWithMessagesResponse
)
from src.Projects import controller
from src.utils.db import get_db
from src.Users.services import is_authenticated_service

project_routes = APIRouter(prefix="/projects", tags=["Projects"])


def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Dependency: extracts the current logged-in user from the JWT token."""
    return is_authenticated_service(request, db)


@project_routes.get(
    "/",
    response_model=List[ProjectResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all projects for the logged-in user"
)
def list_all_projects(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return controller.get_all_projects(current_user.id, db)


@project_routes.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project"
)
def create_new_project(
    project_data: CreateProjectRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return controller.create_project(project_data, current_user.id, db)


@project_routes.get(
    "/{project_id}",
    response_model=ProjectWithMessagesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a single project with its full chat history"
)
def get_project_with_chat_history(
    project_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return controller.get_project_with_chat_history(project_id, current_user.id, db)


@project_routes.delete(
    "/{project_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a project and all its chat history"
)
def delete_project(
    project_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    controller.delete_project(project_id, current_user.id, db)
    return {"message": "Project deleted successfully."}
