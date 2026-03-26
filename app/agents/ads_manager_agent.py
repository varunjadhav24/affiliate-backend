from langgraph.graph import StateGraph, END
from app.agents.base import AgentState, BaseAgent

def create_campaign(state):
    state["campaign_id"] = None
    state["campaign_status"] = "draft"
    state["messages"] = state.get("messages", []) + ["campaign created (stub)"]
    return state

def monitor_performance(state):
    state["messages"] = state.get("messages", []) + ["performance monitored (stub)"]
    return state

def optimise_bids(state):
    state["messages"] = state.get("messages", []) + ["bids optimised (stub)"]
    return state

def reallocate_budget(state):
    state["budget_allocated"] = 0.0
    state["completed"] = True
    state["messages"] = state.get("messages", []) + ["budget reallocated (stub)"]
    return state

class AdsManagerAgent(BaseAgent):
    name = "AdsManagerAgent"
    def build(self):
        g = StateGraph(AgentState)
        g.add_node("create_campaign", create_campaign)
        g.add_node("monitor_performance", monitor_performance)
        g.add_node("optimise_bids", optimise_bids)
        g.add_node("reallocate_budget", reallocate_budget)
        g.set_entry_point("create_campaign")
        g.add_edge("create_campaign", "monitor_performance")
        g.add_edge("monitor_performance", "optimise_bids")
        g.add_edge("optimise_bids", "reallocate_budget")
        g.add_edge("reallocate_budget", END)
        return g.compile()
