"""
Run this script from inside your backend/ folder:
    python bootstrap.py

It will write all files with their full content.
"""

import os

files = {}

# ── alembic.ini ──────────────────────────────────────────────────────────────
files["alembic.ini"] = """[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/affiliate_db

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""

# ── .env.example ─────────────────────────────────────────────────────────────
files[".env.example"] = """DATABASE_URL=postgresql://postgres:postgres@localhost:5432/affiliate_db
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-...
SERPAPI_KEY=your-serpapi-key
GOOGLE_ADS_DEVELOPER_TOKEN=your-developer-token
GOOGLE_ADS_CLIENT_ID=your-oauth2-client-id
GOOGLE_ADS_CLIENT_SECRET=your-oauth2-client-secret
GOOGLE_ADS_REFRESH_TOKEN=your-refresh-token
GOOGLE_ADS_LOGIN_CUSTOMER_ID=1234567890
AMAZON_ACCESS_KEY=your-amazon-access-key
AMAZON_SECRET_KEY=your-amazon-secret-key
AMAZON_PARTNER_TAG=your-associate-tag-21
AMAZON_HOST=webservices.amazon.de
AMAZON_REGION=eu-west-1
GA4_PROPERTY_ID=properties/123456789
DNS_PROVIDER_API_KEY=your-dns-api-key
DNS_BASE_DOMAIN=yourdomain.com
SENTRY_DSN=
SECRET_KEY=change-me-to-a-long-random-string
"""

# ── requirements.txt ─────────────────────────────────────────────────────────
files["requirements.txt"] = """fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.30
alembic==1.13.1
psycopg2-binary==2.9.9
redis==5.0.4
celery==5.4.0
celery[redis]==5.4.0
pydantic==2.7.1
pydantic-settings==2.2.1
langchain==0.2.1
langchain-core==0.2.43
langgraph==0.1.1
langchain-openai==0.1.8
openai==1.30.1
sentry-sdk[fastapi]==2.3.1
python-dotenv==1.0.1
httpx==0.27.0
google-ads==24.1.0
boto3==1.34.110
requests==2.32.2
python-multipart==0.0.9
"""

# ── celery_app.py ─────────────────────────────────────────────────────────────
files["celery_app.py"] = """from celery import Celery
from app.core.config import settings
from app.tasks.scheduler import CELERYBEAT_SCHEDULE

celery_app = Celery(
    "affiliate_platform",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.agent_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule=CELERYBEAT_SCHEDULE,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=86400,
)
"""

# ── main.py ───────────────────────────────────────────────────────────────────
files["main.py"] = """from datetime import datetime
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
"""

# ── alembic/env.py ────────────────────────────────────────────────────────────
files["alembic/env.py"] = """import os, sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.db.base import Base
import app.models  # noqa — triggers all model imports

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata,
                      literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.", poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata,
                          compare_type=True)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"""

# ── alembic/script.py.mako ───────────────────────────────────────────────────
files["alembic/script.py.mako"] = '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}

def upgrade() -> None:
    ${upgrades if upgrades else "pass"}

def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'''

# ── app/__init__.py ───────────────────────────────────────────────────────────
files["app/__init__.py"] = ""

# ── app/core/__init__.py ──────────────────────────────────────────────────────
files["app/core/__init__.py"] = ""

# ── app/core/config.py ────────────────────────────────────────────────────────
files["app/core/config.py"] = """from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",
                                      case_sensitive=True, extra="ignore")
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/affiliate_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    OPENAI_API_KEY: str = ""
    SERPAPI_KEY: str = ""
    GOOGLE_ADS_DEVELOPER_TOKEN: str = ""
    GOOGLE_ADS_CLIENT_ID: str = ""
    GOOGLE_ADS_CLIENT_SECRET: str = ""
    GOOGLE_ADS_REFRESH_TOKEN: str = ""
    GOOGLE_ADS_LOGIN_CUSTOMER_ID: str = ""
    AMAZON_ACCESS_KEY: str = ""
    AMAZON_SECRET_KEY: str = ""
    AMAZON_PARTNER_TAG: str = ""
    AMAZON_HOST: str = "webservices.amazon.de"
    AMAZON_REGION: str = "eu-west-1"
    GA4_PROPERTY_ID: str = ""
    DNS_PROVIDER_API_KEY: str = ""
    DNS_BASE_DOMAIN: str = "example.com"
    SENTRY_DSN: str = ""
    SECRET_KEY: str = "change-me-in-production"

settings = Settings()
"""

# ── app/db/__init__.py ────────────────────────────────────────────────────────
files["app/db/__init__.py"] = ""

# ── app/db/base.py ────────────────────────────────────────────────────────────
files["app/db/base.py"] = """from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
"""

# ── app/db/session.py ─────────────────────────────────────────────────────────
files["app/db/session.py"] = """from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""

# ── app/models/__init__.py ────────────────────────────────────────────────────
files["app/models/__init__.py"] = """from app.models.niche import Niche
from app.models.page import Page
from app.models.affiliate_link import AffiliateLink
from app.models.campaign import Campaign
from app.models.agent_log import AgentLog
from app.models.alert import Alert
from app.models.budget_allocation import BudgetAllocation
from app.models.approval import Approval

__all__ = ["Niche","Page","AffiliateLink","Campaign","AgentLog","Alert","BudgetAllocation","Approval"]
"""

# ── app/models/niche.py ───────────────────────────────────────────────────────
files["app/models/niche.py"] = """from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from sqlalchemy.orm import relationship
from app.db.base import Base

class Niche(Base):
    __tablename__ = "niches"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    subdomain = Column(String(100), nullable=True, unique=True)
    score = Column(Float, nullable=True)
    status = Column(String(50), nullable=False, default="discovered")
    go_no_go = Column(String(10), nullable=True)
    recommended_budget = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    pages = relationship("Page", back_populates="niche", cascade="all, delete-orphan")
    affiliate_links = relationship("AffiliateLink", back_populates="niche", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="niche", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="niche", cascade="all, delete-orphan")
    budget_allocations = relationship("BudgetAllocation", back_populates="niche", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="niche", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_niches_status", "status"),
        Index("ix_niches_go_no_go", "go_no_go"),
        Index("ix_niches_created_at", "created_at"),
    )
"""

# ── app/models/page.py ────────────────────────────────────────────────────────
files["app/models/page.py"] = """from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.base import Base

class Page(Base):
    __tablename__ = "pages"
    id = Column(Integer, primary_key=True, index=True)
    niche_id = Column(Integer, ForeignKey("niches.id", ondelete="CASCADE"), nullable=False)
    page_type = Column(String(50), nullable=False)
    url = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default="draft")
    niche = relationship("Niche", back_populates="pages")
    __table_args__ = (
        Index("ix_pages_niche_id", "niche_id"),
        Index("ix_pages_status", "status"),
    )
"""

# ── app/models/affiliate_link.py ──────────────────────────────────────────────
files["app/models/affiliate_link.py"] = """from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.base import Base

class AffiliateLink(Base):
    __tablename__ = "affiliate_links"
    id = Column(Integer, primary_key=True, index=True)
    niche_id = Column(Integer, ForeignKey("niches.id", ondelete="CASCADE"), nullable=False)
    product_name = Column(String(500), nullable=False)
    asin = Column(String(20), nullable=True)
    link_url = Column(String(1000), nullable=False)
    price = Column(Float, nullable=True)
    rating = Column(Float, nullable=True)
    status = Column(String(50), nullable=False, default="active")
    last_checked = Column(DateTime, nullable=True)
    niche = relationship("Niche", back_populates="affiliate_links")
    __table_args__ = (
        Index("ix_affiliate_links_niche_id", "niche_id"),
        Index("ix_affiliate_links_status", "status"),
    )
"""

# ── app/models/campaign.py ────────────────────────────────────────────────────
files["app/models/campaign.py"] = """from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.base import Base

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True, index=True)
    niche_id = Column(Integer, ForeignKey("niches.id", ondelete="CASCADE"), nullable=False)
    google_campaign_id = Column(String(100), nullable=True, unique=True)
    status = Column(String(50), nullable=False, default="draft")
    budget = Column(Float, nullable=True)
    cpc = Column(Float, nullable=True)
    ctr = Column(Float, nullable=True)
    roas = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    niche = relationship("Niche", back_populates="campaigns")
    __table_args__ = (
        Index("ix_campaigns_niche_id", "niche_id"),
        Index("ix_campaigns_status", "status"),
    )
"""

# ── app/models/agent_log.py ───────────────────────────────────────────────────
files["app/models/agent_log.py"] = """from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from app.db.base import Base

class AgentLog(Base):
    __tablename__ = "agent_logs"
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(100), nullable=False)
    action = Column(String(255), nullable=False)
    input_summary = Column(Text, nullable=True)
    result_summary = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (
        Index("ix_agent_logs_agent_name", "agent_name"),
        Index("ix_agent_logs_timestamp", "timestamp"),
    )
"""

# ── app/models/alert.py ───────────────────────────────────────────────────────
files["app/models/alert.py"] = """from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.base import Base

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, default="info")
    niche_id = Column(Integer, ForeignKey("niches.id", ondelete="SET NULL"), nullable=True)
    resolved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    niche = relationship("Niche", back_populates="alerts")
    __table_args__ = (
        Index("ix_alerts_resolved", "resolved"),
        Index("ix_alerts_severity", "severity"),
        Index("ix_alerts_niche_id", "niche_id"),
    )
"""

# ── app/models/budget_allocation.py ──────────────────────────────────────────
files["app/models/budget_allocation.py"] = """from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.base import Base

class BudgetAllocation(Base):
    __tablename__ = "budget_allocations"
    id = Column(Integer, primary_key=True, index=True)
    niche_id = Column(Integer, ForeignKey("niches.id", ondelete="CASCADE"), nullable=False)
    allocated = Column(Float, nullable=False, default=0.0)
    spent = Column(Float, nullable=False, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    niche = relationship("Niche", back_populates="budget_allocations")
    __table_args__ = (Index("ix_budget_allocations_niche_id", "niche_id"),)
"""

# ── app/models/approval.py ────────────────────────────────────────────────────
files["app/models/approval.py"] = """from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.base import Base

class Approval(Base):
    __tablename__ = "approvals"
    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    niche_id = Column(Integer, ForeignKey("niches.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    niche = relationship("Niche", back_populates="approvals")
    __table_args__ = (
        Index("ix_approvals_status", "status"),
        Index("ix_approvals_niche_id", "niche_id"),
    )
"""

# ── app/schemas/__init__.py ───────────────────────────────────────────────────
files["app/schemas/__init__.py"] = """from app.schemas.niche import NicheBase, NicheCreate, NicheUpdate, NicheResponse
from app.schemas.agent_log import AgentLogBase, AgentLogResponse
from app.schemas.alert import AlertBase, AlertResponse
from app.schemas.approval import ApprovalBase, ApprovalResponse
"""

# ── app/schemas/niche.py ──────────────────────────────────────────────────────
files["app/schemas/niche.py"] = """from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class NicheBase(BaseModel):
    name: str
    subdomain: Optional[str] = None
    score: Optional[float] = None
    status: str = "discovered"
    go_no_go: Optional[str] = None
    recommended_budget: Optional[float] = None

class NicheCreate(NicheBase):
    pass

class NicheUpdate(BaseModel):
    name: Optional[str] = None
    subdomain: Optional[str] = None
    score: Optional[float] = None
    status: Optional[str] = None
    go_no_go: Optional[str] = None
    recommended_budget: Optional[float] = None

class NicheResponse(NicheBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
"""

# ── app/schemas/agent_log.py ──────────────────────────────────────────────────
files["app/schemas/agent_log.py"] = """from datetime import datetime
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
"""

# ── app/schemas/alert.py ──────────────────────────────────────────────────────
files["app/schemas/alert.py"] = """from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class AlertBase(BaseModel):
    type: str
    message: str
    severity: str = "info"
    niche_id: Optional[int] = None
    resolved: bool = False

class AlertResponse(AlertBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
"""

# ── app/schemas/approval.py ───────────────────────────────────────────────────
files["app/schemas/approval.py"] = """from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ApprovalBase(BaseModel):
    action_type: str
    description: str
    niche_id: Optional[int] = None
    status: str = "pending"

class ApprovalResponse(ApprovalBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
"""

# ── app/api/__init__.py ───────────────────────────────────────────────────────
files["app/api/__init__.py"] = ""

# ── app/api/niches.py ─────────────────────────────────────────────────────────
files["app/api/niches.py"] = """from datetime import datetime
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
"""

# ── app/api/sites.py ──────────────────────────────────────────────────────────
files["app/api/sites.py"] = """from datetime import datetime
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
"""

# ── app/api/campaigns.py ──────────────────────────────────────────────────────
files["app/api/campaigns.py"] = """from datetime import datetime
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
"""

# ── app/api/links.py ──────────────────────────────────────────────────────────
files["app/api/links.py"] = """from datetime import datetime
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
"""

# ── app/api/alerts.py ─────────────────────────────────────────────────────────
files["app/api/alerts.py"] = """from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])

def _resp(data: Any, message: str = "OK") -> dict:
    return {"success": True, "data": data, "message": message,
            "timestamp": datetime.utcnow().isoformat()}

@router.get("")
def list_alerts(db: Session = Depends(get_db)):
    alerts = db.query(Alert).filter(Alert.resolved == False).order_by(Alert.created_at.desc()).all()
    return _resp([AlertResponse.model_validate(a).model_dump() for a in alerts], "Alerts fetched")

@router.patch("/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert: raise HTTPException(status_code=404, detail="Alert not found")
    alert.resolved = True; db.commit(); db.refresh(alert)
    return _resp(AlertResponse.model_validate(alert).model_dump(), "Alert resolved")
"""

# ── app/api/approvals.py ──────────────────────────────────────────────────────
files["app/api/approvals.py"] = """from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.approval import Approval
from app.schemas.approval import ApprovalResponse

router = APIRouter(prefix="/approvals", tags=["approvals"])

def _resp(data: Any, message: str = "OK") -> dict:
    return {"success": True, "data": data, "message": message,
            "timestamp": datetime.utcnow().isoformat()}

@router.get("")
def list_approvals(db: Session = Depends(get_db)):
    approvals = db.query(Approval).filter(Approval.status == "pending").order_by(Approval.created_at.desc()).all()
    return _resp([ApprovalResponse.model_validate(a).model_dump() for a in approvals], "Approvals fetched")

@router.post("/{approval_id}/approve")
def approve_action(approval_id: int, db: Session = Depends(get_db)):
    a = db.query(Approval).filter(Approval.id == approval_id).first()
    if not a: raise HTTPException(status_code=404, detail="Approval not found")
    if a.status != "pending": raise HTTPException(status_code=400, detail=f"Already {a.status}")
    a.status = "approved"; db.commit(); db.refresh(a)
    return _resp(ApprovalResponse.model_validate(a).model_dump(), "Approved")

@router.post("/{approval_id}/reject")
def reject_action(approval_id: int, db: Session = Depends(get_db)):
    a = db.query(Approval).filter(Approval.id == approval_id).first()
    if not a: raise HTTPException(status_code=404, detail="Approval not found")
    if a.status != "pending": raise HTTPException(status_code=400, detail=f"Already {a.status}")
    a.status = "rejected"; db.commit(); db.refresh(a)
    return _resp(ApprovalResponse.model_validate(a).model_dump(), "Rejected")
"""

# ── app/api/agent_logs.py ─────────────────────────────────────────────────────
files["app/api/agent_logs.py"] = """from datetime import datetime
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
"""

# ── app/api/budget.py ─────────────────────────────────────────────────────────
files["app/api/budget.py"] = """from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.budget_allocation import BudgetAllocation
from app.models.niche import Niche

router = APIRouter(prefix="/budget-allocations", tags=["budget"])

def _resp(data: Any, message: str = "OK") -> dict:
    return {"success": True, "data": data, "message": message,
            "timestamp": datetime.utcnow().isoformat()}

@router.get("")
def list_budget_allocations(db: Session = Depends(get_db)):
    result = []
    for alloc in db.query(BudgetAllocation).all():
        niche = db.query(Niche).filter(Niche.id == alloc.niche_id).first()
        result.append({"id": alloc.id, "niche_id": alloc.niche_id,
                       "niche_name": niche.name if niche else None,
                       "allocated": alloc.allocated, "spent": alloc.spent,
                       "remaining": round(alloc.allocated - alloc.spent, 2),
                       "utilization_pct": round((alloc.spent / alloc.allocated) * 100, 1) if alloc.allocated > 0 else 0.0,
                       "updated_at": alloc.updated_at.isoformat() if alloc.updated_at else None})
    return _resp(result, "Budget allocations fetched")
"""

# ── app/api/system.py ─────────────────────────────────────────────────────────
files["app/api/system.py"] = """from datetime import datetime
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
"""

# ── app/agents/__init__.py ────────────────────────────────────────────────────
files["app/agents/__init__.py"] = """from app.agents.research_agent import ResearchAgent
from app.agents.business_case_agent import BusinessCaseAgent
from app.agents.site_builder_agent import SiteBuilderAgent
from app.agents.link_builder_agent import LinkBuilderAgent
from app.agents.ads_manager_agent import AdsManagerAgent
from app.agents.controller_agent import ControllerAgent
"""

# ── app/agents/base.py ────────────────────────────────────────────────────────
files["app/agents/base.py"] = """from typing import Any, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph

class AgentState(TypedDict, total=False):
    niche_id: Optional[int]
    niche_name: Optional[str]
    subdomain: Optional[str]
    keyword_data: Optional[list]
    trend_data: Optional[list]
    competition_score: Optional[float]
    search_volume: Optional[int]
    recommended_budget: Optional[float]
    estimated_roas: Optional[float]
    estimated_monthly_revenue: Optional[float]
    go_no_go: Optional[str]
    score: Optional[float]
    pages_generated: Optional[list]
    pages_published: Optional[int]
    affiliate_products: Optional[list]
    links_created: Optional[int]
    campaign_id: Optional[str]
    campaign_status: Optional[str]
    budget_allocated: Optional[float]
    error: Optional[str]
    messages: Optional[list]
    next_action: Optional[str]
    completed: bool

class BaseAgent:
    name: str = "BaseAgent"
    def __init__(self):
        self.graph = None
    def build(self):
        raise NotImplementedError
    def run(self, initial_state: AgentState) -> AgentState:
        if self.graph is None:
            self.graph = self.build()
        return self.graph.invoke(initial_state)
"""

# ── app/agents/research_agent.py ─────────────────────────────────────────────
files["app/agents/research_agent.py"] = """from langgraph.graph import StateGraph, END
from app.agents.base import AgentState, BaseAgent

def fetch_keyword_data(state):
    print("[ResearchAgent] fetch_keyword_data — stub")
    state["keyword_data"] = []
    state["messages"] = state.get("messages", []) + ["keyword_data fetched (stub)"]
    return state

def fetch_trend_data(state):
    print("[ResearchAgent] fetch_trend_data — stub")
    state["trend_data"] = []
    state["messages"] = state.get("messages", []) + ["trend_data fetched (stub)"]
    return state

def analyse_competition(state):
    print("[ResearchAgent] analyse_competition — stub")
    state["competition_score"] = 0.0
    state["search_volume"] = 0
    state["messages"] = state.get("messages", []) + ["competition analysed (stub)"]
    return state

def rank_niches(state):
    print("[ResearchAgent] rank_niches — stub")
    state["score"] = 0.0
    state["completed"] = True
    state["messages"] = state.get("messages", []) + ["niches ranked (stub)"]
    return state

def handle_error(state):
    print(f"[ResearchAgent] ERROR: {state.get('error')}")
    state["completed"] = True
    return state

class ResearchAgent(BaseAgent):
    name = "ResearchAgent"
    def build(self):
        g = StateGraph(AgentState)
        g.add_node("fetch_keyword_data", fetch_keyword_data)
        g.add_node("fetch_trend_data", fetch_trend_data)
        g.add_node("analyse_competition", analyse_competition)
        g.add_node("rank_niches", rank_niches)
        g.add_node("handle_error", handle_error)
        g.set_entry_point("fetch_keyword_data")
        g.add_edge("fetch_keyword_data", "fetch_trend_data")
        g.add_edge("fetch_trend_data", "analyse_competition")
        g.add_edge("analyse_competition", "rank_niches")
        g.add_edge("rank_niches", END)
        g.add_edge("handle_error", END)
        return g.compile()
"""

# ── app/agents/business_case_agent.py ────────────────────────────────────────
files["app/agents/business_case_agent.py"] = """from langgraph.graph import StateGraph, END
from app.agents.base import AgentState, BaseAgent

def gather_market_data(state):
    state["messages"] = state.get("messages", []) + ["market data gathered (stub)"]
    return state

def compute_financials(state):
    state["estimated_monthly_revenue"] = 0.0
    state["estimated_roas"] = 0.0
    state["messages"] = state.get("messages", []) + ["financials computed (stub)"]
    return state

def recommend_budget(state):
    state["recommended_budget"] = 0.0
    state["messages"] = state.get("messages", []) + ["budget recommended (stub)"]
    return state

def make_go_no_go(state):
    state["go_no_go"] = "no_go"
    state["completed"] = True
    state["messages"] = state.get("messages", []) + ["go/no-go decided (stub)"]
    return state

class BusinessCaseAgent(BaseAgent):
    name = "BusinessCaseAgent"
    def build(self):
        g = StateGraph(AgentState)
        g.add_node("gather_market_data", gather_market_data)
        g.add_node("compute_financials", compute_financials)
        g.add_node("recommend_budget", recommend_budget)
        g.add_node("make_go_no_go", make_go_no_go)
        g.set_entry_point("gather_market_data")
        g.add_edge("gather_market_data", "compute_financials")
        g.add_edge("compute_financials", "recommend_budget")
        g.add_edge("recommend_budget", "make_go_no_go")
        g.add_edge("make_go_no_go", END)
        return g.compile()
"""

# ── app/agents/site_builder_agent.py ─────────────────────────────────────────
files["app/agents/site_builder_agent.py"] = """from langgraph.graph import StateGraph, END
from app.agents.base import AgentState, BaseAgent

def provision_subdomain(state):
    state["messages"] = state.get("messages", []) + ["subdomain provisioned (stub)"]
    return state

def generate_content(state):
    state["pages_generated"] = []
    state["messages"] = state.get("messages", []) + ["content generated (stub)"]
    return state

def inject_affiliate_links(state):
    state["messages"] = state.get("messages", []) + ["links injected (stub)"]
    return state

def publish_pages(state):
    state["pages_published"] = 0
    state["completed"] = True
    state["messages"] = state.get("messages", []) + ["pages published (stub)"]
    return state

class SiteBuilderAgent(BaseAgent):
    name = "SiteBuilderAgent"
    def build(self):
        g = StateGraph(AgentState)
        g.add_node("provision_subdomain", provision_subdomain)
        g.add_node("generate_content", generate_content)
        g.add_node("inject_affiliate_links", inject_affiliate_links)
        g.add_node("publish_pages", publish_pages)
        g.set_entry_point("provision_subdomain")
        g.add_edge("provision_subdomain", "generate_content")
        g.add_edge("generate_content", "inject_affiliate_links")
        g.add_edge("inject_affiliate_links", "publish_pages")
        g.add_edge("publish_pages", END)
        return g.compile()
"""

# ── app/agents/link_builder_agent.py ─────────────────────────────────────────
files["app/agents/link_builder_agent.py"] = """from langgraph.graph import StateGraph, END
from app.agents.base import AgentState, BaseAgent

def search_products(state):
    state["affiliate_products"] = []
    state["messages"] = state.get("messages", []) + ["products searched (stub)"]
    return state

def score_and_filter(state):
    state["messages"] = state.get("messages", []) + ["products filtered (stub)"]
    return state

def generate_links(state):
    state["links_created"] = 0
    state["completed"] = True
    state["messages"] = state.get("messages", []) + ["links generated (stub)"]
    return state

class LinkBuilderAgent(BaseAgent):
    name = "LinkBuilderAgent"
    def build(self):
        g = StateGraph(AgentState)
        g.add_node("search_products", search_products)
        g.add_node("score_and_filter", score_and_filter)
        g.add_node("generate_links", generate_links)
        g.set_entry_point("search_products")
        g.add_edge("search_products", "score_and_filter")
        g.add_edge("score_and_filter", "generate_links")
        g.add_edge("generate_links", END)
        return g.compile()
"""

# ── app/agents/ads_manager_agent.py ──────────────────────────────────────────
files["app/agents/ads_manager_agent.py"] = """from langgraph.graph import StateGraph, END
from app.agents.base import AgentState, BaseAgent

def create_campaign(state):
    state["campaign_id"] = None
    state["campaign_status"] = "draft"
    state["messages"] = state.get("messages", []) + ["campaign created (stub)"]
    return state

def monitor_performance(state):
    state["messages"] = state.get("messages", []) + ["performance monitored (stub)"]
    return state

def optimise_bids(state):
    state["messages"] = state.get("messages", []) + ["bids optimised (stub)"]
    return state

def reallocate_budget(state):
    state["budget_allocated"] = 0.0
    state["completed"] = True
    state["messages"] = state.get("messages", []) + ["budget reallocated (stub)"]
    return state

class AdsManagerAgent(BaseAgent):
    name = "AdsManagerAgent"
    def build(self):
        g = StateGraph(AgentState)
        g.add_node("create_campaign", create_campaign)
        g.add_node("monitor_performance", monitor_performance)
        g.add_node("optimise_bids", optimise_bids)
        g.add_node("reallocate_budget", reallocate_budget)
        g.set_entry_point("create_campaign")
        g.add_edge("create_campaign", "monitor_performance")
        g.add_edge("monitor_performance", "optimise_bids")
        g.add_edge("optimise_bids", "reallocate_budget")
        g.add_edge("reallocate_budget", END)
        return g.compile()
"""

# ── app/agents/controller_agent.py ───────────────────────────────────────────
files["app/agents/controller_agent.py"] = """from langgraph.graph import StateGraph, END
from app.agents.base import AgentState, BaseAgent

def assess_system_health(state):
    state["next_action"] = "idle"
    state["messages"] = state.get("messages", []) + ["health assessed (stub)"]
    return state

def trigger_research(state):
    state["messages"] = state.get("messages", []) + ["research triggered (stub)"]
    return state

def trigger_site_builds(state):
    state["messages"] = state.get("messages", []) + ["site builds triggered (stub)"]
    return state

def trigger_ads_optimisation(state):
    state["messages"] = state.get("messages", []) + ["ads optimisation triggered (stub)"]
    return state

def raise_alerts(state):
    state["completed"] = True
    state["messages"] = state.get("messages", []) + ["alerts raised (stub)"]
    return state

def route_after_health(state):
    action = state.get("next_action", "idle")
    if action == "research": return "trigger_research"
    if action == "build": return "trigger_site_builds"
    if action == "optimise": return "trigger_ads_optimisation"
    return "raise_alerts"

class ControllerAgent(BaseAgent):
    name = "ControllerAgent"
    def build(self):
        g = StateGraph(AgentState)
        g.add_node("assess_system_health", assess_system_health)
        g.add_node("trigger_research", trigger_research)
        g.add_node("trigger_site_builds", trigger_site_builds)
        g.add_node("trigger_ads_optimisation", trigger_ads_optimisation)
        g.add_node("raise_alerts", raise_alerts)
        g.set_entry_point("assess_system_health")
        g.add_conditional_edges("assess_system_health", route_after_health)
        g.add_edge("trigger_research", "raise_alerts")
        g.add_edge("trigger_site_builds", "raise_alerts")
        g.add_edge("trigger_ads_optimisation", "raise_alerts")
        g.add_edge("raise_alerts", END)
        return g.compile()
"""

# ── app/services/__init__.py ──────────────────────────────────────────────────
files["app/services/__init__.py"] = ""

# ── app/services/serpapi.py ───────────────────────────────────────────────────
files["app/services/serpapi.py"] = """import requests
from app.core.config import settings

class SerpAPIService:
    def __init__(self):
        self.api_key = settings.SERPAPI_KEY

    def search_keywords(self, query: str, country: str = "de") -> list:
        # TODO: implement full keyword extraction
        params = {"engine": "google", "q": query, "gl": country, "hl": "de", "api_key": self.api_key}
        r = requests.get("https://serpapi.com/search", params=params, timeout=15)
        r.raise_for_status()
        return r.json().get("organic_results", [])

    def get_trends(self, keyword: str, country: str = "DE") -> list:
        # TODO: implement trends parsing
        params = {"engine": "google_trends", "q": keyword, "geo": country, "api_key": self.api_key}
        r = requests.get("https://serpapi.com/search", params=params, timeout=15)
        r.raise_for_status()
        return r.json().get("interest_over_time", {}).get("timeline_data", [])
"""

# ── app/services/google_ads.py ────────────────────────────────────────────────
files["app/services/google_ads.py"] = """from app.core.config import settings

class GoogleAdsService:
    def __init__(self):
        self.developer_token = settings.GOOGLE_ADS_DEVELOPER_TOKEN

    def create_campaign(self, niche_id, campaign_name, daily_budget_eur, keywords, geo_target="DE"):
        raise NotImplementedError("create_campaign not yet implemented")

    def pause_campaign(self, google_campaign_id):
        raise NotImplementedError("pause_campaign not yet implemented")

    def resume_campaign(self, google_campaign_id):
        raise NotImplementedError("resume_campaign not yet implemented")

    def get_campaign_metrics(self, google_campaign_id):
        raise NotImplementedError("get_campaign_metrics not yet implemented")
"""

# ── app/services/amazon_pa.py ─────────────────────────────────────────────────
files["app/services/amazon_pa.py"] = """import urllib.parse
from app.core.config import settings

class AmazonPAService:
    def __init__(self):
        self.access_key = settings.AMAZON_ACCESS_KEY
        self.secret_key = settings.AMAZON_SECRET_KEY
        self.partner_tag = settings.AMAZON_PARTNER_TAG
        self.host = settings.AMAZON_HOST

    def search_products(self, keywords: str, item_count: int = 20) -> list:
        raise NotImplementedError("search_products not yet implemented")

    def get_product_details(self, asin: str) -> dict:
        raise NotImplementedError("get_product_details not yet implemented")

    def generate_affiliate_link(self, asin: str) -> str:
        params = urllib.parse.urlencode({"tag": self.partner_tag, "linkCode": "ogi"})
        return f"https://www.amazon.de/dp/{asin}?{params}"
"""

# ── app/services/ga4.py ───────────────────────────────────────────────────────
files["app/services/ga4.py"] = """from app.core.config import settings

class GA4Service:
    def __init__(self):
        self.property_id = settings.GA4_PROPERTY_ID

    def get_traffic(self, property_id, subdomain, start_date="30daysAgo", end_date="today"):
        raise NotImplementedError("get_traffic not yet implemented")

    def get_conversions(self, property_id=None, start_date="30daysAgo", end_date="today"):
        raise NotImplementedError("get_conversions not yet implemented")
"""

# ── app/services/dns.py ───────────────────────────────────────────────────────
files["app/services/dns.py"] = """from app.core.config import settings

class DNSService:
    def __init__(self):
        self.api_key = settings.DNS_PROVIDER_API_KEY
        self.base_domain = settings.DNS_BASE_DOMAIN

    def create_subdomain(self, name: str, target_ip: str = "127.0.0.1") -> dict:
        raise NotImplementedError("create_subdomain not yet implemented")

    def delete_subdomain(self, name: str) -> bool:
        raise NotImplementedError("delete_subdomain not yet implemented")
"""

# ── app/tasks/__init__.py ─────────────────────────────────────────────────────
files["app/tasks/__init__.py"] = ""

# ── app/tasks/scheduler.py ───────────────────────────────────────────────────
files["app/tasks/scheduler.py"] = """from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    "run-controller-agent-every-6h": {
        "task": "tasks.run_controller_agent",
        "schedule": crontab(minute=0, hour="*/6"),
        "options": {"expires": 3600},
    },
    "check-link-freshness-daily": {
        "task": "tasks.check_link_freshness",
        "schedule": crontab(minute=0, hour=3),
        "options": {"expires": 7200},
    },
}
"""

# ── app/tasks/agent_tasks.py ──────────────────────────────────────────────────
files["app/tasks/agent_tasks.py"] = """from datetime import datetime
from celery_app import celery_app

def _log_agent(agent_name, action, input_summary, result_summary):
    from app.db.session import SessionLocal
    from app.models.agent_log import AgentLog
    db = SessionLocal()
    try:
        db.add(AgentLog(agent_name=agent_name, action=action,
                        input_summary=input_summary, result_summary=result_summary,
                        timestamp=datetime.utcnow()))
        db.commit()
    finally:
        db.close()

@celery_app.task(name="tasks.run_research_agent", bind=True, max_retries=3)
def run_research_agent(self):
    try:
        from app.agents.research_agent import ResearchAgent
        result = ResearchAgent().run({"completed": False, "messages": []})
        _log_agent("ResearchAgent", "run_research_agent", "{}", str(result.get("messages")))
        return {"success": True}
    except Exception as exc:
        _log_agent("ResearchAgent", "run_research_agent", "{}", f"ERROR: {exc}")
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(name="tasks.run_business_case_agent", bind=True, max_retries=3)
def run_business_case_agent(self, niche_id: int):
    try:
        from app.agents.business_case_agent import BusinessCaseAgent
        result = BusinessCaseAgent().run({"niche_id": niche_id, "completed": False, "messages": []})
        _log_agent("BusinessCaseAgent", "run_business_case_agent", f"niche_id={niche_id}", str(result.get("messages")))
        return {"success": True}
    except Exception as exc:
        _log_agent("BusinessCaseAgent", "run_business_case_agent", f"niche_id={niche_id}", f"ERROR: {exc}")
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(name="tasks.run_site_builder_agent", bind=True, max_retries=3)
def run_site_builder_agent(self, niche_id: int, rebuild: bool = False):
    try:
        from app.agents.site_builder_agent import SiteBuilderAgent
        result = SiteBuilderAgent().run({"niche_id": niche_id, "completed": False, "messages": []})
        _log_agent("SiteBuilderAgent", "run_site_builder_agent", f"niche_id={niche_id}", str(result.get("messages")))
        return {"success": True}
    except Exception as exc:
        _log_agent("SiteBuilderAgent", "run_site_builder_agent", f"niche_id={niche_id}", f"ERROR: {exc}")
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(name="tasks.run_link_builder_agent", bind=True, max_retries=3)
def run_link_builder_agent(self, niche_id: int):
    try:
        from app.agents.link_builder_agent import LinkBuilderAgent
        result = LinkBuilderAgent().run({"niche_id": niche_id, "completed": False, "messages": []})
        _log_agent("LinkBuilderAgent", "run_link_builder_agent", f"niche_id={niche_id}", str(result.get("messages")))
        return {"success": True}
    except Exception as exc:
        _log_agent("LinkBuilderAgent", "run_link_builder_agent", f"niche_id={niche_id}", f"ERROR: {exc}")
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(name="tasks.run_ads_manager_agent", bind=True, max_retries=3)
def run_ads_manager_agent(self, niche_id: int):
    try:
        from app.agents.ads_manager_agent import AdsManagerAgent
        result = AdsManagerAgent().run({"niche_id": niche_id, "completed": False, "messages": []})
        _log_agent("AdsManagerAgent", "run_ads_manager_agent", f"niche_id={niche_id}", str(result.get("messages")))
        return {"success": True}
    except Exception as exc:
        _log_agent("AdsManagerAgent", "run_ads_manager_agent", f"niche_id={niche_id}", f"ERROR: {exc}")
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(name="tasks.run_controller_agent", bind=True, max_retries=3)
def run_controller_agent(self):
    try:
        from app.agents.controller_agent import ControllerAgent
        result = ControllerAgent().run({"completed": False, "messages": []})
        _log_agent("ControllerAgent", "run_controller_agent", "{}", str(result.get("messages")))
        return {"success": True}
    except Exception as exc:
        _log_agent("ControllerAgent", "run_controller_agent", "{}", f"ERROR: {exc}")
        raise self.retry(exc=exc, countdown=120)

@celery_app.task(name="tasks.check_link_freshness", bind=True, max_retries=2)
def check_link_freshness(self):
    try:
        from datetime import timedelta
        from app.db.session import SessionLocal
        from app.models.affiliate_link import AffiliateLink
        db = SessionLocal()
        stale_threshold = datetime.utcnow() - timedelta(hours=48)
        stale = (db.query(AffiliateLink.niche_id)
                 .filter(AffiliateLink.status == "active",
                         (AffiliateLink.last_checked == None) | (AffiliateLink.last_checked < stale_threshold))
                 .distinct().all())
        db.close()
        triggered = []
        for (niche_id,) in stale:
            run_link_builder_agent.delay(niche_id=niche_id)
            triggered.append(niche_id)
        _log_agent("LinkBuilderAgent", "check_link_freshness", "{}", f"triggered: {triggered}")
        return {"success": True, "triggered_niches": triggered}
    except Exception as exc:
        _log_agent("LinkBuilderAgent", "check_link_freshness", "{}", f"ERROR: {exc}")
        raise self.retry(exc=exc, countdown=300)
"""

# ─────────────────────────────────────────────────────────────────────────────
# Write all files
# ─────────────────────────────────────────────────────────────────────────────
written = 0
skipped = 0

for path, content in files.items():
    # Ensure parent directories exist
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    written += 1
    print(f"  ✓  {path}")

print(f"\nDone — {written} files written.")
print("\nNext steps:")
print("  python -m alembic revision --autogenerate -m 'initial schema'")
print("  python -m alembic upgrade head")
print("  python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload")