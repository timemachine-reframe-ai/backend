from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.langchain import generate_report_for_session

router = APIRouter()

class ReportRequest(BaseModel):
    requestor: Optional[str] = None

@router.post("/sessions/{session_id}/report", status_code=200)
def request_report(session_id: int, payload: ReportRequest, db: Session = Depends(get_db)):
    """
    회고 리포트 생성(동기 프로토타입).
    - 이 엔드포인트는 DB에 저장하지 않고, 호출 즉시 리포트를 생성하여 반환합니다.
    """
    try:
        result = generate_report_for_session(db, session_id, payload.requestor)
        # 반환 형식: { "report_md": str, "report_json": dict }
        return {"queued": False, "generated": True, "report": result}
    except ValueError as ve:
        # 해당 세션에 채팅 데이터가 없을 때
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        # 기타 내부 오류
        raise HTTPException(status_code=500, detail=str(e))
