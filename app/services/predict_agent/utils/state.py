from typing import Optional,List,Dict,Any
from pydantic import Field,BaseModel
from app.schemas.predict_ticket_schema import PriorityEnum,DepartmentEnum

class LLMPredictOutput(BaseModel):
    department_name: DepartmentEnum = Field(..., description="ชื่อแผนกที่เหมาะสมที่สุดสำหรับจัดการปัญหาใน Ticket นี้")
    priority: PriorityEnum = Field(..., description="ระดับความสำคัญของปัญหา (low, medium, high, urgent)")

class TicketState(BaseModel):
    # ข้อมูลที่ได้รับมาจาก Route
    form_id: str = Field(...,description="form_id ที่ส่งมาจาก backend ")
    title: str = Field(...,description="title ของ ticket")
    description: str = Field(...,description="description ของ ticket")
    
    # ข้อมูลที่ได้จากการประมวลผลผ่าน LLM
    data: Optional[LLMPredictOutput] = Field(None,description="data ที่ได้จากการประมวลผลผ่าน LLM")
    
    success: bool = Field(True,description="success")
    error: Optional[str] = Field(None,description="error")
    steps: List[Dict[str,Any]] = Field([],description="steps")

    class Config:
        arbitrary_types_allowed = True