import json
import logging
from typing import Dict, Any
from src.AI.workflow.engine import WorkflowEngine, WorkflowState
from src.AI.memory.brain import ProjectBrain
from src.AI.orchestrator.intent import IntentExtractionService

logger = logging.getLogger(__name__)

class WebsiteCreationAgent:
    def __init__(self, project_id: int, initial_state: str = "DISCOVERY", initial_brain: dict = None, initial_manifest: dict = None):
        self.project_id = project_id
        
        try:
            self.brain = ProjectBrain(**(initial_brain or {}))
        except Exception as e:
            logger.warning(f"Failed to parse ProjectBrain, starting fresh. {e}")
            self.brain = ProjectBrain()
            
        self.brain.workflow_stage = initial_state
        self.engine = WorkflowEngine(self.brain)

    async def process_message(self, user_message: str, current_code: str = None) -> dict:
        """
        Conversation Orchestrator entry point.
        Step 1: Intent Extraction (updates brain directly from message).
        Step 2: Workflow Engine (state machine + requirement evaluation).
        """
        # ── Step 1: Intent Extraction ──────────────────────────────
        # Always extract before routing so ProjectBrain is up-to-date.
        # This is the fix for "agent forgets context" bug.
        try:
            self.brain = await IntentExtractionService.extract_and_update(user_message, self.brain)
        except Exception as e:
            logger.warning(f"[Agent] Intent extraction non-fatal error: {e}")

        # ── Step 2: Workflow Engine ────────────────────────────────
        updated_brain, response_data = await self.engine.process_user_input(user_message)
        self.brain = updated_brain
        
        interaction_type = response_data.get("type", "SYSTEM")
        
        return {
            "message": response_data.get("text", ""),
            "interaction_type": interaction_type,
            "workflow_state": self.brain.workflow_stage,
            "project_brain": self.brain.model_dump(),
            "extra_data": response_data
        }
