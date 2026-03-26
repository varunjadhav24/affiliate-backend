from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ApprovalBase(BaseModel):
    action_type: str
    description: str
    niche_id: Optional[int] = None
    status: str = "pending"

class ApprovalResponse(ApprovalBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
