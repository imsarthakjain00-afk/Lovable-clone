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
from src.AI import pipeline_service

ai_routes = APIRouter(prefix="/ai", tags=["AI Code Generation"])

class DeepBuildRequest(BaseModel):
    project_id: int
    user_prompt: str



class GenerateWebsiteRequest(BaseModel):
    """Request body for generating a website."""
    project_id: int
    user_prompt: str   # What the user wants to build


class GenerateWebsiteResponse(BaseModel):
    """Response body after website generation."""
    response_text: str       # Friendly message from the AI
    generated_code: str      # Full HTML code of the generated website
    user_message_id: int     # ID of the saved user message in DB
    ai_message_id: int       # ID of the saved AI response in DB


def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Dependency: extracts the current logged-in user from the JWT token."""
    return is_authenticated_service(request, db)


@ai_routes.post(
    "/generate",
    response_model=GenerateWebsiteResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a website from a text prompt using AI"
)
def generate_website_from_prompt(
    request_body: GenerateWebsiteRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = project_services.db_queries.get_project_by_id(request_body.project_id, db)
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to generate code for this project."
        )

    saved_user_message = project_services.save_user_message_to_project(
        project_id=request_body.project_id,
        message_text=request_body.user_prompt,
    )

    ai_output = ai_services.generate_website_code(request_body.user_prompt)

    ai_output["generated_code"] = ai_services.inject_supabase_to_html(
        ai_output["generated_code"], request_body.project_id
    )

    saved_ai_message = project_services.save_ai_response_to_project(
        project_id=request_body.project_id,
        ai_response_text=ai_output["response_text"],
        generated_code=ai_output["generated_code"],
    )

    return {
        "response_text": ai_output["response_text"],
        "generated_code": ai_output["generated_code"],
        "user_message_id": saved_user_message.get("id") if isinstance(saved_user_message, dict) else saved_user_message.id,
        "ai_message_id": saved_ai_message.get("id") if isinstance(saved_ai_message, dict) else saved_ai_message.id
    }


@ai_routes.post(
    "/deep-build",
    response_model=GenerateWebsiteResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a website using the deep multi-agent pipeline"
)
async def deep_build_website(
    request_body: DeepBuildRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = project_services.db_queries.get_project_by_id(request_body.project_id, db)
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to generate code for this project."
        )

    saved_user_message = project_services.save_user_message_to_project(
        project_id=request_body.project_id,
        message_text=request_body.user_prompt,
    )

    try:
        generated_html = await pipeline_service.run_deep_build_pipeline(request_body.user_prompt)
        response_text = "Your website has been generated successfully using Deep Build!"
        
        # Inject Supabase
        generated_html = ai_services.inject_supabase_to_html(
            generated_html, request_body.project_id
        )
    except Exception as e:
        generated_html = f"<!-- Error: {str(e)} -->"
        response_text = "There was an error running the Deep Build pipeline."

    saved_ai_message = project_services.save_ai_response_to_project(
        project_id=request_body.project_id,
        ai_response_text=response_text,
        generated_code=generated_html,
    )

    return {
        "response_text": response_text,
        "generated_code": generated_html,
        "user_message_id": saved_user_message.get("id") if isinstance(saved_user_message, dict) else saved_user_message.id,
        "ai_message_id": saved_ai_message.get("id") if isinstance(saved_ai_message, dict) else saved_ai_message.id
    }


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

    try:
        while True:
            # Wait for user prompt
            data = await websocket.receive_json()
            user_prompt = data.get("user_prompt")
            if not user_prompt:
                continue

            saved_user_message = project_services.save_user_message_to_project(
                project_id=project_id, message_text=user_prompt
            )

            await websocket.send_json(
                {
                    "type": "user_message",
                    "message_id": saved_user_message.id,
                    "message_text": user_prompt,
                }
            )

            full_response = ""
            async_gen = ai_services.generate_website_code_stream(user_prompt)

            for chunk in async_gen:
                full_response += chunk
                await websocket.send_json({"type": "chunk", "text": chunk})

            raw_output = full_response.strip()
            generated_html_code = raw_output
            html_start_idx = generated_html_code.find("<!DOCTYPE html>")
            if html_start_idx == -1:
                html_start_idx = generated_html_code.find("<html")

            if html_start_idx != -1:
                response_text = generated_html_code[:html_start_idx].strip()
                generated_html_code = generated_html_code[html_start_idx:].strip()
            else:
                response_text = "Here is your generated website."

            if generated_html_code.startswith("```html"):
                generated_html_code = generated_html_code[7:]
            if generated_html_code.startswith("```"):
                generated_html_code = generated_html_code[3:]
            if generated_html_code.endswith("```"):
                generated_html_code = generated_html_code[:-3]
            generated_html_code = generated_html_code.strip()

            generated_html_code = ai_services.inject_supabase_to_html(
                generated_html_code, project_id
            )

            if not response_text:
                response_text = "Your website has been generated successfully!"

            saved_ai_message = project_services.save_ai_response_to_project(
                project_id=project_id,
                ai_response_text=response_text,
                generated_code=generated_html_code,
            )

            await websocket.send_json(
                {
                    "type": "completed",
                    "response_text": response_text,
                    "generated_code": generated_html_code,
                    "user_message_id": saved_user_message.get("id") if isinstance(saved_user_message, dict) else saved_user_message.id,
                    "ai_message_id": saved_ai_message.get("id") if isinstance(saved_ai_message, dict) else saved_ai_message.id,
                }
            )

    except WebSocketDisconnect:
        pass
