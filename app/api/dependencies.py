from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.services.langchain import LangChainService


def get_settings_dependency() -> Settings:
    """Expose application settings as a FastAPI dependency."""
    return get_settings()

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_langchain_service(
    settings: Settings = Depends(get_settings_dependency),
) -> LangChainService:
    return LangChainService(settings=settings)
