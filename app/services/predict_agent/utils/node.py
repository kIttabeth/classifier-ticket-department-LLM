# This module handles LangGraph nodes for cache lookup, LLM prediction, and callbacks.
import json
from typing import Any, Dict, List

import httpx
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.services.predict_agent.utils.cache import (
    load_cache_entries,
    find_best_cached_prediction,
    get_ticket_embeddings,
    save_prediction_cache,
)
from app.services.predict_agent.utils.state import (
    IndexedTicketPredictResult,
    PendingTicketItem,
    TicketItem,
    TicketPredictResult,
    TicketState,
)
from app.utils.hmac import SIGNATURE_HEADER, generate_hmac

# This LLM is used for fresh predictions when semantic cache misses.
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    api_key=settings.GEMINI_API_KEY,
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
    # Build the LLM message payload for a single ticket.
    system_content = PREDICT_SYSTEM_PROMPT + "\n\nAvailable Departments:\n" + json.dumps(department_info, ensure_ascii=False)
    user_content = (
        "Ticket Title: " + title + "\n"
        + "Ticket Description: " + description + "\n\n"
        + "Provide your analysis perfectly matching the schema and select the 'department_name' from the provided Available Departments."
    )

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def _normalize_department_name(name: str) -> str:
    # Normalize a department name for lookup matching.
    return (name or "").strip().lower()


def _extract_department_mapping(raw_departments: Any) -> Dict[str, str]:
    # Build {normalized_department_name: department_id} mapping from API response.
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

    for department in department_list:
        if not isinstance(department, dict):
            continue

        department_id = str(
            department.get("id")
            or department.get("department_id")
            or department.get("_id")
            or ""
        ).strip()
        department_name = str(
            department.get("name")
            or department.get("department_name")
            or department.get("title")
            or ""
        ).strip()

        if department_id and department_name:
            mapping[_normalize_department_name(department_name)] = department_id

    return mapping


def _get_tickets_from_state(state: TicketState) -> List[TicketItem]:
    # Read ticket items from the current graph state with backward-compatible fallback.
    if state.grouped_tickets:
        return state.grouped_tickets

    title = getattr(state, "title", None)
    description = getattr(state, "description", None)
    if title and description:
        return [TicketItem(title=title, description=description)]

    return []


def _merge_indexed_results(
    ticket_count: int,
    cached_results: List[IndexedTicketPredictResult],
    fresh_results: List[IndexedTicketPredictResult],
) -> List[TicketPredictResult]:
    # Merge cached and fresh predictions back into the original ticket order.
    merged_result_map: Dict[int, TicketPredictResult] = {
        item.index: item.result for item in cached_results
    }
    merged_result_map.update({item.index: item.result for item in fresh_results})
    return [merged_result_map[index] for index in sorted(merged_result_map) if index < ticket_count]


async def get_department(company_id: str) -> Any:
    # Fetch department data for the given company.
    try:
        request_body: bytes = b""
        signature = generate_hmac(body=request_body, secret=settings.SECRET_API_KEY)
        headers = {
            "Content-Type": "application/json",
            SIGNATURE_HEADER: f"sha256={signature}",
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.BASE_BACKEND_URL}/api/v1/departments/{company_id}",
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as error:
        return str(error)
    except Exception as error:
        return str(error)


async def cache_lookup_node(state: TicketState) -> Dict[str, Any]:
    # Resolve semantic cache hits and collect only the cache misses for LLM processing.
    if state.error or not state.success:
        return {
            "success": False,
            "error": "Cache lookup skipped due to previous error",
            "steps": state.steps + [{"node": "cache_lookup", "status": "error", "error": "Invalid state"}],
        }

    tickets = _get_tickets_from_state(state)
    if not tickets:
        return {
            "success": False,
            "error": "No tickets provided",
            "steps": state.steps + [{"node": "cache_lookup", "status": "error", "error": "No tickets provided"}],
        }

    try:
        cache_entries = await load_cache_entries()
        cached_results: List[IndexedTicketPredictResult] = []
        uncached_tickets: List[PendingTicketItem] = []

        for index, ticket in enumerate(tickets):
            title_embedding, description_embedding = await get_ticket_embeddings(
                title=ticket.title,
                description=ticket.description,
            )
            cached_result, _ = find_best_cached_prediction(
                cache_entries=cache_entries,
                title_embedding=title_embedding,
                description_embedding=description_embedding,
            )

            if cached_result is not None:
                cached_results.append(
                    IndexedTicketPredictResult(index=index, result=cached_result)
                )
                continue

            uncached_tickets.append(
                PendingTicketItem(
                    index=index,
                    title=ticket.title,
                    description=ticket.description,
                    title_embedding=title_embedding,
                    description_embedding=description_embedding,
                )
            )

        data = []
        if not uncached_tickets:
            data = _merge_indexed_results(
                ticket_count=len(tickets),
                cached_results=cached_results,
                fresh_results=[],
            )

        return {
            "data": data,
            "cached_results": cached_results,
            "fresh_results": [],
            "uncached_tickets": uncached_tickets,
            "success": True,
            "steps": state.steps + [{
                "node": "cache_lookup",
                "status": "success",
                "cache_hit_count": len(cached_results),
                "cache_miss_count": len(uncached_tickets),
            }],
        }
    except Exception as error:
        return {
            "success": False,
            "error": str(error),
            "steps": state.steps + [{"node": "cache_lookup", "status": "error", "error": str(error)}],
        }


def route_after_cache_lookup(state: TicketState) -> str:
    # Route to callback immediately on full cache hit, otherwise continue to the LLM node.
    if state.error or not state.success:
        return "callback_node"
    if state.uncached_tickets:
        return "llm_predict"
    return "callback_node"


async def llm_predict_node(state: TicketState) -> Dict[str, Any]:
    # Predict priority and department for cache-miss tickets and merge with cache hits.
    if state.error or not state.success:
        return {
            "success": False,
            "error": "LLM can't process due to previous error",
            "steps": state.steps + [{"node": "llm_predict", "status": "error", "error": "Invalid state"}],
        }

    tickets = _get_tickets_from_state(state)
    if not tickets:
        return {
            "success": False,
            "error": "No tickets provided",
            "steps": state.steps + [{"node": "llm_predict", "status": "error", "error": "No tickets provided"}],
        }

    pending_tickets = state.uncached_tickets or [
        PendingTicketItem(index=index, title=ticket.title, description=ticket.description)
        for index, ticket in enumerate(tickets)
    ]

    department = await get_department(state.company_id)
    if isinstance(department, str):
        return {
            "success": False,
            "error": department,
            "steps": state.steps + [{"node": "llm_predict", "status": "error", "error": department}],
        }

    chain = llm.with_structured_output(TicketPredictResult)

    try:
        fresh_results: List[IndexedTicketPredictResult] = []

        for ticket in pending_tickets:
            messages = _build_predict_messages(ticket.title, ticket.description, department)
            result: TicketPredictResult = await chain.ainvoke(messages)
            result.title = ticket.title
            result.description = ticket.description
            fresh_results.append(
                IndexedTicketPredictResult(index=ticket.index, result=result)
            )

        data = _merge_indexed_results(
            ticket_count=len(tickets),
            cached_results=state.cached_results,
            fresh_results=fresh_results,
        )

        return {
            "data": data,
            "fresh_results": fresh_results,
            "success": True,
            "steps": state.steps + [{
                "node": "llm_predict",
                "status": "success",
                "result_count": len(fresh_results),
                "cache_hit_count": len(state.cached_results),
            }],
        }
    except Exception as error:
        return {
            "success": False,
            "error": str(error),
            "steps": state.steps + [{"node": "llm_predict", "status": "error", "error": str(error)}],
        }


async def save_cache_node(state: TicketState) -> Dict[str, Any]:
    # Persist fresh LLM predictions into Redis semantic cache.
    if state.error or not state.success:
        return {
            "steps": state.steps + [{"node": "save_cache", "status": "skipped", "reason": "Invalid state"}],
        }

    if not state.fresh_results or not state.uncached_tickets:
        return {
            "steps": state.steps + [{"node": "save_cache", "status": "skipped", "reason": "No fresh results"}],
        }

    pending_ticket_map = {ticket.index: ticket for ticket in state.uncached_tickets}

    try:
        for fresh_result in state.fresh_results:
            pending_ticket = pending_ticket_map.get(fresh_result.index)
            if pending_ticket is None:
                continue

            await save_prediction_cache(
                title=pending_ticket.title,
                description=pending_ticket.description,
                title_embedding=pending_ticket.title_embedding,
                description_embedding=pending_ticket.description_embedding,
                result=fresh_result.result,
            )

        return {
            "steps": state.steps + [{
                "node": "save_cache",
                "status": "success",
                "saved_count": len(state.fresh_results),
            }],
        }
    except Exception as error:
        return {
            "steps": state.steps + [{"node": "save_cache", "status": "error", "error": str(error)}],
        }


async def callback_node(state: TicketState) -> Dict[str, Any]:
    # Send callback results to the backend with an HMAC signature header.
    callback_url = f"{settings.BASE_BACKEND_URL}/api/v1/create-bulk"
    payload: list[dict[str, Any]] = []
    department_mapping: Dict[str, str] = {}

    if state.error or not state.success or not state.data:
        tickets_list = _get_tickets_from_state(state)
        error_message = str(state.error) if state.error else "Failed to process ticket"

        for ticket in tickets_list:
            payload.append({
                "department_id": None,
                "form_id": state.form_id,
                "description": ticket.description,
                "message": error_message,
                "priority": None,
                "status": "failed",
                "title": ticket.title,
            })
    else:
        has_routing_result = any(
            (
                (item.priority.value if hasattr(item.priority, "value") else item.priority) not in (None, "", "null")
                or getattr(item, "department_name", "") not in (None, "", "null")
            )
            for item in state.data
        )

        if not has_routing_result:
            return {
                "callback_response": {
                    "status": "Skipped",
                    "status_code": 204,
                    "message": "No routing fields in data; callback skipped",
                }
            }

        departments = await get_department(state.company_id)
        department_mapping = _extract_department_mapping(departments)

        for item in state.data:
            priority_value = item.priority.value if hasattr(item.priority, "value") else item.priority
            department_name = getattr(item, "department_name", "")

            if priority_value in (None, "", "null") and department_name in (None, "", "null"):
                continue

            mapped_department_id = department_mapping.get(_normalize_department_name(department_name), "")
            payload.append({
                "department_id": mapped_department_id,
                "form_id": state.form_id,
                "description": item.description,
                "message": "Processed successfully" if mapped_department_id else f"Department '{department_name}' not found",
                "priority": priority_value,
                "status": "success" if mapped_department_id else "failed",
                "title": item.title,
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
        request_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        signature = generate_hmac(body=request_body, secret=settings.SECRET_API_KEY)
        headers = {
            "Content-Type": "application/json",
            SIGNATURE_HEADER: f"sha256={signature}",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                callback_url,
                content=request_body,
                headers=headers,
            )

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
    except Exception as error:
        return {
            "callback_response": {"status": "Failed", "error": str(error)},
        }
