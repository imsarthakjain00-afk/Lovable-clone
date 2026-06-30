from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.utils.db import Base, engine

# Import all database models so SQLAlchemy creates the tables on startup
from src.Users.models import UserModel
from src.Projects.models import ProjectModel, ChatMessageModel

# Import all route groups
from src.Users.routers import user_routes
from src.Projects.routers import project_routes
from src.AI.routers import ai_routes
from src.Templates.routers import templates_routes

# Create all database tables if they don't exist yet
Base.metadata.create_all(engine)

app = FastAPI(
    title="Lovable Clone API",
    description=(
        "Backend API for Lovable Clone — an AI-powered website builder. "
        "Users can prompt the AI to generate complete websites, manage their projects, "
        "and view their full chat history."
    ),
    version="1.0.0"
)

# Allow the frontend (running on localhost:5173 in dev) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all route groups
app.include_router(user_routes)
app.include_router(project_routes)
app.include_router(ai_routes)
app.include_router(templates_routes)


@app.get("/", tags=["Health Check"])
def health_check():
    """Simple health check to confirm the API is running."""
    return {"status": "ok", "message": "Lovable Clone API is running."}