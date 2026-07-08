from sqlalchemy.orm import Session
from src.Projects.models import ProjectModel


def get_all_projects_by_user(user_id: int, db: Session):
    return (
        db.query(ProjectModel)
        .filter(ProjectModel.user_id == user_id)
        .order_by(ProjectModel.created_at.desc())
        .all()
    )


def get_project_by_id(project_id: int, db: Session):
    return db.query(ProjectModel).filter(ProjectModel.id == project_id).first()


def create_new_project(project: ProjectModel, db: Session):
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def delete_project_by_id(project_id: int, db: Session):
    project = get_project_by_id(project_id, db)
    if project:
        db.delete(project)
        db.commit()
    return project


def update_project_title(project_id: int, new_title: str, db: Session):
    project = get_project_by_id(project_id, db)
    if project:
        project.title = new_title
        db.commit()
        db.refresh(project)
    return project
