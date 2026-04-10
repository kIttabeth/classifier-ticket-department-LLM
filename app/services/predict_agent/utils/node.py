from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.services.predict_agent.util.state import TicketState, LLMPredictOutput
from app.core.config import settings
# การตั้งค่า LLM (gemini-2.5-flash)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    api_key=settings.GEMINI_API_KEY
)

PREDICT_SYSTEM_PROMPT = """
You are an expert IT triage routing system.

Your task is to analyze support tickets and classify:
- assigned department
- priority level

Always return the result strictly following the required schema.
Do not include any explanation outside the schema.
"""



def llm_predict_node(state: TicketState) -> Dict[str, Any]:

    print(state)

    if state.error or not state.success or not state.title or not state.description:
        print("[NODE PREDICT]: LLM can't processing")
        return {
            "success": False,
            "error": "Invalid state",
            "steps": state.steps + [{"node": "LLM_predict", "status": "error", "error": "Invalid state"}]
        }

    print("--- NODE: LLM_predict ---")
    title = state.title
    description = state.description
    
    # สร้าง Prompt Template สำหรับส่งไปให้ Gemini 
    prompt = ChatPromptTemplate.from_messages([
        ("system", PREDICT_SYSTEM_PROMPT),
        ("human", "Ticket Title: {title}\nTicket Description: {description}\n\nProvide your analysis matching the schema perfectly.")
    ])
    
    # ใช้ with_structured_output เพื่อบังคับโครงสร้างข้อมูลให้ออกมาตาม BaseModel
    chain = prompt | llm.with_structured_output(LLMPredictOutput)
    
    try:
        # พยากรณ์ผลลัพธ์
        result: LLMPredictOutput = chain.invoke({
            "title": title,
            "description": description
        })
        
        # คืนค่า (dict) เพื่อเอาไปอัปเดต state ตัวหลักของ Graph
        return {
            "data": result,
            "success": True,
            "steps": state.steps + [{"node": "LLM_predict", "status": "success", "result": result.dict()}]
        }
        
    except Exception as e:
        print(f"Error in LLM_predict: {e}")
        return {
            "success": False,
            "error": str(e),
            "steps": state.steps + [{"node": "LLM_predict", "status": "error", "error": str(e)}]
        }

def callback_node(state: TicketState):
    print(f"Title: {state.title}")
    print(f"Description: {state.description}")
    print(f"Data: {state.data}")
    print(f"Success: {state.success}")
    print(f"Error: {state.error}")
    print(f"Steps: {state.steps}")