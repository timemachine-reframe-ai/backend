from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.reflections import router as reflections_router
from app.api.routes.report_write_routes import router as report_write_router
from app.api.routes.report_read_routes import router as report_read_router

from app.db.session import engine
from app.startup.ensure_schema import ensure_reports_failure_reason_column

app = FastAPI(title="Reflection Reports API", version="1.0.0")

app.include_router(reflections_router, prefix="/api/reflections", tags=["reflections"])
app.include_router(report_write_router, prefix="/api/reflections", tags=["reports"])
app.include_router(report_read_router, prefix="/api/reflections", tags=["reports"])

@app.on_event("startup")
def _startup():
    ensure_reports_failure_reason_column(engine)

@app.get("/health")
def health():
    return {"ok": True}

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)