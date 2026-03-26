from datetime import datetime
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
