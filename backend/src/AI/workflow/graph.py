from pydantic import BaseModel, Field
from typing import List, Optional
from src.AI.memory.brain import ProjectBrain

class QuestionNode(BaseModel):
    id: str
    priority: int
    applicable_categories: List[str] = Field(default_factory=lambda: ["ALL"])
    dependencies: List[str] = Field(default_factory=list)
    prompt_text: str

def evaluate_graph(brain: ProjectBrain, nodes: List[QuestionNode]) -> Optional[QuestionNode]:
    """
    Evaluates the question graph deterministically based on priorities, 
    dependencies, and completed nodes.
    """
    completed = set(brain.completed_questions)
    
    category = brain.website_category or "ALL"
    valid_nodes = []
    
    for node in nodes:
        if node.id in completed:
            continue
            
        is_applicable = "ALL" in node.applicable_categories or category in node.applicable_categories
        if not is_applicable:
            continue
            
        deps_met = all(dep in completed for dep in node.dependencies)
        if deps_met:
            valid_nodes.append(node)
            
    valid_nodes.sort(key=lambda x: x.priority, reverse=True)
    
    if valid_nodes:
        return valid_nodes[0]
        
    return None

DEFAULT_REGISTRY = [
    QuestionNode(
        id="website_category",
        priority=100,
        prompt_text="What type of website are you looking to build? (e.g., SaaS, E-commerce, Portfolio)"
    ),
    QuestionNode(
        id="audience",
        priority=90,
        dependencies=["website_category"],
        prompt_text="Who is the primary audience for this website?"
    ),
    QuestionNode(
        id="business_name",
        priority=80,
        dependencies=["website_category"],
        prompt_text="What is the name of your business or project?"
    ),
    QuestionNode(
        id="saas_pricing",
        priority=70,
        applicable_categories=["SaaS"],
        dependencies=["website_category"],
        prompt_text="Will your SaaS have tiered pricing?"
    ),
    QuestionNode(
        id="ecommerce_products",
        priority=70,
        applicable_categories=["E-commerce"],
        dependencies=["website_category"],
        prompt_text="What kind of products will you be selling?"
    )
]
