from datetime import datetime
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, get_langchain_service
from app.services import ChatService
from app.services.report_service import generate_report_for_session
from app.models.report import Report
from app.schemas.report import ReportCreateRequest, ReportResponse

router = APIRouter()


@router.post(
    "/reports",
    response_model=ReportResponse,
    summary="세션 리포트 동기 생성",
)
def create_report(
    payload: ReportCreateRequest,
    db: Session = Depends(get_db),
    service: ChatService = Depends(get_langchain_service),
    current_user=Depends(get_current_user),
):
    session_id = payload.session_id
    conversation_context = payload.conversation_context.strip()
    if not conversation_context:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="conversationContext is required",
        )
    requestor = payload.requestor

    report = Report(
        session_id=str(session_id),
        requestor=requestor,
        user_id=current_user.id,
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    try:
        generated = generate_report_for_session(
            db=db,
            session_id=session_id,
            conversation_text=conversation_context,
            service=service,
            requestor=requestor,
            user_name=payload.user_name,
        )
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

    return ReportResponse(
        report_id=report.report_id,
        session_id=report.session_id,
        status=report.status,
        failure_reason=report.failure_reason,
        created_at=report.created_at,
        processed_at=report.processed_at,
        report_json=generated["report_json"],
        report_md=generated["report_md"],
    )


@router.delete("/{session_id}", summary="리포트 삭제")
def delete_report(
    session_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # 1. Try match by session_id
    report = (
        db.query(Report)
        .filter(Report.session_id == session_id, Report.user_id == current_user.id)
        .first()
    )

    # 2. If not found and session_id looks like an int, try report_id
    if not report and session_id.isdigit():
        report = (
            db.query(Report)
            .filter(Report.report_id == int(session_id), Report.user_id == current_user.id)
            .first()
        )

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    db.delete(report)
    db.commit()
    return {"ok": True}
