from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.db.session import Base


class Report(Base):
    __tablename__ = "reports"

    report_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, index=True, nullable=False)
    requestor = Column(String, nullable=True)

    status = Column(String, default="pending", nullable=False)  # pending | finished | failed
    report_md = Column(Text, nullable=True)
    report_json = Column(Text, nullable=True)

    failure_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)

