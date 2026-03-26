from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.agent_log import AgentLog
from app.models.campaign import Campaign

router = APIRouter(prefix="/system", tags=["system"])

AGENT_NAMES = ["ResearchAgent","BusinessCaseAgent","SiteBuilderAgent",
               "LinkBuilderAgent","AdsManagerAgent","ControllerAgent"]

def _resp(data: Any, message: str = "OK") -> dict:
    return {"success": True, "data": data, "message": message,
            "timestamp": datetime.utcnow().isoformat()}

@router.get("/agent-status")
def get_agent_status(db: Session = Depends(get_db)):
    statuses = []
    for name in AGENT_NAMES:
        log = db.query(AgentLog).filter(AgentLog.agent_name == name).order_by(AgentLog.timestamp.desc()).first()
        statuses.append({"agent_name": name, "last_action": log.action if log else None,
                         "last_result": log.result_summary if log else None,
                         "last_run": log.timestamp.isoformat() if log else None,
                         "status": "idle" if not log else "ran"})
    return _resp(statuses, "Agent statuses fetched")

@router.post("/pause-all")
def pause_all(db: Session = Depends(get_db)):
    updated = db.query(Campaign).filter(Campaign.status == "active").update({"status": "paused"})
    db.commit()
    return _resp({"campaigns_paused": updated}, f"Paused {updated} campaign(s)")

@router.post("/run-controller")
def run_controller(db: Session = Depends(get_db)):
    from app.tasks.agent_tasks import run_controller_agent
    task = run_controller_agent.delay()
    return _resp({"task_id": task.id}, "Controller Agent triggered")