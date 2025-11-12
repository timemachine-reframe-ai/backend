from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.token import TokenPayload
from app.services.langchain import LangChainService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


def get_settings_dependency() -> Settings:
    """Expose application settings as a FastAPI dependency."""
    return get_settings()

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_langchain_service(
    settings: Settings = Depends(get_settings_dependency),
) -> LangChainService:
    return LangChainService(settings=settings)


def get_token_payload(
    token: str = Depends(oauth2_scheme),
    settings: Settings = Depends(get_settings_dependency),
) -> TokenPayload:
    """Common dependency that validates JWTs and returns their payload."""
    try:
        return decode_access_token(
            token,
            secret_key=settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_user(
    payload: TokenPayload = Depends(get_token_payload),
    repository: UserRepository = Depends(get_user_repository),
):
    """Resolve the authenticated user using the JWT payload."""
    user = repository.get(payload.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User for provided token no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
