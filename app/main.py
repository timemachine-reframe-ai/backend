# main.py
from fastapi import FastAPI
from app.api.endpoints import users
from app.db.session import engine, Base

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TIMEMACHINE-AI API", version="1.0.0")

# 라우터 등록
app.include_router(users.router, prefix="/api", tags=["users"])


@app.get("/")
async def root():
    return {"message": "Welcome to the TIMEMACHINE-AI API!"}