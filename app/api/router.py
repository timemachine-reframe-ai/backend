from fastapi import APIRouter
from app.api.routes.reflections import router as reflections_router
from app.api.routes.report_write_routes import router as report_write_router
from app.api.routes.report_read_routes import router as report_read_router

api_router = APIRouter()

api_router.include_router(reflections_router, prefix="/api/reflections", tags=["reflections"])
api_router.include_router(report_write_router, prefix="/api/reflections", tags=["reports"])
api_router.include_router(report_read_router, prefix="/api/reflections", tags=["reports"])
