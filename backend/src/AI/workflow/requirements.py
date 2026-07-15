"""
Discovery Requirements
======================
Minimal, smart set of requirements. The agent should ask MAX 2 questions
before moving to generation. Everything else is inferred.
"""
from pydantic import BaseModel, Field
from typing import List


class DiscoveryRequirement(BaseModel):
    id: str
    priority: int
    description: str
    dependencies: List[str] = Field(default_factory=list)
    applicable_categories: List[str] = Field(default_factory=lambda: ["ALL"])


# ─────────────────────────────────────────────────────────────────────────────
# ONLY 3 truly required fields. Everything else (visual style, page structure,
# etc.) is inferred by the AI from context. This prevents the endless loop.
# Priority > 80 = mandatory (blocks generation until answered).
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_REQUIREMENTS = [
    DiscoveryRequirement(
        id="website_category",
        priority=100,
        description=(
            "The type of website: Hospital/Medical, E-commerce/Shop, Restaurant/Food, "
            "SaaS/App, Portfolio/Personal, Agency/Services, Blog/Media, or Other. "
            "Can almost always be inferred from the business name or description."
        ),
    ),
    DiscoveryRequirement(
        id="business_name",
        priority=90,
        description=(
            "The official name of the business, clinic, brand, or project. "
            "Often stated in the first message — look carefully."
        ),
    ),
    # core_features is priority 60 (not mandatory) — we infer it from category
    DiscoveryRequirement(
        id="core_features",
        priority=60,
        description=(
            "Key features the site must have. Infer from business type: "
            "hospital→appointments+doctor profiles+services; "
            "e-commerce→product grid+cart+checkout; "
            "restaurant→menu+reservation+hours; "
            "agency→portfolio+contact+testimonials."
        ),
    ),
]
