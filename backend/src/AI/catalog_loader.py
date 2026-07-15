import os
import re

def parse_design_md(file_path: str) -> list[dict]:
    designs = []
    
    if not os.path.exists(file_path):
        return designs
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Split by the markdown horizontal rule '---' or '## DESIGN_ID'
    sections = re.split(r'\n---\n|\n##\s+DESIGN_ID:', content)
    
    for section in sections:
        section = section.strip()
        if not section or section.startswith('# Website Design Catalog'):
            continue
            
        design_data = {}
        
        # If it was split by '---', it still has the '## DESIGN_ID: ' prefix in it
        if section.startswith('## DESIGN_ID:'):
            section = section.replace('## DESIGN_ID:', '', 1).strip()
            
        # The first line is the ID now (or it might have been split out)
        lines = section.split('\n')
        
        # If we split by '## DESIGN_ID:', the first string might just be the ID
        first_line = lines[0].strip()
        if not first_line:
            continue
            
        design_data['id'] = first_line
        
        # Parse the rest of the key-value pairs
        # Format: **KEY**: Value
        for line in lines[1:]:
            line = line.strip()
            match = re.match(r'\*\*(.+?)\*\*:\s*(.*)', line)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                # Use lower case keys for consistency
                design_data[key.lower()] = value
                
        if 'id' in design_data and 'display_name' in design_data:
            designs.append(design_data)
            
    return designs


class DesignCatalog:
    _designs = None
    
    @classmethod
    def load(cls):
        if cls._designs is None:
            design_md_path = os.path.join(os.path.dirname(__file__), 'design.md')
            cls._designs = parse_design_md(design_md_path)
            
    @classmethod
    def get_all_designs(cls) -> list[dict]:
        cls.load()
        return cls._designs
        
    @classmethod
    def get_lightweight_catalog(cls) -> list[dict]:
        cls.load()
        return [
            {
                "id": d.get("id"),
                "display_name": d.get("display_name"),
                "short_description": d.get("description"),
                "best_for": d.get("best_for")
            }
            for d in cls._designs
        ]
        
    @classmethod
    def get_design_by_id(cls, design_id: str) -> dict | None:
        cls.load()
        for d in cls._designs:
            if d.get("id") == design_id:
                return d
        return None
