import logging
import os
import json
from src.utils.settings import settings
from groq import AsyncGroq
from src.AI.memory.brain import DesignBrain
from src.AI.catalog.schemas import DesignMetadata
from src.utils.llm_retry import with_retry, RetryPolicy

logger = logging.getLogger(__name__)

class DesignParser:
    @classmethod
    @with_retry(RetryPolicy(max_retries=1))
    async def parse_to_brain(cls, design: DesignMetadata) -> DesignBrain:
        logger.info(f"Parsing DESIGN.md for {design.id}")
        
        if not os.path.exists(design.relative_path):
            raise FileNotFoundError(f"DESIGN.md not found at {design.relative_path}")
            
        with open(design.relative_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()
            
        client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        schema = DesignBrain.model_json_schema()
        
        prompt = f"""You are a senior design system architect.
Translate the following DESIGN.md into our internal DesignBrain schema.
Infer granular decisions if the markdown is vague.

Markdown Content:
{markdown_content}

Output EXACTLY this JSON schema:
{json.dumps(schema)}
"""

        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        data = json.loads(response.choices[0].message.content)
        return DesignBrain(**data)
