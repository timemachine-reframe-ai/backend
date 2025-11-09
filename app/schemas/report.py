from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class ReportRequest(BaseModel):
    requestor: Optional[str] = None

class Alternative(BaseModel):
    title: str
    summary: str
    pros: List[str]
    cons: List[str]
    script: str

class DecisionPoint(BaseModel):
    chat_id: int
    ts: datetime
    text: str
    sentiment_label: Optional[str]
    sentiment_score: Optional[float]
    alternatives: List[Alternative]
    recommended: Optional[str]

class ReportSummary(BaseModel):
    session_id: int
    period_start: datetime
    period_end: datetime
    aha: str
    next_action: Optional[str]

class ReportResponse(BaseModel):
    report_id: int
    session_id: int
    status: str
    report_md: Optional[str]
    report_json: Optional[Any]
    created_at: datetime
    processed_at: Optional[datetime]
