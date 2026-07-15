import logging
import json
from typing import List, Dict, Any
from src.AI.catalog.registry import DesignRegistry
from src.AI.catalog.schemas import DesignMetadata, DesignIntent, RankedDesign
from src.AI.memory.brain import ProjectBrain
from pydantic import BaseModel
from src.utils.settings import settings
from groq import AsyncGroq
from src.utils.llm_retry import with_retry, RetryPolicy

logger = logging.getLogger(__name__)

class RecommendationEngine:
    @classmethod
    @with_retry(RetryPolicy(max_retries=1))
    async def extract_design_intent(cls, brain: ProjectBrain, website_plan: Dict[str, Any]) -> DesignIntent:
        """Translates ProjectBrain and WebsitePlan into a structured DesignIntent."""
        client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        schema = DesignIntent.model_json_schema()
        
        prompt = f"""You are an expert design strategist.
Extract the visual design intent based on the project requirements.

ProjectBrain:
{brain.model_dump_json()}

WebsitePlan:
{json.dumps(website_plan)}

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
        return DesignIntent(**data)
        
    @classmethod
    def get_similar_designs(cls, design: DesignMetadata, all_designs: List[DesignMetadata], limit: int = 3) -> List[DesignMetadata]:
        similar = []
        for d in all_designs:
            if d.id == design.id:
                continue
            
            score = 0
            if d.category == design.category:
                score += 2
            score += len(set(d.tags) & set(design.tags))
            score += len(set(d.industries) & set(design.industries))
            
            if score > 0:
                similar.append((score, d))
                
        similar.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in similar[:limit]]

    @classmethod
    def get_fallback_recommendations(cls) -> List[RankedDesign]:
        logger.warning("Using fallback design recommendations.")
        fallbacks = ["external_minimal", "external_apple", "external_claude", "external_stripe", "external_editorial"]
        all_designs = DesignRegistry.get_all()
        results = []
        
        for f_id in fallbacks:
            for d in all_designs:
                if d.id == f_id or f_id in d.id.lower():
                    results.append(RankedDesign(
                        design=d, score=90.0, confidence=80.0, 
                        reason="A reliable default design suitable for most projects.",
                        similar_designs=cls.get_similar_designs(d, all_designs)
                    ))
                    break
                    
        # If still empty just return first 5
        if not results and all_designs:
            for d in all_designs[:5]:
                results.append(RankedDesign(
                    design=d, score=85.0, confidence=75.0, 
                    reason="A safe fallback design.",
                    similar_designs=cls.get_similar_designs(d, all_designs)
                ))
        return results

    @classmethod
    @with_retry(RetryPolicy(max_retries=1))
    async def rank_candidates_with_llm(cls, intent: DesignIntent, candidates: List[DesignMetadata], all_designs: List[DesignMetadata]) -> List[RankedDesign]:
        client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        
        candidates_json = [{"id": c.id, "name": c.display_name, "tags": c.tags, "desc": c.short_description} for c in candidates]
        
        schema = {
            "type": "object",
            "properties": {
                "recommendations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "score": {"type": "number"},
                            "confidence": {"type": "number"},
                            "reason": {"type": "string"}
                        },
                        "required": ["id", "score", "confidence", "reason"]
                    }
                }
            },
            "required": ["recommendations"]
        }

        prompt = f"""You are a senior UI/UX design recommendation engine.
Given the DesignIntent and a list of Candidate designs, rank the top 5 BEST matches.
Score is 0-100 for visual match. Confidence is 0-100 for how sure you are it fits.
Reason should explain exactly why to the user in one sentence.

DesignIntent:
{intent.model_dump_json()}

Candidates:
{json.dumps(candidates_json)}

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
        
        results = []
        for rec in data.get("recommendations", [])[:5]:
            for c in candidates:
                if c.id == rec["id"]:
                    results.append(RankedDesign(
                        design=c,
                        score=rec["score"],
                        confidence=rec["confidence"],
                        reason=rec["reason"],
                        similar_designs=cls.get_similar_designs(c, all_designs)
                    ))
                    break
                    
        return results

    @classmethod
    async def get_recommendations(cls, brain: ProjectBrain, website_plan: Dict[str, Any] = None) -> List[RankedDesign]:
        website_plan = website_plan or {}
        all_designs = DesignRegistry.get_all()
        if not all_designs:
            return []

        try:
            # 1. Extract Intent
            intent = await cls.extract_design_intent(brain, website_plan)
            
            # 2. Fast Filter (heuristics)
            intent_ind = intent.industry.lower()
            candidates = []
            for d in all_designs:
                avoid = [a.lower() for a in d.avoid_for]
                if intent_ind and any(intent_ind in a or a in intent_ind for a in avoid):
                    logger.debug(f"Filtered out {d.id} due to avoid_for conflict.")
                    continue
                candidates.append(d)
                
            if len(candidates) < 5:
                candidates = all_designs
                
            # Heuristically sort to get top 15
            candidates.sort(key=lambda x: len(set(x.tags) & set([intent.visual_style, intent.tone, intent.brand_personality])), reverse=True)
            candidates = candidates[:15]
            
            # 3. LLM Ranking
            ranked = await cls.rank_candidates_with_llm(intent, candidates, all_designs)
            if not ranked:
                return cls.get_fallback_recommendations()
                
            ranked.sort(key=lambda x: x.score, reverse=True)
            return ranked
            
        except Exception as e:
            logger.error(f"Error in recommendation engine: {e}")
            return cls.get_fallback_recommendations()
