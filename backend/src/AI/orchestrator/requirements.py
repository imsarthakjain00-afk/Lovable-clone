"""
Requirement Registry and Question Planner

Manages the list of requirements and bundles them into natural questions.
"""
from typing import List, Optional, Tuple, Dict, Any
from src.AI.workflow.requirements import DiscoveryRequirement, DEFAULT_REQUIREMENTS
from src.AI.memory.brain import ProjectBrain
from src.AI.llm.provider import get_llm_provider
from src.utils.llm_retry import with_retry, RetryPolicy
import json
import logging

logger = logging.getLogger(__name__)

class RequirementResolver:
    @staticmethod
    def get_unresolved_requirements(brain: ProjectBrain, requirements: List[DiscoveryRequirement] = DEFAULT_REQUIREMENTS) -> List[DiscoveryRequirement]:
        """
        Returns a prioritized list of requirements that have not been satisfied with high confidence.
        """
        category = brain.website_category or "ALL"
        decisions = brain.memory.decisions
        
        valid_missing = []
        
        for req in requirements:
            # Check applicability
            is_applicable = "ALL" in req.applicable_categories or category in req.applicable_categories
            if not is_applicable:
                continue
                
            state = decisions.get(req.id)
            # A requirement is considered resolved if it is confirmed or inferred with high confidence
            if state and (state.status == "confirmed" or (state.status == "inferred" and state.confidence > 0.8)):
                continue
                
            # Check dependencies
            deps_met = True
            for dep in req.dependencies:
                dep_state = decisions.get(dep)
                if not dep_state or (dep_state.status != "confirmed" and dep_state.confidence <= 0.8):
                    deps_met = False
                    break
                    
            if deps_met:
                valid_missing.append(req)
                
        valid_missing.sort(key=lambda x: x.priority, reverse=True)
        return valid_missing


class QuestionPlanner:
    @classmethod
    @with_retry(RetryPolicy(max_retries=1))
    async def bundle_and_ask(cls, missing_reqs: List[DiscoveryRequirement], brain: ProjectBrain, last_user_message: str = "") -> str:
        """
        Bundles the top requirements into a single, cohesive, natural question.
        Acts as an experienced AI Product Manager.
        """
        if not missing_reqs:
            return ""
            
        llm = get_llm_provider()
        
        # Take the top 2-3 requirements to bundle
        req_descriptions = [req.description for req in missing_reqs[:3]]
        known_facts = json.dumps(brain.memory.project_facts[:10]) if brain.memory.project_facts else '[]'

        prompt = f"""You are a senior AI Product Manager acting as an expert website builder.
You are having a discovery conversation with a client.

WHAT THE CLIENT JUST SAID:
"{last_user_message}"

WHAT YOU ALREADY KNOW ABOUT THEIR PROJECT:
{known_facts}

WHAT YOU STILL NEED TO FIND OUT:
{json.dumps(req_descriptions)}

YOUR TASK:
Write a single, natural follow-up response that:
1. Acknowledges what they just said gracefully.
2. Bundles the missing information into ONE cohesive, conversational question.
3. Provides 2-3 short examples in the question to help them answer (e.g. "Are you looking for something minimal, luxury, or playful?").
4. Sounds like a real human Product Manager — sharp, warm, professional.

STRICT RULES:
- NEVER say "Great!", "Awesome!", or "Sure!"
- NEVER ask a bulleted list of questions. Combine them into one smooth thought.
- Keep it short: max 3 sentences total.

Response:"""

        response = await llm.complete(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.4
        )
        return response.strip()
