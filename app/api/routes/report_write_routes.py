from datetime import datetime
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_langchain_service
from app.services.langchain import LangChainService
from app.services.report_service import generate_report_for_session
from app.models.report import Report

router = APIRouter()


@router.post("/reports", summary="세션 리포트 동기 생성")
def create_report(
    body: dict,
    db: Session = Depends(get_db),
    service: LangChainService = Depends(get_langchain_service),
):
    session_id = body.get("sessionId")
    if session_id is None:
        raise HTTPException(status_code=400, detail="sessionId is required")

    requestor = body.get("requestor")

    report = Report(
        session_id=str(session_id),
        requestor=requestor,
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    try:
        generated = generate_report_for_session(db, session_id, service, requestor)
        report.report_md = generated["report_md"]
        report.report_json = json.dumps(generated["report_json"], ensure_ascii=False)
        report.status = "finished"
        report.processed_at = datetime.utcnow()
        db.commit()
        db.refresh(report)
    except RuntimeError as exc:
        report.status = "failed"
        report.failure_reason = str(exc)
        report.processed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        report.status = "failed"
        report.failure_reason = "Unexpected error"
        report.processed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate report.",
        ) from exc

    return {
        "report_id": report.report_id,
        "session_id": report.session_id,
        "status": report.status,
        "failure_reason": report.failure_reason,
        "created_at": report.created_at,
        "processed_at": report.processed_at,
        "report_json": generated["report_json"],
        "report_md": generated["report_md"],
    }
