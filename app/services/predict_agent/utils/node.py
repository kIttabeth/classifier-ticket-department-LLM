import httpx
import json

from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from app.services.predict_agent.utils.state import TicketState, TicketPredictResult, TicketItem
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
If a ticket title or description is not related to recommendation requests or problem/issue reports,
set both `priority` and `department_name` to null.
"""


def _build_predict_messages(title: str, description: str, department_info: Any) -> list[dict[str, str]]:
    system_content = PREDICT_SYSTEM_PROMPT + "\n\nAvailable Departments:\n" + json.dumps(department_info, ensure_ascii=False)
    user_content = (
        "Ticket Title: " + title + "\n"
        + "Ticket Description: " + description + "\n\n"
        + "Provide your analysis perfectly matching the schema and select the 'department_name' from the provided Available Departments."
    )

    # เดิมใช้ ChatPromptTemplate.from_messages([...]) แต่ตอนนี้เปลี่ยนมาใช้ messages ตรงๆ
    # prompt = ChatPromptTemplate.from_messages([
    #     {"role": "system", "content": PREDICT_SYSTEM_PROMPT + "\n\nAvailable Departments:\n{department_info}"},
    #     {"role": "user", "content": "Ticket Title: {title}\nTicket Description: {description}\n\nProvide your analysis perfectly matching the schema and select the 'department_name' from the provided Available Departments."},
    # ])

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def _normalize_department_name(name: str) -> str:
    return (name or "").strip().lower()


def _extract_department_mapping(raw_departments: Any) -> Dict[str, str]:
    """Build {normalized_department_name: department_id} mapping from API response."""
    if isinstance(raw_departments, str):
        return {}

    department_list = raw_departments
    if isinstance(raw_departments, dict):
        if isinstance(raw_departments.get("data"), list):
            department_list = raw_departments.get("data")
        elif isinstance(raw_departments.get("departments"), list):
            department_list = raw_departments.get("departments")

    mapping: Dict[str, str] = {}
    if not isinstance(department_list, list):
        return mapping

    for dept in department_list:
        if not isinstance(dept, dict):
            continue

        dept_id = str(
            dept.get("id")
            or dept.get("department_id")
            or dept.get("_id")
            or ""
        ).strip()
        dept_name = str(
            dept.get("name")
            or dept.get("department_name")
            or dept.get("title")
            or ""
        ).strip()

        if dept_id and dept_name:
            mapping[_normalize_department_name(dept_name)] = dept_id

    return mapping

async def get_department(company_id:str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.BASE_BACKEND_URL}/api/v1/departments/{company_id}")
            
            response.raise_for_status()  # raises HTTPStatusError ถ้า 4xx/5xx

            data = response.json()
            print(f"Available departments for company_id {company_id}: {data}")
            return data

    except httpx.HTTPStatusError as e:
        return str(e)
    except Exception as e:
        return str(e)

async def llm_predict_node(state: TicketState) -> Dict[str, Any]:

    print(state)

    if state.error or not state.success:
        print("[NODE PREDICT]: LLM can't processing")
        return {
            "success": False,
            "error": "LLM Can't processing due to previous error",
            "steps": state.steps + [{"node": "LLM_predict", "status": "error", "error": "Invalid state"}]
        }
        
    print("--- NODE: LLM_predict ---")
    tickets = state.grouped_tickets

    if not tickets:
        title = getattr(state, "title", None)
        desc = getattr(state, "description", None)
        if title and desc:
            tickets = [TicketItem(title=title, description=desc)]
        else:
            return {
                "success": False,
                "error": "No tickets provided",
                "steps": state.steps + [{"node": "LLM_predict", "status": "error", "error": "No tickets provided"}]
            }
            
    department = await get_department(state.company_id)
    if isinstance(department, str):
        print(f"[NODE PREDICT]: get_department failed: {department}")
        return {
            "success": False,
            "error": str(department),
            "steps": state.steps + [{"node": "LLM_predict", "status": "error", "error": str(department)}]
        }
    
    # สร้าง messages payload สำหรับส่งไปให้ Gemini
    # prompt = ChatPromptTemplate.from_messages([
    #     {"role": "system", "content": PREDICT_SYSTEM_PROMPT + "\n\nAvailable Departments:\n{department_info}"},
    #     {"role": "user", "content": "Ticket Title: {title}\nTicket Description: {description}\n\nProvide your analysis perfectly matching the schema and select the 'department_name' from the provided Available Departments."},
    # ])
    
    # ใช้ with_structured_output เพื่อบังคับโครงสร้างข้อมูลให้ออกมาตาม BaseModel
    # chain = prompt | llm.with_structured_output(TicketPredictResult)
    chain = llm.with_structured_output(TicketPredictResult)
    
    try:
        results = []

        for item in tickets:
            # result: TicketPredictResult = await chain.ainvoke(
            #    {"department_info": department, "title": item.title, "description": item.description}
            #)
            messages = _build_predict_messages(item.title, item.description, department)
            result: TicketPredictResult = await chain.ainvoke(messages)
            
            # บังคับ title / description เดิม เผื่อ LLM ตอบกลับมาเพี้ยน
            result.title = item.title
            result.description = item.description
            
            results.append(result)
            
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
    callback_url = f"{settings.BASE_BACKEND_URL}/api/v1/create-bulk"
    
    print(f"path {callback_url}")
    payload = []
    departments = await get_department(state.company_id)
    department_mapping = _extract_department_mapping(departments)
    
    if state.error or not state.success or not state.data:
        tickets_list = state.grouped_tickets
        if not tickets_list:
            # Fallback if no grouped tickets but have title/desc
            body_title = getattr(state, "title", "")
            body_desc = getattr(state, "description", "")
            if body_title or body_desc:
                tickets_list = [TicketItem(title=body_title, description=body_desc)]

        error_msg = str(state.error) if state.error else "Failed to process ticket"
        
        if tickets_list:
            for t in tickets_list:
                payload.append({
                    "department_id": "",
                    "form_id": state.form_id,
                    "description": t.description,
                    "message": error_msg,
                    "priority": "",
                    "status": "failed",
                    "title": t.title
                })
        else:
            payload.append({
                "department_id": "",
                "form_id": state.form_id,
                "description": "",
                "message": error_msg,
                "priority": "",
                "status": "failed",
                "title": ""
            })
    else:
        for item in state.data:
            priority_val = item.priority.value if hasattr(item.priority, "value") else item.priority
            department_name = getattr(item, "department_name", "")

            # ข้ามรายการที่โมเดลระบุว่าไม่เกี่ยวกับงาน triage
            if priority_val is None and department_name is None:
                continue

            mapped_department_id = department_mapping.get(_normalize_department_name(department_name), "")
            payload.append({
                "department_id": mapped_department_id,
                "form_id": state.form_id,
                "description": item.description,
                "message": "Processed successfully" if mapped_department_id else f"Department '{department_name}' not found",
                "priority": priority_val,
                "status": "success" if mapped_department_id else "failed",
                "title": item.title
            })

    if not payload:
        return {
            "callback_response": {
                "status": "Skipped",
                "status_code": 204,
                "message": "No callback payload to send",
            }
        }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(callback_url, json=payload)
            print("payload:",payload)
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
        