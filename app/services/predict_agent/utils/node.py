import httpx

from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.services.predict_agent.utils.state import TicketState, LLMPredictOutput, TicketPredictResult, TicketItem
from app.core.config import settings
# การตั้งค่า LLM (gemini-2.5-flash)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
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

async def llm_predict_node(state: TicketState) -> Dict[str, Any]:

    print(state)

    if state.error or not state.success:
        print("[NODE PREDICT]: LLM can't processing")
        return {
            "success": False,
            "error": "Invalid state",
            "steps": state.steps + [{"node": "LLM_predict", "status": "error", "error": "Invalid state"}]
        }

    print("--- NODE: LLM_predict ---")
    tickets = state.grouped_tickets

    if not tickets:
        if state.title and state.description:
            tickets = [TicketItem(title=state.title, description=state.description)]
        else:
            return {
                "success": False,
                "error": "No tickets provided",
                "steps": state.steps + [{"node": "LLM_predict", "status": "error", "error": "No tickets provided"}]
            }
    
    # สร้าง Prompt Template สำหรับส่งไปให้ Gemini 
    prompt = ChatPromptTemplate.from_messages([
        ("system", PREDICT_SYSTEM_PROMPT),
        ("human", "Ticket Title: {title}\nTicket Description: {description}\n\nProvide your analysis matching the schema perfectly.")
    ])
    
    # ใช้ with_structured_output เพื่อบังคับโครงสร้างข้อมูลให้ออกมาตาม BaseModel
    chain = prompt | llm.with_structured_output(LLMPredictOutput)
    
    try:
        results = []

        for item in tickets:
            result: LLMPredictOutput = await chain.ainvoke({
                "title": item.title,
                "description": item.description
            })
            results.append(
                TicketPredictResult(
                    title=item.title,
                    description=item.description,
                    prediction=result,
                )
            )
        print(f"LLM Predict Results: {results}")

        return {
            "data": results,
            "success": True,
            "steps": state.steps + [{"node": "LLM_predict", "status": "success", "result_count": len(results)}]
        }

    except Exception as e:
        print(f"Error in LLM_predict: {e}")
        return {
            "success": False,
            "error": str(e),
            "steps": state.steps + [{"node": "LLM_predict", "status": "error", "error": str(e)}]
        }

async def callback_node(state: TicketState):
    print("--- [NODE CALLBACK]: callback_node ---")
    callback_url = f"{settings.BASE_BACKEND_URL}/api/v1/create/ticket"

    if state.error or not state.success or not state.data:
        payload = {
            "form_id": state.form_id,
            "status": "failed",
            "message": f"Failed to process ticket {state.error}",
        }
    else:
        payload = {
            "form_id": state.form_id,
            "status": "success",
            "data": [item.model_dump() for item in state.data],
            "message": f"Ticket {state.form_id} processed successfully ",
            }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(callback_url, json=payload)
            print(f"Callback response: {response.status_code} - {response.text}")

            if response.status_code in (200, 204):
                return {
                    "callback_response": {
                        "status": "Success",
                        "status_code": response.status_code,
                        "message": "Callback successful",
                    }
                }

            return {
                "callback_response": {
                    "status": "Failed",
                    "status_code": response.status_code,
                    "message": response.text,
                }
            }
    except Exception as e:
        print(f"Error in callback_node: {e}")
        return {
            "callback_response": {"status": "Failed", "error": str(e)},
        }
        