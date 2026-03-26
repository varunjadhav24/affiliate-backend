from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.niche import Niche
from app.models.page import Page
from app.schemas.niche import NicheResponse

router = APIRouter(prefix="/sites", tags=["sites"])

def _resp(data: Any, message: str = "OK") -> dict:
    return {"success": True, "data": data, "message": message,
            "timestamp": datetime.utcnow().isoformat()}

def _page_dict(p):
    return {"id": p.id, "niche_id": p.niche_id, "page_type": p.page_type,
            "url": p.url, "status": p.status,
            "published_at": p.published_at.isoformat() if p.published_at else None}

@router.get("")
def list_sites(db: Session = Depends(get_db)):
    niches = (db.query(Niche).join(Page, Page.niche_id == Niche.id)
              .filter(Page.status == "published").distinct().all())
    return _resp([NicheResponse.model_validate(n).model_dump() for n in niches], "Sites fetched")

@router.get("/{niche_id}")
def get_site(niche_id: int, db: Session = Depends(get_db)):
    niche = db.query(Niche).filter(Niche.id == niche_id).first()
    if not niche:
        raise HTTPException(status_code=404, detail="Site not found")
    pages = db.query(Page).filter(Page.niche_id == niche_id).all()
    return _resp({"niche": NicheResponse.model_validate(niche).model_dump(),
                  "pages": [_page_dict(p) for p in pages]}, "Site fetched")

@router.get("/{niche_id}/pages")
def get_site_pages(niche_id: int, db: Session = Depends(get_db)):
    if not db.query(Niche).filter(Niche.id == niche_id).first():
        raise HTTPException(status_code=404, detail="Niche not found")
    return _resp([_page_dict(p) for p in db.query(Page).filter(Page.niche_id == niche_id).all()], "Pages fetched")

@router.post("/{niche_id}/publish")
def publish_site(niche_id: int, db: Session = Depends(get_db)):
    if not db.query(Niche).filter(Niche.id == niche_id).first():
        raise HTTPException(status_code=404, detail="Niche not found")
    from app.tasks.agent_tasks import run_site_builder_agent
    task = run_site_builder_agent.delay(niche_id=niche_id)
    return _resp({"task_id": task.id}, "Site Builder triggered")

@router.post("/{niche_id}/unpublish")
def unpublish_site(niche_id: int, db: Session = Depends(get_db)):
    if not db.query(Niche).filter(Niche.id == niche_id).first():
        raise HTTPException(status_code=404, detail="Niche not found")
    db.query(Page).filter(Page.niche_id == niche_id).update({"status": "unpublished"})
    db.commit()
    return _resp({"niche_id": niche_id}, "Pages unpublished")

@router.post("/{niche_id}/rebuild")
def rebuild_site(niche_id: int, db: Session = Depends(get_db)):
    if not db.query(Niche).filter(Niche.id == niche_id).first():
        raise HTTPException(status_code=404, detail="Niche not found")
    from app.tasks.agent_tasks import run_site_builder_agent
    task = run_site_builder_agent.delay(niche_id=niche_id, rebuild=True)
    return _resp({"task_id": task.id}, "Rebuild triggered")
