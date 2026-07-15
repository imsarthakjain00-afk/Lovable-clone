from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

class WebsiteBlueprint(BaseModel):
    navigation: List[str] = Field(default_factory=list)
    pages: List[str] = Field(default_factory=list)
    sections: Dict[str, List[str]] = Field(default_factory=dict)
    components: List[str] = Field(default_factory=list)
    content_hierarchy: Dict[str, Any] = Field(default_factory=dict)
    cta_locations: List[str] = Field(default_factory=list)
    forms: List[str] = Field(default_factory=list)
    cards: List[str] = Field(default_factory=list)
    image_placements: List[str] = Field(default_factory=list)
    responsive_strategy: str = ""
    accessibility_strategy: str = ""
    seo_strategy: str = ""
    estimated_complexity: str = ""
    estimated_component_count: int = 0
    estimated_generation_time: str = ""

class DesignBrain(BaseModel):
    typography: Dict[str, str] = Field(default_factory=dict)
    spacing: str = ""
    grid_system: str = ""
    border_radius: str = ""
    color_tokens: Dict[str, str] = Field(default_factory=dict)
    desktop_strategy: str = ""
    mobile_strategy: str = ""
    interaction_philosophy: str = ""
    accessibility_rules: List[str] = Field(default_factory=list)

import datetime

class DecisionState(BaseModel):
    status: str = Field(description="unknown, inferred, confirmed, conflicting, rejected")
    value: Any = None
    confidence: float = 0.0
    source: str = "user"
    reason: str = ""
    last_updated: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())

class DecisionEvent(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    field_id: str
    old_value: Any = None
    new_value: Any = None
    reason: str = ""

class ProjectMemory(BaseModel):
    decisions: Dict[str, DecisionState] = Field(default_factory=dict)
    timeline: List[DecisionEvent] = Field(default_factory=list)
    project_facts: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    design_version: int = 1

class ProjectBrain(BaseModel):
    website_category: Optional[str] = None
    memory: ProjectMemory = Field(default_factory=ProjectMemory)
    workflow_stage: str = "DISCOVERY"
    blueprint: Optional[WebsiteBlueprint] = None
    design_id: Optional[str] = None
    design: Optional[DesignBrain] = None
    completed_questions: List[str] = Field(default_factory=list)
