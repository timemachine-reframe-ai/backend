from typing import List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class ReportCreateRequest(BaseModel):
    session_id: str = Field(..., alias="sessionId")
    requestor: Optional[str] = None
    conversation_context: str = Field(..., alias="conversationContext")
    user_name: str = Field(default="사용자", alias="userName")

    model_config = ConfigDict(populate_by_name=True)


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
    session_id: str
    status: str
    failure_reason: Optional[str] = None
    report_md: Optional[str]
    report_json: Optional[Any]
    created_at: datetime
    processed_at: Optional[datetime]
