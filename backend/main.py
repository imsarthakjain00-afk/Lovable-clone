from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.utils.db import Base, engine
from src.utils.settings import settings

# Import all database models so SQLAlchemy creates the tables on startup
from src.Users.models import UserModel
from src.Projects.models import ProjectModel

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

# Parse CORS origins from comma-separated string
cors_origins = [
    origin.strip().rstrip('/') 
    for origin in settings.CORS_ALLOWED_ORIGINS.split(",") 
    if origin.strip()
]

# Ensure localhost is always allowed for local development
if "http://localhost:5173" not in cors_origins:
    cors_origins.append("http://localhost:5173")

if "*" in cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,  # Must be False when origins="*"
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
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