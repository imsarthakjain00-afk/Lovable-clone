"""
Edit Pipeline Service

Implements targeted editing:
Impact Analysis -> Affected Files -> Patch Builder -> Quality Review -> Hot Reload
"""
import logging
from typing import Dict, Any, List, Optional
import json
import re
from src.AI.llm.provider import get_llm_provider
from src.AI.memory.brain import ProjectBrain

logger = logging.getLogger(__name__)

class EditPipelineService:
    @classmethod
    async def process_edit_request(cls, user_message: str, brain: ProjectBrain, file_manifest: Dict[str, str]) -> Dict[str, str]:
        """
        Processes a targeted edit request against the current file manifest.
        Returns the updated file manifest.
        """
        logger.info(f"[EditPipeline] Processing edit request: {user_message}")
        llm = get_llm_provider()
        
        # 1. Impact Analysis
        affected_files = await cls._impact_analysis(user_message, list(file_manifest.keys()), llm)
        logger.info(f"[EditPipeline] Affected files identified: {affected_files}")
        
        if not affected_files:
            logger.warning("[EditPipeline] No files identified for editing.")
            return file_manifest
            
        # 2. Patch Builder
        updated_manifest = dict(file_manifest) # copy
        for filename in affected_files:
            if filename in file_manifest:
                current_content = file_manifest[filename]
                new_content = await cls._build_patch(user_message, filename, current_content, llm)
                if new_content:
                    updated_manifest[filename] = new_content
            else:
                # User might have requested a new file
                new_content = await cls._build_patch(user_message, filename, "", llm)
                if new_content:
                    updated_manifest[filename] = new_content
                    
        # 3. Quality Review (Linting/Verification - to be implemented in validation stage)
        
        return updated_manifest

    @classmethod
    async def _impact_analysis(cls, user_message: str, available_files: List[str], llm) -> List[str]:
        """
        Determines which files need to be modified.
        """
        prompt = f"""You are a senior technical lead. The user wants to make a modification to their project.
        
USER REQUEST:
"{user_message}"

AVAILABLE FILES:
{json.dumps(available_files)}

Identify which files need to be modified to fulfill this request.
Output ONLY a JSON array of file paths. Example: ["src/App.jsx", "src/index.css"]
"""
        messages = [{"role": "user", "content": prompt}]
        raw = await llm.complete(messages, max_tokens=200, temperature=0.1)
        
        try:
            match = re.search(r'(\[.*\])', raw, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except Exception as e:
            logger.error(f"[ImpactAnalysis] Failed to parse affected files: {e}")
            
        return []

    @classmethod
    async def _build_patch(cls, user_message: str, filename: str, current_content: str, llm) -> Optional[str]:
        """
        Re-generates or patches a specific file based on the user's request.
        """
        logger.info(f"[PatchBuilder] Patching file: {filename}")
        
        prompt = f"""You are an elite frontend developer.
The user wants to make the following modification to `{filename}`:
"{user_message}"

CURRENT CONTENT OF `{filename}`:
```
{current_content}
```

Rewrite the entire file to incorporate the user's requested changes while keeping everything else perfectly intact.
Output ONLY the raw file content. Do not use markdown code blocks like ```jsx or ```css.
Start immediately with the file content.
"""
        messages = [{"role": "user", "content": prompt}]
        raw = await llm.complete(messages, max_tokens=8000, temperature=0.3)
        
        # Clean up any potential markdown wrapping
        raw_clean = raw.strip()
        if raw_clean.startswith("```"):
            lines = raw_clean.split("\n")
            if len(lines) > 1:
                raw_clean = "\n".join(lines[1:])
        if raw_clean.endswith("```"):
            raw_clean = raw_clean[:-3]
            
        return raw_clean.strip()
