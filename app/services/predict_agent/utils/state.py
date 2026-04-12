from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.predict_ticket_schema import DepartmentEnum, PriorityEnum

class LLMPredictOutput(BaseModel):
    department_name: DepartmentEnum = Field(..., description="ชื่อแผนกที่เหมาะสมที่สุดสำหรับจัดการปัญหาใน Ticket นี้")
    priority: PriorityEnum = Field(..., description="ระดับความสำคัญของปัญหา (low, medium, high, urgent)")


class TicketPredictResult(BaseModel):
    title: str
    description: str
    prediction: LLMPredictOutput

class TicketItem(BaseModel):
    title: str
    description: str
class TicketState(BaseModel):
    # ข้อมูลที่ได้รับมาจาก Route
    form_id: str = Field(...,description="form_id ที่ส่งมาจาก backend ")
    grouped_tickets: List[TicketItem] = Field(default_factory=list, description="payload แบบ grouped ตาม form_id")
    title: Optional[str] = Field(None,description="title ของ ticket")
    description: Optional[str] = Field(None,description="description ของ ticket")
    
    # ข้อมูลที่ได้จากการประมวลผลผ่าน LLM
    data: List[TicketPredictResult] = Field(default_factory=list,description="ผลลัพธ์ที่ได้จากการประมวลผลผ่าน LLM ต่อแต่ละ ticket")
    callback_response: Optional[Dict[str,Any]] = Field(None,description="response ที่ได้จากการส่งข้อมูลไปยัง callback URL")
    
    success: bool = Field(True,description="success")
    error: Optional[str] = Field(None,description="error")
    steps: List[Dict[str,Any]] = Field(default_factory=list,description="steps")

    class Config:
        arbitrary_types_allowed = True