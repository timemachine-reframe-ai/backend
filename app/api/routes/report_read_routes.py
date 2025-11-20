import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.models.report import Report
from app.schemas.report import ReportResponse

router = APIRouter()


@router.get("/reports", response_model=List[ReportResponse], summary="내 리포트 목록 조회")
def list_reports(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    items = (
        db.query(Report)
        .filter(Report.user_id == current_user.id)
        .order_by(Report.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    results: List[ReportResponse] = []
    for r in items:
        parsed_json = None
        if r.report_json and r.status == "finished":
            try:
                parsed_json = json.loads(r.report_json)
            except Exception:
                parsed_json = None
        results.append(
            ReportResponse(
                report_id=r.report_id,
                session_id=r.session_id,
                status=r.status,
                failure_reason=r.failure_reason if r.status == "failed" else None,
                report_md=r.report_md if r.status == "finished" else None,
                report_json=parsed_json,
                created_at=r.created_at,
                processed_at=r.processed_at,
            )
        )
    return results


@router.get("/reports/{report_id}", summary="리포트 상세 조회")
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    format: str | None = None,
    current_user=Depends(get_current_user),
):
    report = (
        db.query(Report)
        .filter(Report.report_id == report_id, Report.user_id == current_user.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if format == "md":
        if report.status != "finished":
            raise HTTPException(status_code=400, detail="Report not finished")
        return Response(content=report.report_md or "", media_type="text/markdown")

    parsed_json = {}
    if report.report_json and report.status == "finished":
        try:
            parsed_json = json.loads(report.report_json)
        except Exception:
            parsed_json = {}

    return {
        "report_id": report.report_id,
        "session_id": report.session_id,
        "status": report.status,
        "failure_reason": report.failure_reason if report.status == "failed" else None,
        "created_at": report.created_at,
        "processed_at": report.processed_at,
        "report_json": parsed_json if report.status == "finished" else None,
    }
