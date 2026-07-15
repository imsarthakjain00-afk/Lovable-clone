import os
import json
import logging
from src.AI.catalog.schemas import DesignMetadata
import re

logger = logging.getLogger(__name__)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
EXTERNAL_DIR = os.path.join(ROOT_DIR, "design", "awesome-design-md", "design-md")
CUSTOM_DIR = os.path.join(ROOT_DIR, "design", "custom")

class CatalogLoader:
    @classmethod
    def extract_metadata(cls, dir_path: str, source: str) -> DesignMetadata:
        """
        Extracts metadata from a directory containing a DESIGN.md file.
        Reads metadata.json if exists, else infers from DESIGN.md frontmatter or folder name.
        """
        dir_name = os.path.basename(dir_path)
        design_id = f"{source}_{dir_name}"
        
        design_md_path = os.path.join(dir_path, "DESIGN.md")
        if not os.path.exists(design_md_path):
            design_md_path = os.path.join(dir_path, "design.md")
            
        metadata_json_path = os.path.join(dir_path, "metadata.json")
        
        # Defaults
        metadata = {
            "id": design_id,
            "display_name": dir_name.replace("-", " ").title(),
            "source": source,
            "category": "general",
            "tags": [],
            "short_description": f"Design template based on {dir_name}",
            "relative_path": design_md_path
        }
        
        # Check for metadata.json
        if os.path.exists(metadata_json_path):
            try:
                with open(metadata_json_path, "r", encoding="utf-8") as f:
                    meta_data = json.load(f)
                    metadata.update(meta_data)
                    metadata["id"] = design_id # ensure ID matches our format
                    metadata["source"] = source
            except Exception as e:
                logger.warning(f"Failed to parse {metadata_json_path}: {e}")
                
        else:
            # Try to infer some data from first few lines of DESIGN.md
            try:
                with open(design_md_path, "r", encoding="utf-8") as f:
                    for i in range(10):
                        line = f.readline()
                        if not line:
                            break
                        if line.startswith("# "):
                            metadata["display_name"] = line[2:].strip()
                            break
            except Exception:
                pass
                
        # Look for optional files
        if os.path.exists(os.path.join(dir_path, "preview.png")):
            metadata["preview_path"] = os.path.join(dir_path, "preview.png")
            
        if os.path.exists(os.path.join(dir_path, "tokens.json")):
            metadata["token_path"] = os.path.join(dir_path, "tokens.json")
            
        if os.path.exists(os.path.join(dir_path, "examples")):
            metadata["examples_path"] = os.path.join(dir_path, "examples")
            
        return DesignMetadata(**metadata)

    @classmethod
    def scan_directory(cls, base_dir: str, source: str) -> list[DesignMetadata]:
        designs = []
        if not os.path.exists(base_dir):
            return designs
            
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path):
                # Check if it has a DESIGN.md
                if os.path.exists(os.path.join(item_path, "DESIGN.md")) or os.path.exists(os.path.join(item_path, "design.md")):
                    try:
                        metadata = cls.extract_metadata(item_path, source)
                        designs.append(metadata)
                    except Exception as e:
                        logger.error(f"Failed to process design directory {item_path}: {e}")
                        
        return designs

    @classmethod
    def discover_all(cls) -> list[DesignMetadata]:
        designs = []
        designs.extend(cls.scan_directory(EXTERNAL_DIR, "external"))
        designs.extend(cls.scan_directory(CUSTOM_DIR, "custom"))
        return designs
