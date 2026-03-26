from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class AlertBase(BaseModel):
    type: str
    message: str
    severity: str = "info"
    niche_id: Optional[int] = None
    resolved: bool = False

class AlertResponse(AlertBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
