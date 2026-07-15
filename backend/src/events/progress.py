from src.events.bus import EventBus
import logging

logger = logging.getLogger(__name__)

class GenerationProgressService:
    @staticmethod
    async def emit(project_id: int, stage: str, message: str, status: str = "in_progress"):
        """
        Emits a progress event to the EventBus.
        status can be "in_progress", "completed", "error".
        """
        try:
            await EventBus.publish("generation_progress", {
                "project_id": project_id,
                "stage": stage,
                "message": message,
                "status": status
            })
        except Exception as e:
            logger.error(f"Failed to emit generation progress: {e}")
