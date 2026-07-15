"""
Intent Extraction Service

Responsible for extracting rich metadata from user messages 
and deterministically updating the ProjectBrain without asking questions.
"""
from typing import Dict, Any, List
import json
import re
import logging
from src.AI.llm.provider import get_llm_provider
from src.AI.memory.brain import ProjectBrain, DecisionState, DecisionEvent

logger = logging.getLogger(__name__)

class IntentExtractionService:
    @classmethod
    async def extract_and_update(cls, user_message: str, brain: ProjectBrain) -> ProjectBrain:
        """
        Parses the incoming message for any relevant data and updates the brain inline.
        """
        if not user_message.strip():
            return brain
            
        llm = get_llm_provider()
        
        # We explicitly list all potential fields we care about
        # to ensure the LLM maps them into these keys.
        expected_fields = [
            "business_name", "website_category", "target_audience", "page_structure",
            "core_features", "visual_style", "color_palette", "typography", 
            "reference_links", "contact_info"
        ]
        
        sys_prompt = f"""You are an elite AI Product Manager parsing user input.
Your goal is to extract structured requirements from the user's message.

AVAILABLE FIELDS:
{json.dumps(expected_fields)}

RULES:
1. Extract any field that is explicitly mentioned or strongly implied.
2. If a field isn't mentioned, DO NOT include it in the output.
3. Combine all extracted fields into a single JSON object.
4. Output ONLY valid JSON.
5. If the user mentions constraints or entities that don't fit these fields, put them in "extra_constraints" (list of strings).
"""
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            raw = await llm.complete(messages=messages, max_tokens=1500, temperature=0.1)
            
            match = re.search(r'(\{.*\})', raw, re.DOTALL)
            if not match:
                logger.warning("[IntentExtraction] No JSON found in LLM response.")
                return brain
                
            data = json.loads(match.group(1))
            
            # Apply extracted data to brain deterministically
            for field, value in data.items():
                if field == "extra_constraints":
                    if isinstance(value, list):
                        brain.memory.constraints.extend([c for c in value if c not in brain.memory.constraints])
                    continue
                    
                if field in expected_fields and value:
                    existing = brain.memory.decisions.get(field)
                    
                    # Update decision
                    brain.memory.decisions[field] = DecisionState(
                        status="confirmed",
                        value=value,
                        confidence=1.0,
                        source="user",
                        reason="Extracted from intent"
                    )
                    
                    # Add to timeline
                    brain.memory.timeline.append(DecisionEvent(
                        field_id=field,
                        old_value=existing.value if existing else None,
                        new_value=value,
                        reason="Intent Extraction"
                    ))
                    
                    if field not in brain.completed_questions:
                        brain.completed_questions.append(field)
                        
            # Handle categorical override directly
            if "website_category" in data and not brain.website_category:
                brain.website_category = data["website_category"]
                
        except Exception as e:
            logger.error(f"[IntentExtraction] Failed to extract intent: {e}")
            
        return brain
