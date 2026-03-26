from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.agent_log import AgentLog
from app.schemas.agent_log import AgentLogResponse

router = APIRouter(prefix="/agent-logs", tags=["agent-logs"])

def _resp(data: Any, message: str = "OK") -> dict:
    return {"success": True, "data": data, "message": message,
            "timestamp": datetime.utcnow().isoformat()}

@router.get("")
def list_agent_logs(db: Session = Depends(get_db)):
    logs = db.query(AgentLog).order_by(AgentLog.timestamp.desc()).limit(50).all()
    return _resp([AgentLogResponse.model_validate(l).model_dump() for l in logs], "Logs fetched")
