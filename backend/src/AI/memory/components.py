from pydantic import BaseModel, Field
from typing import List

class UIComponent(BaseModel):
    name: str
    purpose: str
    file_path: str
    dependencies: List[str] = Field(default_factory=list)
    used_in_pages: List[str] = Field(default_factory=list)
    associated_styles: List[str] = Field(default_factory=list)
