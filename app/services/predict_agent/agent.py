from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END, START
from app.services.predict_agent.utils.node import llm_predict_node,callback_node
from app.services.predict_agent.utils.state import TicketState

# สร้าง Graph
builder = StateGraph(TicketState)

builder.add_node("llm_predict",llm_predict_node)
builder.add_node("callback_node",callback_node)

builder.add_edge(START,"llm_predict")
builder.add_edge("llm_predict","callback_node")
builder.add_edge("callback_node",END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)