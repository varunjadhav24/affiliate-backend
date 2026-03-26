from datetime import datetime
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
