from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, get_settings_dependency, get_user_repository
from app.core.config import Settings
from app.core.security import create_access_token
from app.models.user import User as UserModel
from app.repositories.user_repository import UserRepository
from app.schemas.user import LoginRequest, LoginResponse, User, LoginIdAvailabilityResponse

router = APIRouter()


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Authenticate user by loginId/password",
)
def login(
    payload: LoginRequest,
    repository: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings_dependency),
):
    user = repository.authenticate(payload)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid login credentials",
        )

    token = create_access_token(
        subject=user.id,
        secret_key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    return LoginResponse(access_token=token)


@router.get(
    "/me",
    response_model=User,
    summary="Get current authenticated user",
)
def read_me(current_user: UserModel = Depends(get_current_user)):
    return current_user


@router.get(
    "/login-id/check",
    response_model=LoginIdAvailabilityResponse,
    summary="Check if loginId is available",
)
def check_login_id(
    login_id: str,
    repository: UserRepository = Depends(get_user_repository),
):
    exists = repository.get_by_login_id(login_id) is not None
    return LoginIdAvailabilityResponse(loginId=login_id, available=not exists)
