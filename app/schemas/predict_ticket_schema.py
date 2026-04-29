from enum import Enum
from typing import List

from pydantic import BaseModel

class PriorityEnum(str,Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

# class DepartmentEnum(str,Enum):
#     Frontend = "Frontend"
#     Backend = "Backend"
#     UXUI = "UXUI"
#     Business_Analyst = "Business Analyst"
#     QA = "QA"
#     IOT = "IOT"
#     OTHER = "OTHER"

class formItem(BaseModel):
    id: str
    title: str 
    description: str

class companyData(BaseModel):
    company_id: str
    forms: List[formItem]

class predictRequest(BaseModel):
    data: List[companyData]

class predictResponse(BaseModel):
    # form_ids: List[str]
    message:str
    queued_count: int    