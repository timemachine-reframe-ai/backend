from sqlalchemy import Column, Integer, String, Text, JSON, TIMESTAMP
from app.db.base import Base  # adjust if your project uses a different import

class Report(Base):
    __tablename__ = "Reports"

    report_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=False, index=True)
    status = Column(String(50), default='pending')
    requested_by = Column(String(100), nullable=True)
    report_md = Column(Text, nullable=True)
    report_json = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)
    processed_at = Column(TIMESTAMP, nullable=True)
