# TIMEMACHINE AI – 백엔드

LangChain 기반으로 Gemini 모델을 호출할 수 있게 구성된 FastAPI 서비스입니다. 사용자 리소스와 상태 체크 API를 제공하며, 추가 AI 워크플로도 `services/` 계층에서 쉽게 붙일 수 있습니다.

## 기술 스택
- FastAPI + Uvicorn
- 기본 SQLite(`app/data/app.db`)를 사용하는 SQLAlchemy ORM
- Pydantic v2 및 `pydantic-settings` 기반 환경설정
- LangChain 1.x Runnable + Gemini 어댑터 (`app/services/langchain.py`, `langchain==1.0.5`)

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
   | `GEMINI_MODEL` | LangChain을 통해 호출할 Gemini 모델 이름 (기본 `gemini-2.5-flash`) |
   | `GEMINI_API_KEY` | Google Generative AI(Gemini) API 키 |

   LangChain 1.x부터는 모든 체인이 `Runnable` 형태로 구성되므로, 추가 AI 기능을 구현할 때도 동일한 패턴(`prompt | model | parser`)을 따라가면 됩니다.

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
└── services/            # LangChain 기반 Gemini 서비스
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
- `GET /api/health/ready` : 레디니스 + Gemini 모델 설정 정보
- `POST /api/reflections/summary` : 회고 입력을 LangChain 1.x(Gemini) 체인에 전달해 요약/인사이트/추천 표현 생성
- `POST /api/reflections/chat` : 시뮬레이션 대화 중 사용자 메시지에 대한 Gemini 응답 생성
- `POST /api/users` : 사용자 생성 (이메일 중복 방지)
- `GET /api/users` : 사용자 목록, `skip/limit` 페이지네이션
- `GET /api/users/{user_id}` : 단일 사용자 조회

새로운 리소스는 `app/api/routes`에 추가하고, 데이터 접근 로직은 `repositories/`·`services/`로 분리하면 깔끔하게 확장할 수 있습니다.

### 회고 요약 API 예시
```http
POST /api/reflections/summary
Content-Type: application/json

{
  "whatHappened": "회의에서 의견 충돌이 있었다",
  "emotions": ["불안", "분노"],
  "whatYouDid": "즉각 반박하며 감정적으로 대응했다",
  "howYouWishItHadGone": "차분하게 근거를 제시하고 싶었다"
}
```

정상 응답은 `{"summary": "...", "keyInsights": [...], "suggestedPhrases": [...]}` 형태이며, Gemini API 키가 비어 있으면 503 오류를 돌려줍니다.

### 시뮬레이션 대화 API 예시
```http
POST /api/reflections/chat
Content-Type: application/json

{
  "whatHappened": "회의에서 의견 충돌이 있었다",
  "emotions": ["불안"],
  "whatYouDid": "즉각 반박했다",
  "howYouWishItHadGone": "차분하게 근거를 설명하고 싶었다",
  "personaName": "팀장님",
  "personaTone": "차분한",
  "personaPersonality": "공감적인 리더",
  "conversation": [
    {"sender": "user", "text": "..."},
    {"sender": "ai", "text": "..."}
  ],
  "message": "제가 왜 이렇게 반응했을까요?"
}
```

→ `{"reply": "..."}` 형태의 응답을 돌려주며, 오류 발생 시 503/500 상태 코드로 알려줍니다.
