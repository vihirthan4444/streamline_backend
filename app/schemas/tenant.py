from pydantic import BaseModel
from typing import Optional

class TenantCreate(BaseModel):
    name: str
    business_type: str

class TenantResponse(BaseModel):
    id: str
    name: str
    business_type: str
    class Config:
        from_attributes = True
