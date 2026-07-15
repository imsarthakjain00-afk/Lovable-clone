from pydantic import BaseModel, Field
from typing import Dict, List
import time
import hashlib

class FileMetadata(BaseModel):
    file_path: str
    purpose: str = ""
    dependencies: List[str] = Field(default_factory=list)
    version: int = 1
    content_hash: str = ""
    created_timestamp: float = Field(default_factory=time.time)
    updated_timestamp: float = Field(default_factory=time.time)

    def update_hash(self, content: str):
        new_hash = hashlib.sha256(content.encode()).hexdigest()
        if new_hash != self.content_hash:
            self.content_hash = new_hash
            self.version += 1
            self.updated_timestamp = time.time()

class ProjectManifest(BaseModel):
    files: Dict[str, FileMetadata] = Field(default_factory=dict)
