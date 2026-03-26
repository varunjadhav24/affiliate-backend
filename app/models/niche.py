from datetime import datetime
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
