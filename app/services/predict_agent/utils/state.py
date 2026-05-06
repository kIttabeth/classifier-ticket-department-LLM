# This module defines the LangGraph state and DTOs for ticket prediction.
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.predict_ticket_schema import PriorityEnum


class TicketItem(BaseModel):
    # Store a single ticket payload that needs routing prediction.
    title: str
    description: str


class TicketPredictResult(BaseModel):
    # Store the routing prediction result for a single ticket.
    title: str = Field(..., description="title ของ ticket")
    description: str = Field(..., description="รายละเอียดของ ticket")
    priority: Optional[PriorityEnum] = Field(
        None,
        description="ระดับความสำคัญของปัญหา (low, medium, high, urgent)",
    )
    department_name: Optional[str] = Field(
        None,
        description="ชื่อแผนกที่เหมาะสมที่สุดสำหรับจัดการ ticket นี้",
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
    company_id: str = Field(..., description="company_id ที่ส่งมาจาก backend")
    form_id: str = Field(..., description="form_id ที่ส่งมาจาก backend")
    grouped_tickets: List[TicketItem] = Field(
        default_factory=list,
        description="payload แบบ grouped ตาม link_id",
    )

    data: List[TicketPredictResult] = Field(
        default_factory=list,
        description="ผลลัพธ์สุดท้ายของการจัดหมวดหมู่ ticket",
    )
    cached_results: List[IndexedTicketPredictResult] = Field(
        default_factory=list,
        description="ผลลัพธ์ที่ดึงได้จาก semantic cache",
    )
    fresh_results: List[IndexedTicketPredictResult] = Field(
        default_factory=list,
        description="ผลลัพธ์ใหม่จาก LLM ที่ต้องบันทึกลง cache",
    )
    uncached_tickets: List[PendingTicketItem] = Field(
        default_factory=list,
        description="tickets ที่ยังไม่พบ semantic cache",
    )
    callback_response: Optional[Dict[str, Any]] = Field(
        None,
        description="response ที่ได้จากการส่งข้อมูลไปยัง callback URL",
    )

    success: bool = Field(True, description="success")
    error: Optional[str] = Field(None, description="error")
    steps: List[Dict[str, Any]] = Field(default_factory=list, description="steps")

    class Config:
        arbitrary_types_allowed = True
