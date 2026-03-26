from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.niche import Niche
from app.schemas.niche import NicheResponse

router = APIRouter(prefix="/niches", tags=["niches"])

def _resp(data: Any, message: str = "OK") -> dict:
    return {"success": True, "data": data, "message": message,
            "timestamp": datetime.utcnow().isoformat()}

@router.get("")
def list_niches(db: Session = Depends(get_db)):
    niches = db.query(Niche).order_by(Niche.created_at.desc()).all()
    return _resp([NicheResponse.model_validate(n).model_dump() for n in niches], "Niches fetched")

@router.get("/{niche_id}")
def get_niche(niche_id: int, db: Session = Depends(get_db)):
    niche = db.query(Niche).filter(Niche.id == niche_id).first()
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")
    return _resp(NicheResponse.model_validate(niche).model_dump(), "Niche fetched")

@router.post("/discover")
def discover_niches():
    from app.tasks.agent_tasks import run_research_agent
    task = run_research_agent.delay()
    return _resp({"task_id": task.id}, "Research agent triggered")

@router.post("/{niche_id}/approve")
def approve_niche(niche_id: int, db: Session = Depends(get_db)):
    niche = db.query(Niche).filter(Niche.id == niche_id).first()
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")
    niche.status = "approved"
    niche.go_no_go = "go"
    db.commit(); db.refresh(niche)
    return _resp(NicheResponse.model_validate(niche).model_dump(), "Niche approved")

@router.post("/{niche_id}/reject")
def reject_niche(niche_id: int, db: Session = Depends(get_db)):
    niche = db.query(Niche).filter(Niche.id == niche_id).first()
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")
    niche.status = "rejected"
    niche.go_no_go = "no_go"
    db.commit(); db.refresh(niche)
    return _resp(NicheResponse.model_validate(niche).model_dump(), "Niche rejected")

@router.get("/{niche_id}/business-case")
def get_business_case(niche_id: int, db: Session = Depends(get_db)):
    niche = db.query(Niche).filter(Niche.id == niche_id).first()
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")
    return _resp({"niche_id": niche_id, "niche_name": niche.name,
                  "recommended_budget": niche.recommended_budget, "score": niche.score,
                  "go_no_go": niche.go_no_go, "estimated_monthly_revenue": None,
                  "estimated_roas": None, "notes": "Populated by Business Case Agent."}, "Business case fetched")

@router.post("/{niche_id}/run-business-case")
def run_business_case(niche_id: int, db: Session = Depends(get_db)):
    niche = db.query(Niche).filter(Niche.id == niche_id).first()
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")
    from app.tasks.agent_tasks import run_business_case_agent
    task = run_business_case_agent.delay(niche_id=niche_id)
    return _resp({"task_id": task.id, "niche_id": niche_id}, "Business Case Agent triggered")

@router.post("/{niche_id}/publish")
def publish_niche_site(niche_id: int, db: Session = Depends(get_db)):
    niche = db.query(Niche).filter(Niche.id == niche_id).first()
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")
    from app.tasks.agent_tasks import run_site_builder_agent
    task = run_site_builder_agent.delay(niche_id=niche_id)
    return _resp({"task_id": task.id, "niche_id": niche_id}, "Site Builder Agent triggered")