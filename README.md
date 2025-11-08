# TIMEMACHINE AI – 백엔드

LangChain 1.0.5 Runnable + Gemini 2.5 Flash 조합으로 작동하는 FastAPI 서비스.  
프론트엔드는 `/api/reflections/*`만 호출하며, 실제 LLM 호출·프롬프트·키 관리·에러 처리를 모두 서버가 담당.

## 기술 스택
- **FastAPI + Uvicorn**: REST API 및 CORS 처리
- **SQLAlchemy ORM (기본 SQLite)**: 사용자 데이터 저장
- **Pydantic v2 + pydantic-settings**: 타입 안전성과 설정 관리
- **LangChain 1.0.5**: Runnable 파이프라인으로 요약/대화 체인 구현
- **LangChain-Google-GenAI 3.0.1**: Gemini 2.5 Flash 모델 연동

## 빠른 시작
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# GEMINI_API_KEY 등 값을 채워 넣어야함.

uvicorn app.main:app --reload
```

기본 헬스 체크: <http://localhost:8000/api/health/live>

### 환경 변수 (`.env`)
| 변수 | 설명 |
| --- | --- |
| `PROJECT_NAME` | FastAPI 문서/헬스에서 노출되는 이름 |
| `API_PREFIX` | 모든 라우터 앞에 붙는 prefix (`/api`) |
| `DATABASE_URL` | SQLAlchemy 연결 문자열 (기본 SQLite 파일) |
| `GEMINI_MODEL` | 사용할 Gemini 모델 ID (기본 `gemini-2.5-flash`) |
| `GEMINI_API_KEY` | Google Generative AI API 키 |

모든 LangChain 체인은 `prompt | model | parser` 패턴으로 구성되어 있으므로, 새로운 분석/대화 체인을 추가할 때도 동일한 형태를 유지하면 됨.

## 디렉터리 구조
```
app/
├── api/            # FastAPI 라우터와 DI 구성요소
├── core/           # 설정 + 보안 유틸
├── db/             # SQLAlchemy 엔진/세션/베이스
├── models/         # ORM 모델
├── repositories/   # 데이터 액세스 계층
├── schemas/        # Pydantic DTO
└── services/       # LangChain 기반 Gemini 서비스
```

## 자주 쓰는 명령
```bash
# 개발 모드
uvicorn app.main:app --reload

# 운영 모드 예시
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 구문 검증
python -m compileall app
```

## 제공 중인 API
- `GET /api/health/live` : 라이브니스 체크
- `GET /api/health/ready` : 서비스 버전과 사용 중인 Gemini 모델 확인
- `POST /api/reflections/summary` : 상황 정보를 입력받아 요약 · 핵심 인사이트 · 추천 표현 JSON 생성
- `POST /api/reflections/chat` : 페르소나 정보와 대화 로그를 기반으로 시뮬레이션 대화 답변 생성
- `POST /api/users` / `GET /api/users` / `GET /api/users/{id}` : 기본 사용자 CRUD (데모용)

새로운 리소스는 `app/api/routes`에 라우터를 추가하고, 내부 로직은 `services/` 혹은 `repositories/`에 분리하면 됨.

### 회고 요약 API 예시
```http
POST /api/reflections/summary
Content-Type: application/json

{
  "whatHappened": "회의에서 의견 충돌이 있었다",
  "emotions": ["불안", "분노"],
  "whatYouDid": "즉각 반박했다",
  "howYouWishItHadGone": "차분하게 근거를 설명하고 싶었다"
}
```

정상 응답:
```json
{
  "summary": "두 사람이 의견 충돌로 갈등했지만, 관계 회복을 바라고 있습니다.",
  "keyInsights": [
    "즉각적인 방어 반응이 갈등을 키웠습니다.",
    "사과를 미룬 것에 대한 아쉬움이 관계 회복 욕구로 이어집니다."
  ],
  "suggestedPhrases": [
    "지금 생각해보니 감정이 앞섰던 것 같아.",
    "우리 관계를 지키고 싶어. 다시 얘기해볼 수 있을까?"
  ]
}
```

### 시뮬레이션 대화 API 예시
```http
POST /api/reflections/chat
Content-Type: application/json

{
  "whatHappened": "...",
  "emotions": ["불안"],
  "whatYouDid": "즉각 반박했다",
  "howYouWishItHadGone": "차분하게 설명하고 싶었다",
  "personaName": "팀장님",
  "personaTone": "차분한",
  "personaPersonality": "공감적인 리더",
  "conversation": [
    {"sender": "user", "text": "그때 너무 놀랐어요."},
    {"sender": "ai", "text": "나도 당황했지만 너를 미워한 건 아니야."}
  ],
  "message": "제가 왜 그렇게 말했는지 모르겠어요."
}
```

→ `{"reply": "..."}` 형태로 반환되며, Gemini 키가 없으면 503, 그 외 예외는 500으로 응답.
