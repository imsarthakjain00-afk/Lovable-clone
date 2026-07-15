import logging
from typing import List, Tuple
from src.AI.catalog.registry import DesignRegistry
from src.AI.catalog.ranking import RecommendationEngine, RankedDesign
from src.AI.catalog.parser import DesignParser
from src.AI.catalog.tokenizer import DesignTokenizer
from src.AI.memory.brain import ProjectBrain, DesignBrain
from src.AI.memory.tokens import DesignTokens

logger = logging.getLogger(__name__)

class DesignCatalogService:
    @classmethod
    def startup(cls):
        """Called once at backend startup to load/cache metadata."""
        DesignRegistry.load()

    @classmethod
    async def get_recommendations(cls, brain: ProjectBrain) -> List[RankedDesign]:
        return await RecommendationEngine.get_recommendations(brain)

    @classmethod
    async def process_selection(cls, design_id: str) -> Tuple[DesignBrain, DesignTokens]:
        """
        Loads the selected design, parses it to a DesignBrain, and generates DesignTokens.
        """
        design_meta = DesignRegistry.get_by_id(design_id)
        if not design_meta:
            raise ValueError(f"Design {design_id} not found in registry.")
            
        design_brain = await DesignParser.parse_to_brain(design_meta)
        design_tokens = await DesignTokenizer.generate_tokens(design_brain)
        
        return design_brain, design_tokens

    @classmethod
    async def refine_design(cls, current_brain: DesignBrain, user_prompt: str) -> Tuple[DesignBrain, DesignTokens]:
        """
        Refines an existing DesignBrain using natural language and regenerates the associated DesignTokens.
        """
        from src.AI.catalog.refinement import DesignRefinementLayer
        refined_brain = await DesignRefinementLayer.refine_design_brain(current_brain, user_prompt)
        refined_tokens = await DesignTokenizer.generate_tokens(refined_brain)
        
        return refined_brain, refined_tokens
