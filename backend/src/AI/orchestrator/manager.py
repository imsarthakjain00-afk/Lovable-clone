"""
Conversation Orchestrator

The main entry point for conversational interaction. 
Acts as a state machine / orchestrator for Intent -> Memory -> Workflow -> Generation.
"""
import logging
from typing import Dict, Any, Tuple
from pydantic import BaseModel, Field
from src.AI.memory.brain import ProjectBrain
from src.AI.workflow.engine import WorkflowEngine

logger = logging.getLogger(__name__)

class ConversationState(BaseModel):
    conversation_id: str
    project_id: str
    active_requirement: str = None
    pending_questions: list[str] = Field(default_factory=list)
    answered_requirements: list[str] = Field(default_factory=list)
    confirmation_state: str = "pending"  # pending, ready_for_summary, user_approved
    conversation_summary: str = ""
    reasoning_trace: list[str] = Field(default_factory=list)
    
class ConversationOrchestrator:
    def __init__(self, brain: ProjectBrain, conversation_state: ConversationState = None):
        self.brain = brain
        self.state = conversation_state or ConversationState(
            conversation_id=str(brain.project_id),
            project_id=str(brain.project_id)
        )
        self.workflow_engine = WorkflowEngine(self.brain)

    async def process_message(self, user_message: str) -> Tuple[ProjectBrain, Dict[str, Any]]:
        """
        Main orchestration loop inspired by LangGraph concepts.
        Routes the message through distinct stages.
        """
        # Step 1: Intent Extraction (Updates ProjectBrain directly)
        # TODO: Implement IntentExtractionService
        
        # Step 2: Memory Resolution
        # TODO: Implement RequirementResolver
        
        # Step 3: Question Planner (Bundle requirements)
        # TODO: Implement QuestionPlanner
        
        # Step 4: Fallback to existing WorkflowEngine for now
        # We will gradually intercept stages here.
        updated_brain, response = await self.workflow_engine.process_user_input(user_message)
        self.brain = updated_brain
        
        return self.brain, response
