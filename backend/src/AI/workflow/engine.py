"""
Workflow Engine — Strict 7-Step Conversation Flow

States (in order):
  GREETING            → Auto-sent on first project open. No user input yet.
  AWAITING_DESCRIPTION → User has been greeted, waiting for them to describe what they want.
  AWAITING_PAGE_TYPE   → Agent understood the idea, now asking single vs multi-page.
  ARCHITECTURE_PLANNING → Running silently in background, streaming progress to chat.
  DESIGN_SELECTION     → Showing top 5 designs matched to the project.
  PRD_REVIEW           → Showing PRD summary, awaiting user confirmation.
  GENERATION_PIPELINE  → Website is being generated.
  COMPLETE             → Website is live, showing view/deploy options.
"""
import logging
import json
from typing import Dict, Any, Tuple

from src.AI.memory.brain import ProjectBrain
from src.AI.llm.provider import get_llm_provider
from src.utils.llm_retry import with_retry, RetryPolicy

logger = logging.getLogger(__name__)


class WorkflowState:
    GREETING = "GREETING"
    AWAITING_DESCRIPTION = "AWAITING_DESCRIPTION"
    AWAITING_PAGE_TYPE = "AWAITING_PAGE_TYPE"
    ARCHITECTURE_PLANNING = "ARCHITECTURE_PLANNING"
    DESIGN_SELECTION = "DESIGN_SELECTION"
    PRD_REVIEW = "PRD_REVIEW"
    GENERATION_PIPELINE = "GENERATION_PIPELINE"
    COMPLETE = "COMPLETE"

    # Legacy aliases kept so existing DB rows don't break on load
    DISCOVERY = "AWAITING_DESCRIPTION"
    DISCOVERY_ANALYSIS = "AWAITING_DESCRIPTION"
    DISCOVERY_SUMMARY = "PRD_REVIEW"
    WEBSITE_BLUEPRINT = "ARCHITECTURE_PLANNING"
    DESIGN_RECOMMENDATION = "DESIGN_SELECTION"
    DESIGN_ADAPTATION = "DESIGN_SELECTION"
    DESIGN_CUSTOMIZATION = "DESIGN_SELECTION"
    FINAL_PROJECT_REVIEW = "PRD_REVIEW"
    FINAL_CONFIRMATION = "PRD_REVIEW"
    QUALITY_REVIEW = "COMPLETE"

    @classmethod
    def normalize(cls, raw_state: str) -> str:
        """Maps any legacy state string to the current canonical state."""
        legacy_map = {
            "DISCOVERY": cls.AWAITING_DESCRIPTION,
            "DISCOVERY_ANALYSIS": cls.AWAITING_DESCRIPTION,
            "DISCOVERY_SUMMARY": cls.PRD_REVIEW,
            "WEBSITE_BLUEPRINT": cls.ARCHITECTURE_PLANNING,
            "DESIGN_RECOMMENDATION": cls.DESIGN_SELECTION,
            "DESIGN_ADAPTATION": cls.DESIGN_SELECTION,
            "DESIGN_CUSTOMIZATION": cls.DESIGN_SELECTION,
            "FINAL_PROJECT_REVIEW": cls.PRD_REVIEW,
            "FINAL_CONFIRMATION": cls.PRD_REVIEW,
            "QUALITY_REVIEW": cls.COMPLETE,
        }
        return legacy_map.get(raw_state, raw_state)


class WorkflowEngine:
    def __init__(self, brain: ProjectBrain):
        self.brain = brain
        # Normalize legacy states from DB on load
        self.brain.workflow_stage = WorkflowState.normalize(self.brain.workflow_stage)

    async def process_user_input(self, user_message: str) -> Tuple[ProjectBrain, Dict[str, Any]]:
        lower = user_message.lower().strip()

        # ── Handle system commands from UI buttons ────────────────────────────
        if lower.startswith("[sys:select_design]"):
            design_id = user_message.replace("[sys:select_design]", "").strip()
            self.brain.design_id = design_id
            self.brain.workflow_stage = WorkflowState.PRD_REVIEW
            return self.brain, await self._handle_prd_review()

        if lower.startswith("[sys:confirm_build]"):
            self.brain.workflow_stage = WorkflowState.GENERATION_PIPELINE
            return self.brain, self._handle_generation_start()

        if lower.startswith("[sys:save_deployed_url]"):
            url = user_message.replace("[sys:save_deployed_url]", "").strip()
            self.brain.memory.project_facts.append(f"deployed_url:{url}")
            return self.brain, {
                "type": "DEPLOY_CONFIRMED",
                "text": f"🚀 Your website is live at [{url}]({url})\n\nThis link has been saved to your project. You can always find it in your **Deployed Sites** section."
            }

        # ── Route by current state ────────────────────────────────────────────
        state = self.brain.workflow_stage

        if state == WorkflowState.GREETING:
            # First user message after greeting — store what they said and move forward
            self.brain.memory.project_facts.append(f"user_idea: {user_message}")
            self.brain.workflow_stage = WorkflowState.AWAITING_PAGE_TYPE
            return self.brain, await self._acknowledge_and_ask_page_type(user_message)

        if state == WorkflowState.AWAITING_DESCRIPTION:
            self.brain.memory.project_facts.append(f"user_idea: {user_message}")
            self.brain.workflow_stage = WorkflowState.AWAITING_PAGE_TYPE
            return self.brain, await self._acknowledge_and_ask_page_type(user_message)

        if state == WorkflowState.AWAITING_PAGE_TYPE:
            page_type = self._parse_page_type(lower)
            self.brain.memory.decisions["page_structure"] = _make_decision(page_type, "confirmed")
            self.brain.memory.project_facts.append(f"page_type: {page_type}")
            self.brain.workflow_stage = WorkflowState.ARCHITECTURE_PLANNING
            return self.brain, await self._run_architecture_planning()

        if state == WorkflowState.ARCHITECTURE_PLANNING:
            # Architecture is running — user shouldn't be here, but push forward
            return self.brain, {
                "type": "PROGRESS",
                "text": "Still planning the architecture — hang tight for a moment! ⚡"
            }

        # Legacy states — skip straight to generation if encountered
        if state in (WorkflowState.DESIGN_SELECTION, WorkflowState.PRD_REVIEW):
            self.brain.workflow_stage = WorkflowState.GENERATION_PIPELINE
            return self.brain, self._handle_generation_start()

        if state == WorkflowState.GENERATION_PIPELINE:
            return self.brain, self._handle_generation_start()

        if state == WorkflowState.COMPLETE:
            return self.brain, {
                "type": "COMPLETE",
                "text": "Your website is already live in the preview panel! Click **Publish** in the top bar to deploy it to the web. 🚀"
            }

        # Fallback for any unknown state
        self.brain.workflow_stage = WorkflowState.AWAITING_DESCRIPTION
        return self.brain, {
            "type": "QUESTION",
            "text": "What would you like to build today?"
        }

    # ── State handlers ─────────────────────────────────────────────────────────

    @staticmethod
    def build_greeting(username: str) -> Dict[str, Any]:
        """Returns the auto-greeting sent as soon as a project is opened."""
        first_name = username.split("_")[0].capitalize() if "_" in username else username.capitalize()
        return {
            "type": "GREETING",
            "text": f"Hey, {first_name}! What do you wanna build today?\nLet's build some crazy websites 🚀"
        }

    @with_retry(RetryPolicy(max_retries=1))
    async def _acknowledge_and_ask_page_type(self, user_idea: str) -> Dict[str, Any]:
        llm = get_llm_provider()

        prompt = f"""The user wants to build: "{user_idea}"

Write a single short response that:
1. Acknowledges what they want to build in 1 sentence (mention the specific thing they described).
2. Immediately asks: would they like a **multi-page** or **single-page** website?

Explain briefly:
- Multi-page: different sections (About, Contact, etc.) are on separate pages — great for larger sites.
- Single-page: all sections scroll on one page — great for landing pages and portfolios.

Rules:
- Do NOT say "Great!", "Awesome!", "Sure!" or any hollow filler.
- Keep it under 5 sentences total.
- Sound like a professional product designer, not a chatbot.

Response:"""

        text = await llm.complete(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.4
        )
        return {
            "type": "QUESTION",
            "text": text.strip(),
            "chips": ["Single-page website", "Multi-page website"]
        }

    def _parse_page_type(self, lower_msg: str) -> str:
        if any(w in lower_msg for w in ["multi", "multiple", "several", "many page"]):
            return "multi-page"
        return "single-page"

    @with_retry(RetryPolicy(max_retries=1))
    async def _run_architecture_planning(self) -> Dict[str, Any]:
        """Plans the architecture silently, auto-selects a design, then starts generation immediately."""
        user_idea = next(
            (f.replace("user_idea: ", "") for f in self.brain.memory.project_facts if f.startswith("user_idea:")),
            "a website"
        )
        page_type = self.brain.memory.decisions.get("page_structure")
        page_type_val = page_type.value if page_type else "single-page"

        llm = get_llm_provider()

        arch_prompt = f"""You are a senior frontend architect.

Plan a {page_type_val} website for: "{user_idea}"

Output a JSON object with these keys:
- "sections": array of section names in order
- "pages": array of page names (for multi-page) or ["Home"] for single-page
- "nav_items": array of navigation link labels
- "key_features": array of 3-5 must-have features specific to this type of project
- "website_category": one word category (e.g. "hospital", "restaurant", "portfolio", "saas", "ecommerce")

Output ONLY valid JSON."""

        try:
            raw = await llm.complete(
                messages=[{"role": "user", "content": arch_prompt}],
                max_tokens=600,
                temperature=0.2
            )
            import re
            match = re.search(r'(\{.*\})', raw, re.DOTALL)
            if match:
                arch_data = json.loads(match.group(1))
                self.brain.memory.project_facts.append(f"architecture:{json.dumps(arch_data)}")
                if arch_data.get("website_category"):
                    self.brain.website_category = arch_data["website_category"]
        except Exception as e:
            logger.warning(f"[ARCHITECTURE_PLANNING] Non-fatal: {e}")

        # Auto-select a sensible default design and skip user selection entirely
        try:
            from src.AI.catalog.service import DesignCatalogService
            from src.AI.catalog.adaptation import DesignAdaptationService
            recs = await DesignCatalogService.get_recommendations(self.brain)
            if recs:
                self.brain.design_id = recs[0].get("id") or recs[0].get("design_id", "external_apple")
            else:
                self.brain.design_id = "external_apple"
            base_brain, _ = await DesignCatalogService.process_selection(self.brain.design_id)
            adapted = await DesignAdaptationService.adapt(self.brain, base_brain)
            self.brain.design = adapted
        except Exception as e:
            logger.warning(f"[ARCHITECTURE_PLANNING] Auto-design selection non-fatal: {e}")
            self.brain.design_id = "external_apple"

        # Skip directly to generation
        self.brain.workflow_stage = WorkflowState.GENERATION_PIPELINE
        return self._handle_generation_start()

    @with_retry(RetryPolicy(max_retries=1))
    async def _show_design_options(self) -> Dict[str, Any]:
        from src.AI.catalog.service import DesignCatalogService
        from src.AI.catalog.formatter import RecommendationFormatter

        recs = await DesignCatalogService.get_recommendations(self.brain)
        formatted_recs = RecommendationFormatter.format_for_frontend(recs)

        return {
            "type": "DESIGN_SELECTION",
            "text": "Here are the top 5 designs that match your project. Pick the one that fits your vision best 👇",
            "recommendations": formatted_recs
        }

    async def _handle_prd_review(self) -> Dict[str, Any]:
        from src.AI.catalog.service import DesignCatalogService
        from src.AI.catalog.adaptation import DesignAdaptationService

        # Load and adapt the selected design
        try:
            base_brain, _ = await DesignCatalogService.process_selection(self.brain.design_id)
            adapted = await DesignAdaptationService.adapt(self.brain, base_brain)
            self.brain.design = adapted
        except Exception as e:
            logger.warning(f"[PRD_REVIEW] Design adaptation non-fatal: {e}")

        prd_text = self._build_prd()
        return {
            "type": "REVIEW",
            "text": prd_text,
            "chips": ["Yes, build it! 🚀", "Change design"]
        }

    def _build_prd(self) -> str:
        user_idea = next(
            (f.replace("user_idea: ", "") for f in self.brain.memory.project_facts if f.startswith("user_idea:")),
            "your project"
        )
        page_type = self.brain.memory.decisions.get("page_structure")
        page_type_val = page_type.value if page_type else "single-page"

        arch_str = ""
        for fact in self.brain.memory.project_facts:
            if fact.startswith("architecture:"):
                try:
                    arch_data = json.loads(fact.replace("architecture:", ""))
                    sections = ", ".join(arch_data.get("sections", []))
                    features = "\n".join([f"  - {f}" for f in arch_data.get("key_features", [])])
                    arch_str = f"\n**Sections:** {sections}\n\n**Key Features:**\n{features}"
                except Exception:
                    pass

        design_name = self.brain.design_id or "Selected Design"

        return f"""## 📋 Project Details

**Project:** {user_idea}
**Type:** {page_type_val.capitalize()} website
**Design:** {design_name}{arch_str}

---

Shall I start building the website? 🚀"""

    def _handle_generation_start(self) -> Dict[str, Any]:
        return {
            "type": "GENERATING",
            "text": "⚡ Building your website — this usually takes 30–60 seconds. Your live preview will appear on the right as it streams in."
        }


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_decision(value: Any, status: str = "confirmed"):
    """Creates a simple DecisionState-compatible dict for brain.memory.decisions."""
    from src.AI.memory.brain import DecisionState
    return DecisionState(status=status, value=value, confidence=1.0, source="user")


from typing import Any
