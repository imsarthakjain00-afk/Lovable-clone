from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from src.utils.db import Base


class ProjectModel(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    title = Column(String, nullable=False, default="Untitled Project")
    description = Column(Text, nullable=True)
    
    # State representation for the unified website creation agent
    workflow_state = Column(String, nullable=False, default="DISCOVERY")
    
    # Structured project specification (JSON)
    project_brain = Column(JSON, nullable=True, default={})
    
    # File manifest for generated output (JSON)
    file_manifest = Column(JSON, nullable=True, default={})
    
    # Selected design ID
    design_id = Column(String, nullable=True)
    
    # Generation counter (increments on each new generation)
    generation_count = Column(Integer, nullable=False, default=0)

    # Vercel deployment URL — set after user publishes
    deployed_url = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ProjectVersion(Base):
    __tablename__ = "project_versions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, index=True) # Usually a ForeignKey, but keeping it simple
    version_number = Column(Integer, nullable=False)
    file_manifest = Column(JSON, nullable=False) # The actual file tree {"src/App.jsx": "...", ...}
    commit_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
