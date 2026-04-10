from fastapi import APIRouter,BackgroundTasks
from app.schemas.predict_ticket_schema import predictRequest,predictResponse
from app.services.predict_agent.util.agent import graph

router = APIRouter(prefix="/predict",tags=["predict-ticket"])

@router.post("/", response_model=predictResponse)
async def predict_ticket(ticket: predictRequest, background_tasks: BackgroundTasks):
    state_dict = {
        "form_id": ticket.from_id,
        "title": ticket.title,
        "description": ticket.description
    }

    background_tasks.add_task(graph.ainvoke, state_dict)

    return predictResponse(
        form_id=ticket.from_id,
        message="Processing queued",
        status=200
    )