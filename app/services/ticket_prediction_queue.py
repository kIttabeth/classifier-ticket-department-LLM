# This module owns queueing prediction jobs from transport DTOs into Celery state.
import uuid
from typing import Iterable

from app.schemas.predict_ticket_schema import companyData, predictResponse
from app.worker import ticket_prediction


def build_thread_id(company_id: str, form_id: str) -> str:
    # Build a unique LangGraph thread ID for one company/form prediction job.
    return f"{company_id}_{form_id}_{uuid.uuid4().hex[:8]}"


def queue_prediction_jobs(request_data: Iterable[companyData]) -> predictResponse:
    # Group incoming forms by company/form and enqueue one Celery task per group.
    grouped_tickets = {}

    for company in request_data:
        for form in company.forms:
            key = (company.company_id, form.id)
            grouped_tickets.setdefault(key, []).append(
                {
                    "title": form.title,
                    "description": form.description,
                }
            )

    queued_count = 0
    for (company_id, form_id), tickets_list in grouped_tickets.items():
        state_dict = {
            "company_id": company_id,
            "form_id": form_id,
            "grouped_tickets": tickets_list,
            "thread_id": build_thread_id(company_id, form_id),
        }
        ticket_prediction.delay(state_dict)
        queued_count += 1

    return predictResponse(
        message="Processing queued",
        queued_count=queued_count,
    )
