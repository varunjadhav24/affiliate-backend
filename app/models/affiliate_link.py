from datetime import datetime
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
