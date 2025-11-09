from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.dependencies import get_current_user, get_user_repository
from app.repositories.user_repository import UserRepository
from app.schemas.user import User, UserCreate, UserUpdate
from app.models.user import User as UserModel

router = APIRouter()


@router.post(
    "/",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
)
def create_user_endpoint(
    payload: UserCreate,
    repository: UserRepository = Depends(get_user_repository),
):
    if repository.get_by_email(payload.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    if repository.get_by_login_id(payload.loginId):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Login ID already registered")
    return repository.create(payload)


@router.get("/", response_model=List[User], summary="List users")
def read_users(
    skip: int = 0,
    limit: int = 10,
    repository: UserRepository = Depends(get_user_repository),
):
    return repository.list(skip=skip, limit=limit)


@router.get(
    "/{user_id}",
    response_model=User,
    summary="Get a single user by id",
)
def read_user(user_id: int, repository: UserRepository = Depends(get_user_repository)):
    user = repository.get(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put(
    "/{user_id}",
    response_model=User,
    summary="Update user",
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    repository: UserRepository = Depends(get_user_repository),
    current_user: UserModel = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    user = repository.update(user_id, payload)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
)
def delete_user(
    user_id: int,
    repository: UserRepository = Depends(get_user_repository),
    current_user: UserModel = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    deleted = repository.delete(user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
