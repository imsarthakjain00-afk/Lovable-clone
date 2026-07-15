from typing import Dict, Any
from src.AI.memory.brain import ProjectBrain

class ProjectReviewBuilder:
    @staticmethod
    def build(brain: ProjectBrain) -> str:
        """
        Builds a comprehensive markdown-formatted Final Project Review.
        """
        review = "### Final Project Review\n\n"
        
        # Business & Website
        review += "#### Project Details\n"
        review += f"- **Category**: {brain.website_category or 'General'}\n"
        
        facts = "\n".join([f"  - {f}" for f in brain.memory.project_facts])
        if facts:
            review += f"- **Facts**:\n{facts}\n"
            
        constraints = "\n".join([f"  - {c}" for c in brain.memory.constraints])
        if constraints:
            review += f"- **Constraints**:\n{constraints}\n"

        # Blueprint Summary
        if brain.blueprint:
            review += "\n#### Website Blueprint\n"
            review += f"- **Estimated Pages**: {len(brain.blueprint.pages)}\n"
            review += f"- **Estimated Components**: {brain.blueprint.estimated_component_count}\n"
            if brain.blueprint.responsive_strategy:
                review += f"- **Responsive Strategy**: {brain.blueprint.responsive_strategy}\n"
            if brain.blueprint.accessibility_strategy:
                review += f"- **Accessibility**: {brain.blueprint.accessibility_strategy}\n"
                
        # Design
        review += "\n#### Design Selections\n"
        review += f"- **Selected Design ID**: {brain.design_id}\n"
        if brain.design:
            typography = ", ".join(brain.design.typography.values()) if brain.design.typography else "System Default"
            review += f"- **Typography**: {typography}\n"
            review += f"- **Interaction Philosophy**: {brain.design.interaction_philosophy}\n"
            
        review += "\n**Everything is ready. Should I begin generating your website?**"
        return review
