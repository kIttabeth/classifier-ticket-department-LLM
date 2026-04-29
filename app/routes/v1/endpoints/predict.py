# This module exposes the ticket prediction endpoint.
from fastapi import APIRouter, HTTPException
import uuid

from app.schemas.predict_ticket_schema import predictRequest, predictResponse
from app.worker import ticket_prediction

router = APIRouter(tags=["predict-ticket"])

@router.post("/predict-LLM", response_model=predictResponse)
async def predict_ticket(tickets: predictRequest):
    # Queue grouped ticket prediction jobs for asynchronous processing.
    try:
        grouped_tickets = {}
        
        print(tickets)

        for company in tickets.data:
            for form in company.forms:
                key = (company.company_id, form.id)
                grouped_tickets.setdefault(key, []).append(
                    {
                        "title": form.title,
                        "description": form.description,
                    }
                )
        # {
        #   ("xxxx1", "form_A"): [
        #     {"title": "Bug Report",   "description": "App crashes"},
        #     {"title": "Bug Report 2", "description": "Login fail"},
        #   ],
        #   ("xxxx1", "form_B"): [
        #     {"title": "Feature Req",  "description": "Add darkmode"},
        #   ],
        #   ("xxxx2", "form_C"): [
        #     {"title": "Support",      "description": "Can't pay"},
        #   ],
        # }

        queued_count = 0

        for (company_id, form_id), tickets_list in grouped_tickets.items():
            state_dict = {
                "company_id": company_id,
                "form_id": form_id,
                "grouped_tickets": tickets_list
            }
            
            state_dict["thread_id"] = f"{company_id}_{form_id}_{uuid.uuid4().hex[:8]}"  # เพิ่ม thread_id ที่ไม่ซ้ำกันสำหรับแต่ละงาน
            
            ticket_prediction.delay(state_dict)
            queued_count += 1

        return predictResponse(
            message="Processing queued",
            queued_count=queued_count,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
