from pydantic import BaseModel, Field
from typing import Dict

class DesignTokens(BaseModel):
    colors: Dict[str, str] = Field(default_factory=dict)
    typography: Dict[str, str] = Field(default_factory=dict)
    spacing: Dict[str, str] = Field(default_factory=dict)
    radii: Dict[str, str] = Field(default_factory=dict)
    shadows: Dict[str, str] = Field(default_factory=dict)
