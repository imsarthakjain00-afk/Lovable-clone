from fastapi import APIRouter, status
from typing import List
from pydantic import BaseModel

templates_routes = APIRouter(prefix="/templates", tags=["Website Templates"])


class WebsiteTemplate(BaseModel):
    """Represents a pre-built website template."""
    id: int
    name: str
    description: str
    category: str       # e.g. 'landing', 'portfolio', 'ecommerce'
    preview_emoji: str  # emoji used as a visual preview icon
    starter_prompt: str # the prompt pre-filled when user picks this template


# Static list of templates — can be moved to DB later
AVAILABLE_TEMPLATES: List[WebsiteTemplate] = [
    WebsiteTemplate(
        id=1,
        name="SaaS Landing Page",
        description="A clean, conversion-focused landing page for a software product.",
        category="landing",
        preview_emoji="🚀",
        starter_prompt="Create a modern SaaS landing page with a hero section, features grid, pricing table, and footer."
    ),
    WebsiteTemplate(
        id=2,
        name="Personal Portfolio",
        description="Showcase your work, skills, and experience professionally.",
        category="portfolio",
        preview_emoji="🎨",
        starter_prompt="Create a personal portfolio website with an about section, skills, projects showcase, and contact form."
    ),
    WebsiteTemplate(
        id=3,
        name="Restaurant Website",
        description="A beautiful website for a restaurant with menu and booking.",
        category="business",
        preview_emoji="🍽️",
        starter_prompt="Create a restaurant website with a hero image, menu section, about us, gallery, and reservation form."
    ),
    WebsiteTemplate(
        id=4,
        name="E-Commerce Store",
        description="A product listing page with shopping cart functionality.",
        category="ecommerce",
        preview_emoji="🛍️",
        starter_prompt="Create an e-commerce product listing page with product cards, filters, and a shopping cart sidebar."
    ),
    WebsiteTemplate(
        id=5,
        name="Blog / Magazine",
        description="A clean, readable blog with article cards and categories.",
        category="blog",
        preview_emoji="📝",
        starter_prompt="Create a blog website with a header, featured article, article card grid, sidebar, and newsletter signup."
    ),
    WebsiteTemplate(
        id=6,
        name="Agency Website",
        description="A professional agency site with services and team sections.",
        category="business",
        preview_emoji="💼",
        starter_prompt="Create a digital agency website with services section, case studies, team members, and contact form."
    ),
    WebsiteTemplate(
        id=7,
        name="Event / Conference",
        description="Promote an event with schedule, speakers, and registration.",
        category="event",
        preview_emoji="🎤",
        starter_prompt="Create an event landing page with countdown timer, speaker profiles, schedule, and registration form."
    ),
    WebsiteTemplate(
        id=8,
        name="Startup Homepage",
        description="A bold, eye-catching homepage for a new startup.",
        category="landing",
        preview_emoji="⚡",
        starter_prompt="Create a startup homepage with animated hero, product screenshots, testimonials, and a CTA section."
    ),
]


@templates_routes.get(
    "/",
    response_model=List[WebsiteTemplate],
    status_code=status.HTTP_200_OK,
    summary="Get all available website templates"
)
def get_all_templates():
    """Returns the full list of pre-built website templates."""
    return AVAILABLE_TEMPLATES


@templates_routes.get(
    "/{template_id}",
    response_model=WebsiteTemplate,
    status_code=status.HTTP_200_OK,
    summary="Get a single template by its ID"
)
def get_template_by_id(template_id: int):
    """Returns a single template. Raises 404 if not found."""
    from fastapi import HTTPException
    template = next((t for t in AVAILABLE_TEMPLATES if t.id == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found.")
    return template
