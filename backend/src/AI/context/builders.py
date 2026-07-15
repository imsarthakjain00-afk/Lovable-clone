from typing import Dict, Any
from src.AI.memory.brain import ProjectBrain

class DiscoveryContextBuilder:
    @staticmethod
    def build(brain: ProjectBrain, next_question: str) -> Dict[str, Any]:
        return {
            "explicit_decisions": {k: v.value for k, v in brain.memory.decisions.items() if v.status == 'confirmed'},
            "project_facts": brain.memory.project_facts,
            "category": brain.website_category,
            "active_question": next_question
        }

class PlanningContextBuilder:
    @staticmethod
    def build(brain: ProjectBrain) -> Dict[str, Any]:
        return {
            "category": brain.website_category,
            "project_facts": brain.memory.project_facts,
            "constraints": brain.memory.constraints,
            "explicit_decisions": {k: v.value for k, v in brain.memory.decisions.items() if v.status == 'confirmed'}
        }

class GenerationContextBuilder:
    @staticmethod
    def build(brain: ProjectBrain, component_registry: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "website_plan": brain.website_plan.model_dump() if brain.website_plan else {},
            "design_brain": brain.design.model_dump() if brain.design else {},
            "component_registry": component_registry
        }

class EditingContextBuilder:
    @staticmethod
    def build(brain: ProjectBrain, affected_files: Dict[str, str]) -> Dict[str, Any]:
        """
        affected_files is a dict of filename -> file content
        """
        return {
            "design_brain": brain.design.model_dump() if brain.design else {},
            "affected_files": affected_files
        }
