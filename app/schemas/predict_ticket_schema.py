from enum import Enum
from typing import List

from pydantic import BaseModel

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

class ticket(BaseModel):
    form_id:str
    title:str 
    description:str
    
class predictRequest(BaseModel):
    data:List[ticket]

class predictResponse(BaseModel):
    form_ids: List[str]
    status: int
    message:str
    