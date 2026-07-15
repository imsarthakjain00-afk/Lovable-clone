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


def update_project_state(project_id: int, workflow_state: str, project_brain: dict, file_manifest: dict, db: Session):
    project = get_project_by_id(project_id, db)
    if project:
        project.workflow_state = workflow_state
        project.project_brain = project_brain
        project.file_manifest = file_manifest
        db.commit()
        db.refresh(project)
    return project


def get_latest_project_version(project_id: int, db: Session):
    from src.Projects.models import ProjectVersion
    return (
        db.query(ProjectVersion)
        .filter(ProjectVersion.project_id == project_id)
        .order_by(ProjectVersion.version_number.desc())
        .first()
    )


def save_project_version(project_id: int, manifest: dict, commit_message: str, db: Session):
    """Persists a new version of the project file manifest."""
    from src.Projects.models import ProjectVersion
    project = get_project_by_id(project_id, db)
    if not project:
        return None
        
    project.generation_count = (project.generation_count or 0) + 1
    project.file_manifest = manifest
    
    new_version = ProjectVersion(
        project_id=project_id,
        version_number=project.generation_count,
        file_manifest=manifest,
        commit_message=commit_message
    )
    db.add(new_version)
    db.commit()
    db.refresh(project)
    return project


def save_deployed_url(project_id: int, url: str, db: Session):
    project = get_project_by_id(project_id, db)
    if project:
        project.deployed_url = url
        db.commit()
        db.refresh(project)
    return project
