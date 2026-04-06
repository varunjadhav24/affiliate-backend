from dotenv import load_dotenv
import os
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from datetime import datetime
import sentry_sdk
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

if settings.SENTRY_DSN:
    sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.2)

app = FastAPI(
    title="Automated Affiliate Growth Platform",
    description="Backend API for the Germany-focused affiliate marketing platform.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.niches import router as niches_router
from app.api.sites import router as sites_router
from app.api.sites_serve import router as sites_serve_router
from app.api.campaigns import router as campaigns_router
from app.api.links import router as links_router
from app.api.alerts import router as alerts_router
from app.api.approvals import router as approvals_router
from app.api.agent_logs import router as agent_logs_router
from app.api.budget import router as budget_router
from app.api.system import router as system_router

API_PREFIX = "/api/v1"
app.include_router(niches_router, prefix=API_PREFIX)
app.include_router(sites_router, prefix=API_PREFIX)
app.include_router(sites_serve_router)
app.include_router(campaigns_router, prefix=API_PREFIX)
app.include_router(links_router, prefix=API_PREFIX)
app.include_router(alerts_router, prefix=API_PREFIX)
app.include_router(approvals_router, prefix=API_PREFIX)
app.include_router(agent_logs_router, prefix=API_PREFIX)
app.include_router(budget_router, prefix=API_PREFIX)
app.include_router(system_router, prefix=API_PREFIX)

@app.get("/health", tags=["health"])
def health_check():
    return {
        "success": True,
        "data": {"status": "ok"},
        "message": "Server is running",
        "timestamp": datetime.utcnow().isoformat(),
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
