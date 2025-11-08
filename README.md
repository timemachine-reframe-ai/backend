# TIMEMACHINE AI – 백엔드

LangChain 연동을 고려해 구조화된 FastAPI 서비스입니다. 사용자 리소스와 상태 체크 API를 제공하며, 추가 AI 워크플로도 `services/` 계층에서 쉽게 붙일 수 있습니다.

## 기술 스택
- FastAPI + Uvicorn
- 기본 SQLite(`app/data/app.db`)를 사용하는 SQLAlchemy ORM
- Pydantic v2 및 `pydantic-settings` 기반 환경설정
- LangChain · OpenAI 어댑터 (`app/services/langchain.py`)

## 시작하기
1. **의존성 설치**
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **환경 변수 설정**
   ```bash
   cp .env.example .env
   # 필요 값으로 수정
   ```
   | 변수 | 설명 |
   | --- | --- |
   | `PROJECT_NAME` | FastAPI 제목 (기본값 `TIMEMACHINE-AI API`) |
   | `API_PREFIX` | 모든 라우터의 공통 prefix (`/api`) |
   | `DATABASE_URL` | SQLAlchemy 연결 문자열 (기본 SQLite) |
   | `LANGCHAIN_MODEL` | LangChain에서 사용할 모델 이름 |
   | `LANGCHAIN_API_KEY` | LangChain/OpenAI 접근 토큰 |
   | `LANGCHAIN_TRACING` | LangSmith 트레이싱 여부 (`true`/`false`) |

3. **서버 실행**
   ```bash
   uvicorn app.main:app --reload
   ```
   기본 헬스체크: `http://localhost:8000/api/health/live`

## 디렉터리 구조
```
app/
├── api/                 # 라우터, 의존성, 헬스 체크
├── core/                # 설정/보안 유틸
├── db/                  # SQLAlchemy 엔진 및 세션
├── models/              # ORM 모델 (User 등)
├── repositories/        # 데이터 접근 계층
├── schemas/             # Pydantic 스키마
└── services/            # LangChain 등 도메인 서비스
```

## 자주 쓰는 명령
```bash
# 실서비스 모드로 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 구문 체크/간단 테스트
python -m compileall app
```

## 제공 중인 API
- `GET /api/health/live` : 라이브니스 체크
- `GET /api/health/ready` : 레디니스 + LangChain 설정 정보
- `POST /api/users` : 사용자 생성 (이메일 중복 방지)
- `GET /api/users` : 사용자 목록, `skip/limit` 페이지네이션
- `GET /api/users/{user_id}` : 단일 사용자 조회

새로운 리소스는 `app/api/routes`에 추가하고, 데이터 접근 로직은 `repositories/`·`services/`로 분리하면 깔끔하게 확장할 수 있습니다.
