from typing import List, Dict, Any
from src.AI.catalog.schemas import RankedDesign

class RecommendationFormatter:
    @staticmethod
    def format_for_frontend(ranked_designs: List[RankedDesign]) -> List[Dict[str, Any]]:
        """
        Transforms backend RankedDesign objects into a premium presentation model
        for the frontend Recommendation Cards.
        """
        formatted = []
        for index, item in enumerate(ranked_designs):
            design = item.design
            formatted.append({
                "id": design.id,
                "display_name": design.display_name,
                "match_percentage": round(item.score),
                "confidence": round(item.confidence),
                "reason": item.reason,
                "category": design.category,
                "tags": design.tags,
                "preview_url": design.preview_path or "/placeholder-preview.png",
                "difficulty": "Advanced" if design.complexity_score > 70 else "Medium" if design.complexity_score > 40 else "Simple",
                "best_for": design.best_for,
                "visual_style": next(iter(design.styles)) if design.styles else "General",
                "premium_score": design.premium_score,
                "accessibility_score": design.accessibility_score,
                "is_recommended": index == 0,
                "estimated_generation_complexity": "High" if design.complexity_score > 60 else "Standard"
            })
        return formatted
