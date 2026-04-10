from pydantic import BaseModel
from enum import Enum

class PriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class DepartmentEnum(str,Enum):
    Frontend = "Frontend"
    Backend = "Backend"
    UXUI = "UXUI"
    Business_Analyst = "Business Analyst"
    QA = "QA"
    IOT = "IOT"
    OTHER = "OTHER"

class predictRequest(BaseModel):
    from_id:str
    title:str 
    description:str

class predictResponse(BaseModel):
    form_id:str
    status: int
    message:str
    