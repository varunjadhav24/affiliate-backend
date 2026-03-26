from typing import Any, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph

class AgentState(TypedDict, total=False):
    niche_id: Optional[int]
    niche_name: Optional[str]
    subdomain: Optional[str]
    keyword_data: Optional[list]
    trend_data: Optional[list]
    competition_score: Optional[float]
    search_volume: Optional[int]
    recommended_budget: Optional[float]
    estimated_roas: Optional[float]
    estimated_monthly_revenue: Optional[float]
    go_no_go: Optional[str]
    score: Optional[float]
    pages_generated: Optional[list]
    pages_published: Optional[int]
    affiliate_products: Optional[list]
    links_created: Optional[int]
    campaign_id: Optional[str]
    campaign_status: Optional[str]
    budget_allocated: Optional[float]
    error: Optional[str]
    messages: Optional[list]
    next_action: Optional[str]
    completed: bool

class BaseAgent:
    name: str = "BaseAgent"
    def __init__(self):
        self.graph = None
    def build(self):
        raise NotImplementedError
    def run(self, initial_state: AgentState) -> AgentState:
        if self.graph is None:
            self.graph = self.build()
        return self.graph.invoke(initial_state)
