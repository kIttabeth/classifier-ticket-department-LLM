from fastapi import APIRouter, BackgroundTasks

from app.schemas.predict_ticket_schema import predictRequest, predictResponse
from app.services.predict_agent.agent import graph

router = APIRouter(prefix="/predict-LLM", tags=["predict-ticket"])

@router.post("/", response_model=predictResponse)
async def predict_ticket(tickets: predictRequest, background_tasks: BackgroundTasks):
    try:
        grouped_tickets = {}

        for ticket in tickets.data:
            grouped_tickets.setdefault(ticket.form_id, []).append(
                {
                    "title": ticket.title,
                    "description": ticket.description,
                }
            )

        form_ids = list(grouped_tickets.keys())

        for form_id in form_ids:
            state_dict = {
                "form_id": form_id,
                "grouped_tickets": grouped_tickets[form_id]
            }
            background_tasks.add_task(
                graph.ainvoke,
                state_dict,
                {"configurable": {"thread_id": form_id}},
            )

        return predictResponse(
            form_ids=form_ids,
            queued_count=len(form_ids),
            message="Processing queued",
            status=200
        )
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))