from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class NicheBase(BaseModel):
    name: str
    subdomain: Optional[str] = None
    score: Optional[float] = None
    status: str = "discovered"
    go_no_go: Optional[str] = None
    recommended_budget: Optional[float] = None

class NicheCreate(NicheBase):
    pass

class NicheUpdate(BaseModel):
    name: Optional[str] = None
    subdomain: Optional[str] = None
    score: Optional[float] = None
    status: Optional[str] = None
    go_no_go: Optional[str] = None
    recommended_budget: Optional[float] = None

class NicheResponse(NicheBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
