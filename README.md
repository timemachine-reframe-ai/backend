# TIMEMACHINE AI – 백엔드

이 폴더는 “AI 상담사” 역할을 하는 FastAPI 서버입니다. 사용자가 겪은 상황을 보내면 요약 리포트를 만들어 주고, 가상의 인물(persona)처럼 대화를 이어 줍니다. 프런트엔드는 `/api/reflections/*` 라우트만 호출하면 되고, 모델 키 관리·프롬프트 작성·후처리는 모두 여기서 처리합니다.

---

## 1. 우리는 어떤 기술을 쓰나요?

- **FastAPI + Uvicorn** – 빠르게 REST API를 만들고 CORS도 처리합니다.
- **SQLAlchemy + SQLite** – 사용자와 리포트를 파일 DB에 저장합니다.
- **Pydantic v2** – API 스키마와 환경 설정을 깔끔하게 관리합니다.
- **LangChain + langchain-google-genai** – Gemini 2.5 Flash 모델을 안전하게 호출합니다.

---

## 2. 폴더 한눈에 보기

```
app/
├── api/          FastAPI 라우터와 의존성 주입
├── core/         환경설정, 보안 유틸
├── db/           SQLAlchemy Base, 세션
├── models/       ORM 모델
├── repositories/ DB 접근 로직
├── schemas/      요청/응답 Pydantic 모델
└── services/
    ├── reflection/   요약·감정·대화 LLM 로직
    └── report_service.py  리포트 생성 헬퍼
```

폴더 이름을 보면 어디에 어떤 코드를 넣어야 할지 바로 알 수 있습니다.

---

## 3. 로컬에서 바로 돌려보기

1. 파이썬 가상환경 만들기
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate   # Windows는 .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. 환경 변수 채우기
   ```bash
   cp .env.example .env
   # GEMINI_API_KEY 를 발급받아 넣으면 LLM을 바로 사용할 수 있습니다.
   ```
3. 서버 실행
   ```bash
   uvicorn app.main:app --reload
   ```
4. 헬스 체크: <http://localhost:8000/api/health>

자주 쓰는 명령
```bash
uvicorn app.main:app --reload               # 개발 서버
uvicorn app.main:app --host 0.0.0.0 --port 8000   # 운영 예시
python -m compileall app                    # 문법 오류 빠르게 확인
```

---

## 4. `.env` 에 꼭 넣어야 할 것들

| 이름 | 설명 |
| --- | --- |
| `PROJECT_NAME` | 자동 문서/헬스 체크에서 노출할 이름 |
| `API_PREFIX` | 모든 라우터 앞에 붙는 경로 (기본 `/api`) |
| `DATABASE_URL` | SQLAlchemy 연결 문자열 |
| `GEMINI_MODEL` | 사용할 모델 ID (기본 `gemini-2.0-flash`) |
| `GEMINI_API_KEY` | Google Generative AI 키. 없으면 규칙 기반으로만 동작 |

키가 필요하면 [Google AI Studio](https://aistudio.google.com/app/apikey) 에서 발급받으세요.

---

## 5. LLM을 켜면 뭐가 좋아지나요?

- `GEMINI_API_KEY` 를 넣으면 LLM 경로가 활성화됩니다.
  - 리포트에 `emotionsDetailed`, `moodTimeline` 같은 풍부한 필드가 추가되고,
  - persona 대화가 실제 사람처럼 자연스러워집니다.
- 키가 없어도 걱정 마세요. 시스템이 자동으로 규칙 기반 로직으로 전환합니다.

---

## 6. 리포트/대화는 어떻게 만들어질까요?

### 감정 라벨(고정 16개)
불안, 당황, 화남, 슬픔, 기쁨, 죄책감, 수치심, 안도, 기대, 좌절, 실망, 긴장, 혼란, 짜증, 무력감, 흥분  
(예: “걱정”이라고 적어도 자동으로 “불안”으로 정리됩니다.)

### 응답 구조
| 항목 | 설명 |
| --- | --- |
| `summary` | 1~3문장 요약 |
| `keyInsights` | 핵심 인사이트 2~5개 |
| `suggestedPhrases` | 추천 표현 2~5개 |
| `emotions`, `decisionPoints`, `actionItems`, `confidence` | 감정·결정·할 일·신뢰도 |
| `emotionsDetailed`, `moodTimeline` | LLM 활성 시 추가되는 상세 감정·감정 타임라인 |

### 주요 API
- `POST /api/reflections/summary` – 상황만 보내면 즉시 리포트 JSON을 받습니다.
- `POST /api/reflections/reports` – 세션 ID 기준으로 리포트를 생성하고 DB에 저장합니다.
- `GET /api/reflections/reports/{id}` – 저장된 리포트를 JSON 또는 Markdown으로 조회합니다.
- `POST /api/reflections/chat` – persona 정보 + 대화 기록을 보내면 “그 사람처럼” 답합니다.

---

## 7. 안전장치(후처리 로직)

- LLM이 엉뚱한 감정을 내놓으면 taxonomy 규칙으로 정리
- 근거 텍스트가 본문에 없으면 비워둠 (200자 제한)
- score/vad 값은 0~1 범위로 강제
- 타임라인은 최대 8개 구간, 구간당 감정 2개까지만 허용
- LLM 호출 실패 시 규칙 기반 로직으로 자동 전환

---

## 8. 바로 테스트해 보기

```bash
# 1) 헬스 체크
curl http://localhost:8000/api/health

# 2) 요약 생성
curl -X POST http://localhost:8000/api/reflections/summary \
  -H "Content-Type: application/json" \
  -d '{"whatHappened":"회의에서 충돌","whatYouDid":"즉각 반박","howYouWishItHadGone":"차분히 설명"}'

# 3) 리포트 생성
curl -X POST http://localhost:8000/api/reflections/reports \
  -H "Content-Type: application/json" \
  -d '{"sessionId":123}'

# 4) 리포트 조회 (JSON)
curl http://localhost:8000/api/reflections/reports/1

# 5) 리포트 조회 (Markdown)
curl -i http://localhost:8000/api/reflections/reports/1?format=md
```

LLM을 켜고 끄면서 위 명령을 실행해 보면, 응답에 포함되는 필드가 어떻게 달라지는지 바로 확인할 수 있습니다.
