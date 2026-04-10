from langgraph.graph import StateGraph,END,START
from app.services.predict_agent.util.node import llm_predict_node,callback_node
from app.services.predict_agent.util.state import TicketState

# สร้าง Graph
builder = StateGraph(TicketState)

builder.add_node("LLM_predict",llm_predict_node)
builder.add_node("Callback_node",callback_node)

builder.add_edge(START,"LLM_predict")
builder.add_edge("LLM_predict","Callback_node")
builder.add_edge("Callback_node",END)

graph = builder.compile()