from datetime import datetime
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
