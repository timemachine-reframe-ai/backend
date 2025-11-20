from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.reflections import router as reflections_router
from app.api.routes.report_write_routes import router as report_write_router
from app.api.routes.report_read_routes import router as report_read_router
from app.api.routes.users_routes import router as users_router
from app.api.routes.auth_routes import router as auth_router

from app.db.session import engine, Base
from app.startup.ensure_schema import ensure_reports_failure_reason_column
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="Reflection Reports API", version="1.0.0")

app.include_router(reflections_router, prefix="/api/reflections", tags=["reflections"])
app.include_router(report_write_router, prefix="/api/reflections", tags=["reports"])
app.include_router(report_read_router, prefix="/api/reflections", tags=["reports"])

app.include_router(auth_router, prefix="/api", tags=["auth"])
app.include_router(users_router, prefix="/api/users", tags=["users"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    Base.metadata.create_all(bind=engine)
    ensure_reports_failure_reason_column(engine)


@app.get("/health")
def health():
    return {"ok": True}
