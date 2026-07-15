import logging
import json
from src.AI.memory.brain import ProjectBrain, DesignBrain
from src.utils.settings import settings
from groq import AsyncGroq
from src.utils.llm_retry import with_retry, RetryPolicy

logger = logging.getLogger(__name__)

class DesignAdaptationService:
    @classmethod
    @with_retry(RetryPolicy(max_retries=1))
    async def adapt(cls, brain: ProjectBrain, base_design: DesignBrain, customizations: str = "") -> DesignBrain:
        """
        Adapts the original DesignBrain to the specific industry of the ProjectBrain,
        and optionally applies user-provided customizations.
        """
        if not settings.GROQ_API_KEY:
            return base_design

        client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        schema = DesignBrain.model_json_schema()
        
        industry = brain.website_category or "General"
        facts = brain.memory.project_facts
        
        prompt = f"""You are a senior UI/UX Product Designer.
You have a base design system (DesignBrain) and need to adapt it for a new project in the '{industry}' industry.
Modify the tokens (colors, typography, spacing, border-radius, philosophy) so they perfectly suit this industry while maintaining the core aesthetic of the base design.

Project Facts:
{json.dumps(facts)}

User Customizations / Refinements:
{customizations if customizations else 'None'}

Base DesignBrain:
{base_design.model_dump_json(indent=2)}

Output the fully adapted DesignBrain EXACTLY to this JSON schema:
{json.dumps(schema)}
"""

        try:
            response = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            data = json.loads(response.choices[0].message.content)
            return DesignBrain(**data)
        except Exception as e:
            logger.error(f"Design adaptation failed: {e}")
            return base_design
