import logging
from groq import AsyncGroq
from src.utils.settings import settings
from src.AI.memory.brain import ProjectBrain, WebsitePlan
import json

logger = logging.getLogger(__name__)

async def execute_best_practice_reasoning(brain: ProjectBrain):
    """
    Appends UX/IA best practices to project_facts based on the website category.
    """
    if not brain.website_category or not settings.GROQ_API_KEY:
        return
        
    client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    
    prompt = f"""You are a UX expert. The user is building a '{brain.website_category}' website.
Provide 3 highly specific UX/conversion best practices for this exact type of website.
Return ONLY a JSON object containing a "best_practices" key with an array of strings."""
    
    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        data = json.loads(response.choices[0].message.content)
        facts = data.get("best_practices", [])
        
        for f in facts:
            if f not in brain.memory.project_facts:
                brain.memory.project_facts.append(f)
                
    except Exception as e:
        logger.error(f"Best practice reasoning failed: {e}")

async def execute_micro_planning(brain: ProjectBrain):
    """
    Updates the WebsitePlan progressively based on current facts.
    """
    if not settings.GROQ_API_KEY:
        if not brain.website_plan:
            brain.website_plan = WebsitePlan()
        return

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    schema = WebsitePlan.model_json_schema()
    
    prompt = f"""You are a website architect. Based on the current project brain, output the optimal website architecture.
Current category: {brain.website_category}
Facts & Constraints: {json.dumps(brain.memory.project_facts)} {json.dumps(brain.memory.constraints)}
Explicit Decisions: {json.dumps({k: v.value for k, v in brain.memory.decisions.items() if v.status == 'confirmed'})}

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
        brain.website_plan = WebsitePlan(**data)
    except Exception as e:
        logger.error(f"Micro planning failed: {e}")
        if not brain.website_plan:
            brain.website_plan = WebsitePlan()
