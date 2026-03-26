from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.affiliate_link import AffiliateLink
from app.models.niche import Niche

router = APIRouter(prefix="/links", tags=["links"])

def _resp(data: Any, message: str = "OK") -> dict:
    return {"success": True, "data": data, "message": message,
            "timestamp": datetime.utcnow().isoformat()}

def _l(lnk):
    return {"id": lnk.id, "niche_id": lnk.niche_id, "product_name": lnk.product_name,
            "asin": lnk.asin, "link_url": lnk.link_url, "price": lnk.price,
            "rating": lnk.rating, "status": lnk.status,
            "last_checked": lnk.last_checked.isoformat() if lnk.last_checked else None}

@router.get("/all")
def list_all_links(db: Session = Depends(get_db)):
    """Get all affiliate links across all niches."""
    from app.models.niche import Niche
    links = db.query(AffiliateLink).all()
    result = []
    for lnk in links:
        niche = db.query(Niche).filter(Niche.id == lnk.niche_id).first()
        result.append({
            "id": lnk.id,
            "niche_id": lnk.niche_id,
            "niche_name": niche.name if niche else None,
            "product_name": lnk.product_name,
            "asin": lnk.asin,
            "link_url": lnk.link_url,
            "price": lnk.price,
            "rating": lnk.rating,
            "status": lnk.status,
            "last_checked": lnk.last_checked.isoformat() if lnk.last_checked else None,
        })
    return _resp(result, "All affiliate links fetched")

@router.get("/{niche_id}")
def list_links(niche_id: int, db: Session = Depends(get_db)):
    if not db.query(Niche).filter(Niche.id == niche_id).first():
        raise HTTPException(status_code=404, detail="Niche not found")
    return _resp([_l(lnk) for lnk in db.query(AffiliateLink).filter(AffiliateLink.niche_id == niche_id).all()], "Links fetched")

@router.post("/{niche_id}/refresh")
def refresh_links(niche_id: int, db: Session = Depends(get_db)):
    if not db.query(Niche).filter(Niche.id == niche_id).first():
        raise HTTPException(status_code=404, detail="Niche not found")
    from app.tasks.agent_tasks import run_link_builder_agent
    task = run_link_builder_agent.delay(niche_id=niche_id)
    return _resp({"task_id": task.id}, "Link Builder triggered")
