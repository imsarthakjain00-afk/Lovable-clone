from fastapi import APIRouter, Depends, HTTPException, status, Request, WebSocket, WebSocketDisconnect
import jwt
from jwt.exceptions import InvalidTokenError
from src.utils.settings import settings
from src.Users.db_queries import get_user_by_id
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.AI import services as ai_services
from src.Projects import services as project_services
from src.utils.db import get_db
from src.Users.services import is_authenticated_service
ai_routes = APIRouter(prefix="/ai", tags=["AI Code Generation"])

class DeepBuildRequest(BaseModel):
    project_id: int
    user_prompt: str
    images: list = []


class GenerateWebsiteRequest(BaseModel):
    """Request body for generating a website."""
    project_id: int
    user_prompt: str   # What the user wants to build
    images: list = []


class GenerateWebsiteResponse(BaseModel):
    """Response body after website generation."""
    response_text: str       # Friendly message from the AI
    generated_code: str      # Full HTML code of the generated website
    user_message_id: int     # ID of the saved user message in DB
    ai_message_id: int       # ID of the saved AI response in DB


def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Dependency: extracts the current logged-in user from the JWT token."""
    return is_authenticated_service(request, db)

def authenticate_websocket(token: str, db: Session):
    try:
        data = jwt.decode(token, settings.SECRET_KEY, settings.ALGORITHM)
        user_id = data.get("_id")
        user = get_user_by_id(user_id, db)
        return user
    except InvalidTokenError:
        return None


@ai_routes.websocket("/ws/{project_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: int,
    token: str = None,
    db: Session = Depends(get_db),
):
    import asyncio
    import time
    from src.events.bus import EventBus
    import logging
    
    logger = logging.getLogger("websocket")
    
    await websocket.accept()

    if not token:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Token is required"
        )
        return

    current_user = authenticate_websocket(token, db)
    if not current_user:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token"
        )
        return

    # Check if project belongs to user
    project = project_services.db_queries.get_project_by_id(project_id, db)
    if not project or project.user_id != current_user.id:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Unauthorized project access",
        )
        return
        
    async def event_handler(payload):
        if payload.get("project_id") == project_id:
            try:
                await websocket.send_json({"type": "pipeline_event", "data": payload})
            except Exception as e:
                logger.error(f"[WS_EVENT_ERROR] Failed to send event: {e}")

    subscribed = False
    try:
        for event in ["generation_progress", "build_validation_started", "quality_review_started", "quality_review_completed", "edit_started", "code_chunk", "generation_complete", "generation_failed"]:
            EventBus.subscribe(event, event_handler)
        subscribed = True

        # ── Auto-send greeting if this is the first time the project is opened ──
        from src.AI.workflow.engine import WorkflowState, WorkflowEngine
        if project.workflow_state in (WorkflowState.GREETING, "GREETING"):
            username = current_user.username or current_user.name or "there"
            greeting = WorkflowEngine.build_greeting(username)
            saved_greeting = project_services.save_ai_response_to_project(
                project_id=project_id,
                ai_response_text=greeting["text"],
                generated_code=None,
            )
            await websocket.send_json({
                "type": "completed",
                "response_text": greeting["text"],
                "interaction_type": greeting["type"],
                "workflow_state": WorkflowState.AWAITING_DESCRIPTION,
                "options": greeting.get("chips", []),
                "extra_data": {},
                "ai_message_id": saved_greeting.get("id") if isinstance(saved_greeting, dict) else saved_greeting.id,
                "user_message_id": None,
            })
            # Advance state in DB so next message hits AWAITING_DESCRIPTION
            project_services.db_queries.update_project_state(
                project_id=project_id,
                workflow_state=WorkflowState.AWAITING_DESCRIPTION,
                project_brain=project.project_brain or {},
                file_manifest=project.file_manifest or {},
                db=db,
            )

        while True:
            # Wait for user prompt
            data = await websocket.receive_json()
            user_prompt = data.get("user_prompt")
            current_code = data.get("current_code") # Optional, provided if editing
            images = data.get("images", [])  # [{name, dataUrl, type}]
            if not user_prompt and not images:
                continue
            if not user_prompt:
                user_prompt = "Use the attached images to build a website."
                
            start_time = time.time()
            logger.info(f"[STAGE: REQUEST_RECEIVED] User message received for project {project_id}")

            saved_user_message = project_services.save_user_message_to_project(
                project_id=project_id, message_text=user_prompt
            )

            await websocket.send_json(
                {
                    "type": "user_message",
                    "message_id": saved_user_message.get("id") if isinstance(saved_user_message, dict) else saved_user_message.id,
                    "message_text": user_prompt,
                }
            )
            
            # Reload project to ensure we have the latest state
            project = project_services.db_queries.get_project_by_id(project_id, db)
            logger.info(f"[STAGE: PROJECT_LOADED] Project {project_id} loaded. Current state: {project.workflow_state}")

            try:
                # Wrap AI service processing in a timeout (e.g. 10 minutes max for generation)
                logger.info(f"[STAGE: PIPELINE_STARTED] Starting workflow pipeline for project {project_id}")
                
                response_data = await asyncio.wait_for(
                    ai_services.process_user_prompt(
                        project_id=project_id,
                        user_prompt=user_prompt,
                        current_state=project.workflow_state,
                        current_brain=project.project_brain or {},
                        current_manifest=project.file_manifest or {},
                        current_code=current_code,
                        images=images,
                    ),
                    timeout=600.0  # 10 minutes
                )
                
                logger.info(f"[STAGE: PIPELINE_FINISHED] Workflow pipeline finished for project {project_id}. Duration: {time.time() - start_time:.2f}s")

                response_text = response_data.get("message", "Processing complete.")
                generated_html_code = response_data.get("generated_code")
                new_state = response_data.get("workflow_state", project.workflow_state)
                new_brain = response_data.get("project_brain", project.project_brain)
                new_manifest = response_data.get("file_manifest", project.file_manifest)
                interaction_type = response_data.get("interaction_type", "COMPLETION")
                options = response_data.get("options", [])

                project_services.db_queries.update_project_state(
                    project_id=project_id,
                    workflow_state=new_state,
                    project_brain=new_brain,
                    file_manifest=new_manifest,
                    db=db
                )

                saved_ai_message = project_services.save_ai_response_to_project(
                    project_id=project_id,
                    ai_response_text=response_text,
                    generated_code=generated_html_code,
                )
                
                logger.info(f"[STAGE: WORKFLOW_COMPLETED] Sending completion to UI for project {project_id}")
                
                extra_data = response_data.get("extra_data", {})
                
                await websocket.send_json(
                    {
                        "type": "completed",
                        "response_text": response_text,
                        "generated_code": generated_html_code,
                        "interaction_type": interaction_type,
                        "workflow_state": new_state,
                        "options": options,
                        "extra_data": extra_data,
                        "user_message_id": saved_user_message.get("id") if isinstance(saved_user_message, dict) else saved_user_message.id,
                        "ai_message_id": saved_ai_message.get("id") if isinstance(saved_ai_message, dict) else saved_ai_message.id,
                    }
                )
                
                if interaction_type == "GENERATING":
                    from src.AI.pipelines.generation import execute_generation_pipeline
                    from src.AI.catalog.tokenizer import DesignTokenizer
                    from src.AI.memory.brain import ProjectBrain, DesignBrain
                    from src.AI.memory.tokens import DesignTokens
                    
                    async def run_pipeline():
                        try:
                            # Reconstruct brain
                            brain_obj = ProjectBrain(**new_brain)
                            
                            # Guard: use adapted design or a sensible default
                            design_brain_obj = brain_obj.design or DesignBrain(
                                typography={"heading": "Inter, sans-serif", "body": "Inter, sans-serif"},
                                color_tokens={"primary": "#6366f1", "background": "#0f0f0f", "text": "#ffffff"},
                                border_radius="0.75rem",
                                spacing="8px base",
                                grid_system="12-column",
                                desktop_strategy="full-width sections with max-width 1280px",
                                mobile_strategy="stacked single-column layout",
                                interaction_philosophy="smooth hover transitions and subtle animations",
                            )
                            
                            # Generate design tokens (skip if design_brain is minimal)
                            try:
                                tokens = await DesignTokenizer.generate_tokens(design_brain_obj)
                            except Exception as tok_err:
                                logger.warning(f"DesignTokenizer failed, using empty tokens: {tok_err}")
                                tokens = DesignTokens()
                            
                            # Run generation pipeline, pass db so HTML is persisted
                            await execute_generation_pipeline(
                                brain_obj, design_brain_obj, tokens,
                                project_id=project_id, db=db,
                                user_prompt=user_prompt, current_code=current_code,
                                images=images,
                            )
                        except Exception as e:
                            logger.error(f"Background generation failed: {e}", exc_info=True)
                            await EventBus.publish("generation_failed", {
                                "project_id": project_id,
                                "type": "generation_failed",
                                "error": str(e)
                            })
                            
                    asyncio.create_task(run_pipeline())
            
            except asyncio.TimeoutError:
                logger.error(f"[STAGE: TIMEOUT] Pipeline timed out after 600s for project {project_id}")
                await websocket.send_json({
                    "type": "generation_timeout",
                    "error": "The generation process took too long and was aborted."
                })
            
            except Exception as e:
                logger.error(f"[STAGE: FAILED] Pipeline exception for project {project_id}: {str(e)}", exc_info=True)
                await websocket.send_json({
                    "type": "generation_failed",
                    "error": str(e)
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for project {project_id}")
    finally:
        if subscribed:
            for event in ["generation_progress", "build_validation_started", "quality_review_started", "quality_review_completed", "edit_started", "code_chunk", "generation_complete", "generation_failed"]:
                EventBus.unsubscribe(event, event_handler)
