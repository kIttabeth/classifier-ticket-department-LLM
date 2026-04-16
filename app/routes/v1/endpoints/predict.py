from fastapi import APIRouter, BackgroundTasks

from app.schemas.predict_ticket_schema import predictRequest, predictResponse
from app.services.predict_agent.agent import graph

router = APIRouter(prefix="/predict-LLM", tags=["predict-ticket"])

@router.post("/", response_model=predictResponse)
async def predict_ticket(tickets: predictRequest, background_tasks: BackgroundTasks):
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

        form_ids = []

        for (company_id, form_id), tickets_list in grouped_tickets.items():
            form_ids.append(form_id)
            state_dict = {
                "company_id": company_id,
                "form_id": form_id,
                "grouped_tickets": tickets_list
            }

        # state_dict = {
        #     "company_id": "xxxx1",
        #     "form_id":    "form_A",
        #     "grouped_tickets": [
        #         {"title": "Bug Report",   "description": "App crashes"},
        #         {"title": "Bug Report 2", "description": "Login fail"},
        #     ]
        # }
        
            background_tasks.add_task(
                graph.ainvoke,
                state_dict,
                {"configurable": {"thread_id": f"{company_id}-{form_id}"}},
            )

        return predictResponse(
            message="Processing queued",
            queued_count=len(form_ids),
        )
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))