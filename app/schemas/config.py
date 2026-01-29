from pydantic import BaseModel
from typing import List, Dict, Any

class ModuleBase(BaseModel):
    code: str
    name: str

class Module(ModuleBase):
    id: str
    class Config:
        from_attributes = True

class TenantModuleResponse(BaseModel):
    code: str
    name: str
    enabled: bool

class ThemeBase(BaseModel):
    name: str
    properties: Dict[str, Any]

class Theme(ThemeBase):
    id: str
    class Config:
        from_attributes = True
