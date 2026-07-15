import asyncio
from src.AI.workflow.engine import WorkflowEngine, WorkflowState
from src.AI.memory.brain import ProjectBrain
from src.AI.catalog.registry import DesignRegistry

async def test():
    DesignRegistry.load()
    brain = ProjectBrain()
    brain.workflow_stage = WorkflowState.DESIGN_SELECTION
    engine = WorkflowEngine(brain)
    b, res = await engine.process_user_input('?')
    print(res)

asyncio.run(test())
