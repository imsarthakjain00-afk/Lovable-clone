import logging
import json
from typing import Dict, Any, List
from src.AI.memory.brain import ProjectBrain, DecisionState
from src.utils.settings import settings
from src.AI.llm.provider import get_llm_provider
from src.utils.llm_retry import with_retry, RetryPolicy

logger = logging.getLogger(__name__)

class DiscoveryAnalysisService:
    @classmethod
    @with_retry(RetryPolicy(max_retries=1))
    async def analyze(cls, brain: ProjectBrain) -> ProjectBrain:
        """
        Analyzes the extracted memory to:
        - resolve conflicts
        - merge duplicate answers
        - infer low-risk information
        - calculate confidence
        """
        llm = get_llm_provider()
        
        # Prepare the current state for the LLM
        current_decisions = {
            k: {"value": v.value, "status": v.status, "confidence": v.confidence}
            for k, v in brain.memory.decisions.items()
        }
        
        prompt = f"""You are a senior Business Analyst reviewing a client discovery session.
        
Current Decisions:
{json.dumps(current_decisions, indent=2)}

Project Facts:
{json.dumps(brain.memory.project_facts, indent=2)}

Task:
1. Resolve any conflicting information.
2. Merge duplicate facts.
3. Infer low-risk missing information (e.g., if they are a 'Restaurant', infer typical features like 'Menu', 'Location', 'Hours').
4. Assign a confidence score (0-100) to each decision based on how explicit it was.
5. If you infer something, mark its status as 'inferred' and source as 'ai'.

Return a JSON object with:
- `updated_decisions`: A dictionary mapping keys to objects with `value`, `status`, `confidence`, and `source`.
- `updated_facts`: A clean list of string facts.

Output EXACTLY JSON:"""

        try:
            messages = [{"role": "user", "content": prompt}]
            raw = await llm.complete(messages=messages, max_tokens=2000, temperature=0.1)
            data = json.loads(raw.strip())
            
            updated_decisions = data.get("updated_decisions", {})
            updated_facts = data.get("updated_facts", brain.memory.project_facts)
            
            for k, v in updated_decisions.items():
                if k in brain.memory.decisions:
                    decision = brain.memory.decisions[k]
                    decision.value = v.get("value", decision.value)
                    decision.status = v.get("status", decision.status)
                    decision.confidence = v.get("confidence", decision.confidence)
                    if v.get("source"):
                        decision.source = v.get("source")
                else:
                    brain.memory.decisions[k] = DecisionState(
                        status=v.get("status", "inferred"),
                        value=v.get("value"),
                        confidence=v.get("confidence", 50.0),
                        source=v.get("source", "ai"),
                        reason="Inferred during Discovery Analysis"
                    )
            
            brain.memory.project_facts = updated_facts
            
        except Exception as e:
            logger.error(f"Discovery Analysis failed: {e}")
            
        return brain
