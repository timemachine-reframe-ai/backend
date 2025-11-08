from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine

settings = get_settings()


def create_application() -> FastAPI:
    Base.metadata.create_all(bind=engine)

    application = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router, prefix=settings.API_PREFIX)
    return application


app = create_application()


@app.get("/")
async def root():
    return {
        "message": "Welcome to the TIMEMACHINE-AI API!",
        "version": settings.VERSION,
    }
