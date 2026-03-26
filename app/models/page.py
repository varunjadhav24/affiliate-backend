from datetime import datetime
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
