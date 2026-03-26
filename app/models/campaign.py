from datetime import datetime
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
