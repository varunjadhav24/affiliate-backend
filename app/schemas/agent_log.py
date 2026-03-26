from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class AgentLogBase(BaseModel):
    agent_name: str
    action: str
    input_summary: Optional[str] = None
    result_summary: Optional[str] = None

class AgentLogResponse(AgentLogBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    timestamp: datetime
