import pytest
import asyncio
from src.AI.memory.brain import ProjectBrain
from src.AI.workflow.engine import WorkflowEngine, WorkflowState
from src.AI.workflow.requirements import DEFAULT_REQUIREMENTS
from src.AI.workflow.discovery import evaluate_discovery_state

@pytest.mark.asyncio
async def test_all_of_these_expansion():
    brain = ProjectBrain()
    brain.website_category = "General"
    engine = WorkflowEngine(brain)
    
    # Simulate a vague answer to a feature question
    brain.workflow_stage = WorkflowState.DISCOVERY
    brain, response = await engine.process_user_input("I want all of the features you mentioned: blog, contact form, and testimonials.")
    
    # Verify it got extracted properly
    assert "core_features" in brain.memory.decisions
    extracted = str(brain.memory.decisions["core_features"].value).lower()
    assert "blog" in extracted
    assert "contact form" in extracted
    assert "testimonials" in extracted

@pytest.mark.asyncio
async def test_long_content_extraction():
    brain = ProjectBrain()
    engine = WorkflowEngine(brain)
    
    long_input = """
    We are building a website for Greenfield Hospital. We need a single page architecture.
    We must have doctor profiles, a patient portal login, and a contact form.
    The primary audience is local residents looking for urgent care or pediatrics.
    """
    brain, response = await engine.process_user_input(long_input)
    
    # Should extract multiple decisions
    assert "business_name" in brain.memory.decisions
    assert "Greenfield" in str(brain.memory.decisions["business_name"].value)
    
    assert "page_structure" in brain.memory.decisions
    assert "single" in str(brain.memory.decisions["page_structure"].value).lower()

@pytest.mark.asyncio
async def test_deduplication_and_completion():
    brain = ProjectBrain()
    engine = WorkflowEngine(brain)
    
    # Feed it all required info to see if it finishes naturally
    bulk_input = "We are a SaaS company named TechFlow. We want a multi-page site for developers. We need a tiered pricing page, login, and docs. Minimalist style."
    brain, response = await engine.process_user_input(bulk_input)
    
    # Since all standard fields are satisfied, it should move to DISCOVERY_SUMMARY
    assert brain.workflow_stage == WorkflowState.DISCOVERY_SUMMARY
    assert response.get("type") == "CONFIRMATION"

@pytest.mark.asyncio
async def test_project_isolation():
    brain1 = ProjectBrain()
    engine1 = WorkflowEngine(brain1)
    
    brain2 = ProjectBrain()
    engine2 = WorkflowEngine(brain2)
    
    await engine1.process_user_input("My business is Acme Corp.")
    
    biz1 = brain1.memory.decisions.get("business_name")
    assert biz1 is not None
    assert "Acme" in str(biz1.value)
    
    assert "business_name" not in brain2.memory.decisions

@pytest.mark.asyncio
async def test_conflict_resolution():
    brain = ProjectBrain()
    engine = WorkflowEngine(brain)
    
    # Initial statement
    await engine.process_user_input("I want a single page website for my bakery.")
    assert "single" in str(brain.memory.decisions["page_structure"].value).lower()
    
    # Later statement contradicting the first
    await engine.process_user_input("Actually, let's make it a multi-page website.")
    assert "multi" in str(brain.memory.decisions["page_structure"].value).lower()
    
    # Verify timeline recorded both
    timeline_events = [t for t in brain.memory.timeline if t.field_id == "page_structure"]
    assert len(timeline_events) >= 2

@pytest.mark.asyncio
async def test_entity_extraction():
    brain = ProjectBrain()
    engine = WorkflowEngine(brain)
    
    await engine.process_user_input("You can email us at support@example.com or visit https://example.com.")
    
    facts = brain.memory.project_facts
    assert any("support@example.com" in f for f in facts)
    assert any("https://example.com" in f for f in facts)
