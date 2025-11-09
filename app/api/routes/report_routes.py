from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.report import ReportRequest, ReportResponse
from app.services.report_service import enqueue_report_generation, get_report_by_id

router = APIRouter(prefix="/reflections", tags=["reflections"])

@router.post("/sessions/{session_id}/report", status_code=202)
async def request_report(session_id: int, payload: ReportRequest, db: AsyncSession = Depends(get_db)):
    try:
        report_id = await enqueue_report_generation(db, session_id, payload.requestor)
        return {"queued": True, "reportId": report_id, "status": "pending"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/{report_id}", response_model=ReportResponse)
async def fetch_report(report_id: int, db: AsyncSession = Depends(get_db)):
    row = await get_report_by_id(db, report_id)
    if not row:
        raise HTTPException(status_code=404, detail="report not found")
    return row
