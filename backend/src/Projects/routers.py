from fastapi import APIRouter, Depends, status, Request, HTTPException
from sqlalchemy.orm import Session
from typing import List
from src.Projects.dtos import CreateProjectRequest, UpdateProjectRequest, ProjectResponse, ProjectWithMessagesResponse
from src.Projects import controller
from src.utils.db import get_db
from src.Users.services import is_authenticated_service

project_routes = APIRouter(prefix="/projects", tags=["Projects"])


def get_current_user(request: Request, db: Session = Depends(get_db)):
    return is_authenticated_service(request, db)


@project_routes.get("/", response_model=List[ProjectResponse], status_code=status.HTTP_200_OK)
def list_all_projects(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return controller.get_all_projects(current_user.id, db)


@project_routes.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_new_project(
    project_data: CreateProjectRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return controller.create_project(project_data, current_user.id, db)


@project_routes.post("/{project_id}/deploy", status_code=status.HTTP_200_OK)
async def deploy_project(
    project_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = controller.get_project_with_chat_history(project_id, current_user.id, db)
    
    # Find the latest generated HTML code
    latest_code = None
    for msg in reversed(project["chat_messages"]):
        if msg.get("generated_code"):
            latest_code = msg["generated_code"]
            break
            
    if not latest_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No generated code found in this project to deploy."
        )
        
    from src.Projects.deployment_service import deploy_to_vercel
    deploy_url = await deploy_to_vercel(latest_code, project["title"])
    return {"url": deploy_url}


@project_routes.get("/{project_id}", status_code=status.HTTP_200_OK)
def get_project_with_chat_history(
    project_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return controller.get_project_with_chat_history(project_id, current_user.id, db)


@project_routes.patch("/{project_id}", response_model=ProjectResponse, status_code=status.HTTP_200_OK)
def rename_project(
    project_id: int,
    update_data: UpdateProjectRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return controller.rename_project(project_id, update_data.title, current_user.id, db)


@project_routes.delete("/{project_id}", status_code=status.HTTP_200_OK)
def delete_project(
    project_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller.delete_project(project_id, current_user.id, db)
    return {"message": "Project deleted successfully."}
