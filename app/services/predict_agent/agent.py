# This module builds the LangGraph workflow for ticket prediction.
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.services.predict_agent.utils.node import (
    cache_lookup_node,
    callback_node,
    llm_predict_node,
    route_after_cache_lookup,
    save_cache_node,
)
from app.services.predict_agent.utils.state import TicketState

builder = StateGraph(TicketState) 
# builder = StateGraph(TicketState, input=TicketItem) #map key จาก TicketItem ไปยัง TicketState โดยตรง

builder.add_node("cache_lookup", cache_lookup_node)
builder.add_node("llm_predict", llm_predict_node)
builder.add_node("save_cache", save_cache_node)
builder.add_node("callback_node", callback_node)

builder.add_edge(START, "cache_lookup")
builder.add_conditional_edges(
    "cache_lookup",
    route_after_cache_lookup,
    ["llm_predict", "callback_node"],
)
builder.add_edge("llm_predict", "save_cache")
builder.add_edge("save_cache", "callback_node")
builder.add_edge("callback_node", END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)
