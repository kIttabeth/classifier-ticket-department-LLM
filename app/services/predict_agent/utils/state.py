# This module defines the LangGraph state and DTOs for ticket prediction.
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.predict_ticket_schema import PriorityEnum


class TicketItem(BaseModel):
    # Store a single ticket payload that needs routing prediction.
    title: str
    description: str


class TicketPredictResult(BaseModel):
    # Store the final routing prediction result for a single ticket.
    title: str = Field(..., description="Original ticket title")
    description: str = Field(..., description="Original ticket description")
    priority: Optional[PriorityEnum] = Field(
        None,
        description="Predicted ticket priority",
    )
    department_name: Optional[str] = Field(
        None,
        description="Predicted target department name",
    )


class TicketRoutingDecision(BaseModel):
    # Store only the routing fields returned directly from the LLM.
    priority: Optional[PriorityEnum] = Field(
        None,
        description="LLM-predicted priority for the ticket",
    )
    department_name: Optional[str] = Field(
        None,
        description="LLM-predicted department name for the ticket",
    )


class HybridEmbeddingData(BaseModel):
    # Store the hybrid embedding response for one content field.
    dense: List[float] = Field(default_factory=list)
    sparse: Dict[str, Any] = Field(default_factory=dict)


class PendingTicketItem(BaseModel):
    # Store a ticket that still needs LLM prediction plus its embeddings.
    index: int
    title: str
    description: str
    title_embedding: HybridEmbeddingData = Field(default_factory=HybridEmbeddingData)
    description_embedding: HybridEmbeddingData = Field(default_factory=HybridEmbeddingData)


class IndexedTicketPredictResult(BaseModel):
    # Store a prediction result together with its original ticket position.
    index: int
    result: TicketPredictResult


class TicketState(BaseModel):
    # Store the shared LangGraph state for the full ticket prediction flow.
    company_id: str = Field(..., description="company_id sent from backend")
    form_id: str = Field(..., description="form_id sent from backend")
    grouped_tickets: List[TicketItem] = Field(
        default_factory=list,
        description="Grouped tickets for the current form",
    )

    data: List[TicketPredictResult] = Field(
        default_factory=list,
        description="Final ticket routing results",
    )
    cached_results: List[IndexedTicketPredictResult] = Field(
        default_factory=list,
        description="Prediction results loaded from semantic cache",
    )
    fresh_results: List[IndexedTicketPredictResult] = Field(
        default_factory=list,
        description="Fresh LLM results that should be written back to cache",
    )
    uncached_tickets: List[PendingTicketItem] = Field(
        default_factory=list,
        description="Tickets that still require LLM prediction",
    )
    callback_response: Optional[Dict[str, Any]] = Field(
        None,
        description="Response returned from the callback endpoint",
    )

    success: bool = Field(True, description="Whether the workflow is successful")
    error: Optional[str] = Field(None, description="Workflow error message")
    steps: List[Dict[str, Any]] = Field(default_factory=list, description="Workflow steps")

    class Config:
        arbitrary_types_allowed = True
