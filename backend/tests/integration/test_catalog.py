import pytest
import os
from src.AI.catalog.registry import DesignRegistry
from src.AI.catalog.ranking import RecommendationEngine
from src.AI.memory.brain import ProjectBrain, ProjectMemory
from src.AI.catalog.cache import DesignCache
from src.AI.catalog.service import DesignCatalogService

@pytest.mark.asyncio
async def test_repository_discovery():
    DesignRegistry.reload()
    designs = DesignRegistry.get_all()
    
    assert len(designs) > 0, "Failed to discover designs from external repository"
    
    # Check that metadata was extracted
    first_design = designs[0]
    assert first_design.id
    assert first_design.display_name
    assert first_design.source in ["external", "custom"]
    assert first_design.relative_path.endswith(".md")

@pytest.mark.asyncio
async def test_recommendation_engine():
    brain = ProjectBrain(
        website_category="SaaS",
        memory=ProjectMemory(
            decisions={},
            project_facts=["The user wants a modern, dark-mode focused aesthetic."],
            constraints=[]
        )
    )
    
    recommendations = await RecommendationEngine.get_recommendations(brain)
    assert len(recommendations) <= 3
    if recommendations:
        assert recommendations[0].score >= 0.0

@pytest.mark.asyncio
async def test_cache_mechanism():
    cache = DesignCache.load()
    assert len(cache.designs) > 0
