from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from app.db.session import SessionLocal
from app.models.page import Page
from app.models.niche import Niche

router = APIRouter()

SKIP_HOSTS = {"api.bestehobby.de", "dashboard.bestehobby.de", "bestehobby.de", "www.bestehobby.de"}

@router.get("/", response_class=HTMLResponse)
async def serve_site(request: Request):
    host = request.headers.get("host", "").split(":")[0]
    if host in SKIP_HOSTS:
        raise HTTPException(status_code=404, detail="Not Found")
    db = SessionLocal()
    try:
        niche = db.query(Niche).filter(Niche.subdomain == host).first()
        if not niche:
            raise HTTPException(status_code=404, detail="Site not found")
        page = db.query(Page).filter(
            Page.niche_id == niche.id,
            Page.page_type == "homepage",
            Page.status == "published"
        ).first()
        if not page or not page.content:
            raise HTTPException(status_code=404, detail="Page not found")
        return HTMLResponse(content=page.content)
    finally:
        db.close()

@router.get("/impressum", response_class=HTMLResponse)
async def serve_impressum(request: Request):
    host = request.headers.get("host", "").split(":")[0]
    db = SessionLocal()
    try:
        niche = db.query(Niche).filter(Niche.subdomain == host).first()
        if not niche:
            raise HTTPException(status_code=404, detail="Not Found")
        page = db.query(Page).filter(
            Page.niche_id == niche.id,
            Page.page_type == "impressum"
        ).first()
        if not page or not page.content:
            raise HTTPException(status_code=404, detail="Not Found")
        return HTMLResponse(content=page.content)
    finally:
        db.close()

@router.get("/datenschutz", response_class=HTMLResponse)
async def serve_datenschutz(request: Request):
    host = request.headers.get("host", "").split(":")[0]
    db = SessionLocal()
    try:
        niche = db.query(Niche).filter(Niche.subdomain == host).first()
        if not niche:
            raise HTTPException(status_code=404, detail="Not Found")
        page = db.query(Page).filter(
            Page.niche_id == niche.id,
            Page.page_type == "datenschutz"
        ).first()
        if not page or not page.content:
            raise HTTPException(status_code=404, detail="Not Found")
        return HTMLResponse(content=page.content)
    finally:
        db.close()
