from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.db.session import Base


class Report(Base):
    __tablename__ = "reports"

    report_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)
    session_id = Column(String(255), index=True, nullable=False)
    requestor = Column(String(255), nullable=True)

    status = Column(
        String(255), default="pending", nullable=False
    )  # pending | finished | failed
    report_md = Column(Text, nullable=True)
    report_json = Column(Text, nullable=True)

    failure_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
