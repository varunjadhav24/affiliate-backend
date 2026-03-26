from datetime import datetime
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
