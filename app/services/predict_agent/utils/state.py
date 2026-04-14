from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.predict_ticket_schema import DepartmentEnum, PriorityEnum

class TicketItem(BaseModel):
    title: str
    description: str
    
class TicketPredictResult(BaseModel):
    # department_id: str = Field(..., description="ID ของแผนกที่เหมาะสมที่สุดสำหรับจัดการปัญหาใน Ticket นี้ (อ้างอิง ID จากข้อมูล Available Departments ที่ให้ไป)")
    title: str =  Field(..., description="title ของ ticket")
    description: str = Field(..., description="รายละเอียดของ ticket")
    priority: PriorityEnum = Field(..., description="ระดับความสำคัญของปัญหา (low, medium, high, urgent)")
    department_name: str = Field(..., description="ชื่อแผนกที่เหมาะสมที่สุดสำหรับจัดการปัญหาใน Ticket นี้")
    
class TicketState(BaseModel):
    # ข้อมูลที่ได้รับมาจาก Route
    company_id: str = Field(...,description="company_id ที่ส่งมาจาก backend ")
    form_id: str = Field(...,description="form_id ที่ส่งมาจาก backend ")
    grouped_tickets: List[TicketItem] = Field(default_factory=list, description="payload แบบ grouped ตาม form_id")
    # title: Optional[str] = Field(None,description="title ของ ticket")
    # description: Optional[str] = Field(None,description="description ของ ticket")
    
    # ข้อมูลที่ได้จากการประมวลผลผ่าน LLM
    data: List[TicketPredictResult] = Field(default_factory=list,description="ผลลัพธ์ที่ได้จากการประมวลผลผ่าน LLM ต่อแต่ละ ticket")
    callback_response: Optional[Dict[str,Any]] = Field(None,description="response ที่ได้จากการส่งข้อมูลไปยัง callback URL")
    
    success: bool = Field(True,description="success")
    error: Optional[str] = Field(None,description="error")
    steps: List[Dict[str,Any]] = Field(default_factory=list,description="steps")

    class Config:
        arbitrary_types_allowed = True