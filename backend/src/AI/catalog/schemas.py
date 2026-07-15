from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class DesignIntent(BaseModel):
    website_category: str = ""
    industry: str = ""
    target_audience: str = ""
    brand_personality: str = ""
    visual_style: str = ""
    tone: str = ""
    business_type: str = ""
    desired_feeling: str = ""
    page_complexity: str = ""
    animation_preference: str = ""
    color_preference: str = ""
    ux_priority: str = ""

class DesignMetadata(BaseModel):
    id: str
    display_name: str
    source: str  # "external" or "custom"
    category: str = "general"
    tags: List[str] = Field(default_factory=list)
    short_description: str = ""
    relative_path: str # path to the DESIGN.md
    preview_path: Optional[str] = None
    token_path: Optional[str] = None
    examples_path: Optional[str] = None
    supported_features: List[str] = Field(default_factory=list)
    
    # Enhanced attributes
    industries: List[str] = Field(default_factory=list)
    styles: List[str] = Field(default_factory=list)
    tone: str = ""
    complexity_score: int = 50
    motion_level: int = 50
    visual_density: int = 50
    minimalism_score: int = 50
    premium_score: int = 50
    accessibility_score: int = 50
    best_for: List[str] = Field(default_factory=list)
    avoid_for: List[str] = Field(default_factory=list)

class DesignCatalogCache(BaseModel):
    version: int = 2
    designs: Dict[str, DesignMetadata] = Field(default_factory=dict)

class RankedDesign(BaseModel):
    design: DesignMetadata
    score: float
    confidence: float
    reason: str
    similar_designs: List[DesignMetadata] = Field(default_factory=list)

