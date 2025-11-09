from fastapi import APIRouter

from app.api.routes import auth, health, reflections, users

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(
    reflections.router,
    prefix="/reflections",
    tags=["reflections"],
)
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(auth.router, tags=["auth"])
