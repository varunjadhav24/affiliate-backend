from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from app.db.session import SessionLocal
from app.models.page import Page
from app.models.niche import Niche

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def serve_site(request: Request):
    host = request.headers.get("host", "").split(":")[0]
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
        return HTMLResponse(content=f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{niche.name} - BesteHobby</title>
<style>body{{font-family:Arial,sans-serif;max-width:900px;margin:0 auto;padding:20px}}h1{{color:#2d6a4f}}</style>
</head>
<body>{page.content}</body>
</html>""")
    finally:
        db.close()
