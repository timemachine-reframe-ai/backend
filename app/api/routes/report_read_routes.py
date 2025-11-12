import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models.report import Report

router = APIRouter()


@router.get("/reports/{report_id}", summary="리포트 상세 조회")
def get_report(report_id: int, db: Session = Depends(get_db), format: str | None = None):
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if format == "md":
        if report.status != "finished":
            raise HTTPException(status_code=400, detail="Report not finished")
        return report.report_md or ""

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
