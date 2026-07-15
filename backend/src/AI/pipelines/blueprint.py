import logging
import json
from typing import Dict, Any
from src.AI.memory.brain import ProjectBrain, WebsiteBlueprint
from src.utils.settings import settings
from groq import AsyncGroq
from src.utils.llm_retry import with_retry, RetryPolicy

logger = logging.getLogger(__name__)

class BlueprintService:
    @classmethod
    @with_retry(RetryPolicy(max_retries=1))
    async def build(cls, brain: ProjectBrain) -> ProjectBrain:
        """
        Generates the logical WebsiteBlueprint based on the project brain.
        """
        if not settings.GROQ_API_KEY:
            if not brain.blueprint:
                brain.blueprint = WebsiteBlueprint()
            return brain

        client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        schema = WebsiteBlueprint.model_json_schema()
        
        decisions = {k: v.value for k, v in brain.memory.decisions.items() if v.status in ['confirmed', 'inferred']}
        
        prompt = f"""You are a senior Solution Architect. Based on the client's discovery summary, generate the complete logical Website Blueprint.
This is the logical architecture, not code.

Current category: {brain.website_category}
Decisions: {json.dumps(decisions, indent=2)}
Facts: {json.dumps(brain.memory.project_facts, indent=2)}

Output exactly to this JSON schema:
{json.dumps(schema)}
"""

        try:
            response = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            data = json.loads(response.choices[0].message.content)
            brain.blueprint = WebsiteBlueprint(**data)
        except Exception as e:
            logger.error(f"Blueprint generation failed: {e}")
            if not brain.blueprint:
                brain.blueprint = WebsiteBlueprint()
                
        return brain
