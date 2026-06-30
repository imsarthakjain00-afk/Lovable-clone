from fastapi import APIRouter, Depends, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.AI import services as ai_services
from src.Projects import services as project_services
from src.utils.db import get_db
from src.Users.services import is_authenticated_service

ai_routes = APIRouter(prefix="/ai", tags=["AI Code Generation"])


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
    """
    Accepts a user's text prompt, calls the AI to generate a full website,
    saves both the user's message and AI response to the project chat history,
    and returns the generated HTML code.
    """
    # Step 1: Save the user's message to the project's chat history
    saved_user_message = project_services.save_user_message_to_project(
        project_id=request_body.project_id,
        message_text=request_body.user_prompt,
        db=db
    )

    # Step 2: Call AI service to generate the website code
    ai_output = ai_services.generate_website_code(request_body.user_prompt)

    # Step 3: Save the AI's response to the project's chat history
    saved_ai_message = project_services.save_ai_response_to_project(
        project_id=request_body.project_id,
        ai_response_text=ai_output["response_text"],
        generated_code=ai_output["generated_code"],
        db=db
    )

    return {
        "response_text": ai_output["response_text"],
        "generated_code": ai_output["generated_code"],
        "user_message_id": saved_user_message.id,
        "ai_message_id": saved_ai_message.id
    }
