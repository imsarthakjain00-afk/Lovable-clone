from typing import List, Optional, Tuple
from src.AI.memory.brain import ProjectBrain
from src.AI.workflow.requirements import DiscoveryRequirement, DEFAULT_REQUIREMENTS

def calculate_quality_score(brain: ProjectBrain, requirements: List[DiscoveryRequirement]) -> float:
    """Calculates a Discovery Quality Score based on the current state of requirements."""
    total_weight = 0
    earned_score = 0
    
    category = brain.website_category or "ALL"
    decisions = brain.memory.decisions
    
    for req in requirements:
        is_applicable = "ALL" in req.applicable_categories or category in req.applicable_categories
        if not is_applicable:
            continue
            
        weight = req.priority
        total_weight += weight
        
        state = decisions.get(req.id)
        if state:
            if state.status == "confirmed":
                earned_score += weight * 1.0
            elif state.status == "inferred":
                earned_score += weight * (0.5 + (0.5 * state.confidence))
            
    if total_weight == 0:
        return 100.0
        
    return (earned_score / total_weight) * 100.0

def evaluate_discovery_state(brain: ProjectBrain, requirements: List[DiscoveryRequirement] = DEFAULT_REQUIREMENTS) -> Tuple[bool, float, List[DiscoveryRequirement]]:
    """
    Evaluates the current state of ProjectBrain.
    Returns (is_complete, quality_score, list_of_missing_requirements).
    """
    category = brain.website_category or "ALL"
    decisions = brain.memory.decisions
    
    valid_missing = []
    
    # 1. Determine missing requirements
    for req in requirements:
        is_applicable = "ALL" in req.applicable_categories or category in req.applicable_categories
        if not is_applicable:
            continue
            
        state = decisions.get(req.id)
        if state and state.status in ["confirmed", "inferred"]:
            continue # Satisfied
            
        # Check dependencies
        deps_met = True
        for dep in req.dependencies:
            dep_state = decisions.get(dep)
            if not dep_state or dep_state.status not in ["confirmed", "inferred"]:
                deps_met = False
                break
                
        if deps_met:
            valid_missing.append(req)
            
    # Sort missing by priority
    valid_missing.sort(key=lambda x: x.priority, reverse=True)
    
    # 2. Calculate quality score
    score = calculate_quality_score(brain, requirements)
    
    # 3. Determine if complete
    # Discovery is complete if no mandatory high-priority requirements (> 80) are missing.
    # We no longer care about the absolute score since we minimized requirements.
    high_priority_missing = [r for r in valid_missing if r.priority > 80]
    is_complete = len(high_priority_missing) == 0
    
    return is_complete, score, valid_missing
