import logging
import json
from src.utils.settings import settings
from groq import AsyncGroq
from src.AI.memory.brain import DesignBrain
from src.utils.llm_retry import with_retry, RetryPolicy

logger = logging.getLogger(__name__)

class DesignRefinementLayer:
    @classmethod
    @with_retry(RetryPolicy(max_retries=1))
    async def refine_design_brain(cls, current_brain: DesignBrain, user_prompt: str) -> DesignBrain:
        """
        Applies a natural language user prompt to tweak a DesignBrain.
        """
        logger.info(f"Refining DesignBrain with prompt: {user_prompt}")
        
        client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        schema = DesignBrain.model_json_schema()
        
        system_prompt = f"""You are a senior design system architect.
The user wants to refine an existing DesignBrain.
Apply their requested changes to the JSON structure.
Preserve the existing structure except where it conflicts with the user's request.

Current DesignBrain:
{current_brain.model_dump_json(indent=2)}

User Request:
{user_prompt}

Output EXACTLY this JSON schema representing the UPDATED DesignBrain:
{json.dumps(schema)}
"""

        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": system_prompt}],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        data = json.loads(response.choices[0].message.content)
        return DesignBrain(**data)
