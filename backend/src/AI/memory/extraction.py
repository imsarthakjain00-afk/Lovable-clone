import json
import logging
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from src.utils.settings import settings
from src.AI.llm.provider import get_llm_provider
from src.AI.memory.brain import ProjectBrain

logger = logging.getLogger(__name__)

import re
from src.AI.memory.brain import DecisionState, DecisionEvent

class ExtractedDecision(BaseModel):
    field_id: str = Field(description="The ID of the requirement or question being answered.")
    value: Any = Field(description="The extracted value, fully resolved. (e.g. if user said 'all of them', this must be the actual list of all options).")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0.")
    status: str = Field(description="One of: 'confirmed', 'inferred', 'rejected'")
    source: str = Field(default="user_input", description="Where this decision came from.")
    reason: str = Field(default="", description="Why this value was extracted.")

class MemoryExtractionResult(BaseModel):
    category_detected: Optional[str] = Field(default=None, description="Detected website category (e.g., SaaS, E-commerce).")
    decisions: List[ExtractedDecision] = Field(default_factory=list, description="List of extracted decisions or answers.")
    entities: List[str] = Field(default_factory=list, description="Key entities mentioned (e.g., specific brand names, products).")
    constraints: List[str] = Field(default_factory=list, description="Explicit constraints mentioned by the user.")

def deterministic_extract_entities(text: str) -> List[str]:
    """Extracts obvious entities before LLM to save tokens and improve accuracy."""
    entities = []
    # Emails
    emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
    if emails:
        entities.extend([f"Email: {e}" for e in emails])
    # URLs
    urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', text)
    if urls:
        entities.extend([f"Website: {u}" for u in urls])
    # Phones (very simple)
    phones = re.findall(r'\+?\d[\d -]{8,12}\d', text)
    if phones:
        entities.extend([f"Phone: {p}" for p in phones])
    return list(set(entities))

async def extract_memory(user_message: str, current_brain: ProjectBrain, active_question_id: str = None) -> MemoryExtractionResult:
    """
    Extracts structured memory from a user message using Groq's JSON mode.
    Acts as an Answer Resolver.
    """
    pre_extracted_entities = deterministic_extract_entities(user_message)
    
    llm = get_llm_provider()
    schema = MemoryExtractionResult.model_json_schema()
    
    from src.AI.workflow.requirements import DEFAULT_REQUIREMENTS
    valid_fields = {req.id: req.description for req in DEFAULT_REQUIREMENTS}
    
    # Format current decisions for LLM context
    current_decisions = {k: v.model_dump() for k, v in current_brain.memory.decisions.items()}
    
    sys_prompt = f"""You are a senior AI Product Manager parsing user input.
Your job is to resolve answers, extract bulk information, and map it to structured decisions.

# CRITICAL RULES:
1. Answer Resolution: If the user gives an indirect answer like "all of these", "both", "yes", "the first one", you MUST resolve it to the actual explicit values based on the Active Question. Never store "all of these" as a value.
2. Bulk Extraction: If the user pastes a massive wall of text, extract everything possible into 'decisions' (e.g. business_name, core_features) and 'entities'.
3. Do not ignore ANY rich user input.
4. Set status to 'confirmed' if explicitly stated, 'inferred' if you guessed it, or 'rejected' if the user said they don't want it.
5. You MUST ONLY use the following field_ids for your extracted decisions:
{json.dumps(valid_fields, indent=2)}
If something doesn't match perfectly, put it in 'entities' or 'constraints'. Do NOT invent new field_ids.

You must return a JSON object conforming EXACTLY to this schema:
{json.dumps(schema)}

Current Project State (For Context):
Category: {current_brain.website_category}
Active Question ID (if any): {active_question_id}
Pre-extracted entities: {pre_extracted_entities}
Current Decisions: {json.dumps(current_decisions)}
"""

    try:
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_message}
        ]
        raw = await llm.complete(messages=messages, max_tokens=1500, temperature=0.1)
        
        # Robustly extract JSON even if LLM adds conversational prefix text
        import re
        match = re.search(r'(\{.*\})', raw, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in LLM response")
            
        data = json.loads(match.group(1))
        res = MemoryExtractionResult(**data)
        res.entities.extend(pre_extracted_entities)
        return res
    except Exception as e:
        logger.error(f"Memory extraction failed: {e}")
        return MemoryExtractionResult(entities=pre_extracted_entities)

def apply_memory_extraction(brain: ProjectBrain, extraction: MemoryExtractionResult) -> ProjectBrain:
    """
    Applies the extracted memory to the ProjectBrain deterministically,
    handling Intent Satisfaction, Conflict Resolution, and Confidence Promotion.
    """
    if extraction.category_detected and not brain.website_category:
        brain.website_category = extraction.category_detected
        
    for decision in extraction.decisions:
        existing = brain.memory.decisions.get(decision.field_id)
        
        # Determine if we should update
        should_update = False
        reason = ""
        
        if not existing:
            should_update = True
            reason = "Initial extraction"
        else:
            if existing.status == "inferred" and decision.status == "confirmed":
                should_update = True
                reason = "Confidence promotion: user confirmed inferred value"
            elif decision.status == "confirmed" and existing.value != decision.value:
                should_update = True
                reason = "Conflict resolution: user changed their mind"
            elif decision.status == "inferred" and existing.status == "inferred" and decision.confidence > existing.confidence:
                should_update = True
                reason = "Stronger inference extracted"

        if should_update:
            old_val = existing.value if existing else None
            
            brain.memory.decisions[decision.field_id] = DecisionState(
                status=decision.status,
                value=decision.value,
                confidence=decision.confidence,
                source=decision.source,
                reason=decision.reason
            )
            
            brain.memory.timeline.append(DecisionEvent(
                field_id=decision.field_id,
                old_value=old_val,
                new_value=decision.value,
                reason=reason
            ))
            
            if decision.status == "confirmed" and decision.field_id not in brain.completed_questions:
                brain.completed_questions.append(decision.field_id)
            
    brain.memory.project_facts.extend([e for e in extraction.entities if e not in brain.memory.project_facts])
    brain.memory.constraints.extend([c for c in extraction.constraints if c not in brain.memory.constraints])
    
    return brain
