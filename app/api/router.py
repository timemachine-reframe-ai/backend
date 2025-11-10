from fastapi import APIRouter

# 기존 라우트들
from app.api.routes import health, reflections, users
# 새로 추가: 회고 리포트 라우트
from app.api.routes import report_routes

api_router = APIRouter()

# 헬스 체크
api_router.include_router(health.router, prefix="/health", tags=["health"])

# 기존 reflections 관련
api_router.include_router(
    reflections.router,
    prefix="/reflections",
    tags=["reflections"],
)

# 사용자 관련
api_router.include_router(users.router, prefix="/users", tags=["users"])

# 회고 리포트 (프로토타입, /api/reflections/sessions/{id}/report)
api_router.include_router(report_routes.router, prefix="/reflections", tags=["reflections"])
