import logging
import json
from src.AI.memory.brain import DesignBrain
from src.AI.memory.tokens import DesignTokens
from src.utils.llm_retry import with_retry, RetryPolicy
from src.AI.llm.provider import get_llm_provider

logger = logging.getLogger(__name__)


class DesignTokenizer:
    @classmethod
    @with_retry(RetryPolicy(max_retries=1))
    async def generate_tokens(cls, brain: DesignBrain) -> DesignTokens:
        """
        Translates a parsed DesignBrain into concrete DesignTokens (CSS scales).
        Uses the configured LLM provider.
        """
        if brain is None:
            logger.warning("DesignBrain is None — returning default DesignTokens")
            return DesignTokens()
            
        logger.info("Generating DesignTokens from DesignBrain")
        
        llm = get_llm_provider()
        schema = DesignTokens.model_json_schema()
        
        prompt = f"""You are a design system engineer.
Translate the following strategic DesignBrain into concrete CSS DesignTokens.
Provide explicit hex values, rem sizes, and spacing strings.

DesignBrain Content:
{brain.model_dump_json(indent=2)}

Output EXACTLY this JSON schema (no extra text, just valid JSON):
{json.dumps(schema)}
"""

        text = await llm.complete(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.1
        )
        
        # Extract JSON from response
        text = text.strip()
        if "```" in text:
            import re
            match = re.search(r'```(?:json)?\s*([\s\S]+?)\s*```', text)
            if match:
                text = match.group(1)
        
        try:
            data = json.loads(text)
            return DesignTokens(**data)
        except Exception as e:
            logger.error(f"Failed to parse DesignTokens JSON: {e}. Raw: {text[:200]}")
            return DesignTokens()
