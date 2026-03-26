from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.campaign import Campaign

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

def _resp(data: Any, message: str = "OK") -> dict:
    return {"success": True, "data": data, "message": message,
            "timestamp": datetime.utcnow().isoformat()}

def _c(c):
    return {"id": c.id, "niche_id": c.niche_id, "google_campaign_id": c.google_campaign_id,
            "status": c.status, "budget": c.budget, "cpc": c.cpc, "ctr": c.ctr, "roas": c.roas,
            "created_at": c.created_at.isoformat() if c.created_at else None}

@router.get("")
def list_campaigns(db: Session = Depends(get_db)):
    return _resp([_c(c) for c in db.query(Campaign).order_by(Campaign.created_at.desc()).all()], "Campaigns fetched")

@router.get("/{campaign_id}")
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c: raise HTTPException(status_code=404, detail="Campaign not found")
    return _resp(_c(c), "Campaign fetched")

@router.post("/{campaign_id}/pause")
def pause_campaign(campaign_id: int, db: Session = Depends(get_db)):
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c: raise HTTPException(status_code=404, detail="Campaign not found")
    c.status = "paused"; db.commit(); db.refresh(c)
    return _resp(_c(c), "Campaign paused")

@router.post("/{campaign_id}/resume")
def resume_campaign(campaign_id: int, db: Session = Depends(get_db)):
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c: raise HTTPException(status_code=404, detail="Campaign not found")
    c.status = "active"; db.commit(); db.refresh(c)
    return _resp(_c(c), "Campaign resumed")
