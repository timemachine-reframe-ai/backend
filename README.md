# TIMEMACHINE AI – 백엔드

Gemini 2.5 Flash + LangChain 조합으로 회고 요약, 시뮬레이션 대화, 리포트 생성을 담당하는 FastAPI 서비스입니다. 프런트엔드는 `/api/reflections/*`만 호출하고, 모든 프롬프트/LLM 키/후처리는 서버에서 관리합니다.

---

## 1. 기술 스택
- **FastAPI + Uvicorn**: REST API 및 CORS 처리
- **SQLAlchemy (SQLite 기본)**: 사용자·리포트 저장
- **Pydantic v2 + pydantic-settings**: DTO 및 설정 관리
- **LangChain + langchain-google-genai**: Gemini 2.5 Flash 모델 연동

---

## 2. 디렉터리 구조
```
app/
├── api/                # FastAPI 라우터와 의존성 주입
├── core/               # 환경설정, 보안, 공통 유틸
├── db/                 # SQLAlchemy Base/세션
├── models/             # ORM 모델
├── repositories/       # 데이터 접근 레이어
├── schemas/            # Pydantic 요청/응답 모델
└── services/
    ├── reflection/     # LangChain 기반 감정·요약·채팅 서비스
    └── report_service.py
```

---

## 3. 빠른 시작
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows는 .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                # GEMINI_API_KEY 등 값을 채워 넣으세요
uvicorn app.main:app --reload
```
기본 헬스 체크: <http://localhost:8000/api/health>

자주 쓰는 명령:
```bash
uvicorn app.main:app --reload                       # 개발 서버
uvicorn app.main:app --host 0.0.0.0 --port 8000     # 운영 예시
python -m compileall app                            # 구문 검증
```

---

## 4. 환경 변수 (`.env`)
| 변수 | 설명 |
| --- | --- |
| `PROJECT_NAME` | FastAPI 문서/헬스에서 사용되는 이름 |
| `API_PREFIX` | 모든 라우터 prefix (기본 `/api`) |
| `DATABASE_URL` | SQLAlchemy 연결 문자열 |
| `GEMINI_MODEL` | 사용할 Gemini 모델 ID (기본 `gemini-2.0-flash`) |
| `GEMINI_API_KEY` | Google Generative AI API 키 (없으면 룰 기반으로 동작) |

키 발급: https://aistudio.google.com/app/apikey

---

## 5. LLM 활성화 동작
- `GEMINI_API_KEY` **존재**: LLM 경로 사용 → `emotionsDetailed`, `moodTimeline` 등 확장 필드 포함, 보다 풍부한 인사이트 제공
- `GEMINI_API_KEY` **없음**: 자동으로 규칙 기반 fallback → 핵심 필드(`summary`, `keyInsights`, `suggestedPhrases` 등)만 반환하지만 서비스는 정상 동작

모든 LangChain 체인은 `prompt → model → parser` 패턴이므로 새로운 분석을 추가할 때도 동일한 형태를 따르면 됩니다.

---

## 6. Reflection Reporting 상세

### 6.1 Emotion Taxonomy (16개 고정 라벨)
| 라벨 | 영어 | 극성 |
| ---- | ---- | ---- |
| 불안 | Anxiety | Negative |
| 당황 | Embarrassment | Negative |
| 화남 | Anger | Negative |
| 슬픔 | Sadness | Negative |
| 기쁨 | Joy | Positive |
| 죄책감 | Guilt | Negative |
| 수치심 | Shame | Negative |
| 안도 | Relief | Positive |
| 기대 | Expectation | Positive |
| 좌절 | Frustration | Negative |
| 실망 | Disappointment | Negative |
| 긴장 | Tension | Neutral |
| 혼란 | Confusion | Neutral |
| 짜증 | Irritation | Negative |
| 무력감 | Helplessness | Negative |
| 흥분 | Excitement | Positive |

대표적인 동의어 정규화: 걱정/초조 → 불안, 부끄러움 → 수치심, 짜증남 → 짜증, 분노 → 화남, 희열/즐거움 → 기쁨 등.

### 6.2 반환 필드
| 구분 | 필드 | 설명 |
| --- | --- | --- |
| **핵심 필드 (항상 포함)** | `summary`, `keyInsights`, `suggestedPhrases`, `emotions`, `decisionPoints`, `actionItems`, `confidence` | 1~3문장 요약, 인사이트/표현 2~5개, 감정 1~3개, 액션 최대 10개 |
| **확장 필드 (LLM 활성 시)** | `emotionsDetailed`, `moodTimeline` | 감정별 점수·근거, 시간대별 감정 흐름 |

### 6.3 주요 엔드포인트
- `POST /api/reflections/summary` : 상황을 입력하면 즉시 리포트 JSON을 반환 (저장 X)
- `POST /api/reflections/reports` : 세션 ID 기준으로 리포트를 생성·DB 저장 (Markdown + JSON)
- `GET /api/reflections/reports/{id}` : 저장된 리포트 조회 (`?format=md` 지원)
- `POST /api/reflections/chat` : 시뮬레이션 대화 메시지에 대한 AI 응답 반환

요약 요청 예시:
```json
{
  "whatHappened": "회의에서 의견 충돌이 있었다",
  "emotions": ["불안", "분노"],
  "whatYouDid": "즉각 반박했다",
  "howYouWishItHadGone": "차분하게 근거를 설명하고 싶었다"
}
```

응답 예시:
```json
{
  "summary": "두 사람이 의견 충돌로 갈등했지만 관계 회복을 원합니다.",
  "keyInsights": [
    "즉각적인 방어 반응이 갈등을 키웠습니다.",
    "사과를 미루면서 아쉬움이 커졌습니다."
  ],
  "suggestedPhrases": [
    "지금 생각해보니 감정이 앞섰던 것 같아.",
    "우리 관계가 소중해서 다시 이야기 나누고 싶어."
  ]
}
```

시뮬레이션 요청 (`/chat`)에서는 `personaName`, `personaTone`, `conversation`, `message` 필드를 포함해 AI가 역할극 형태로 답변합니다.

---

## 7. 검증 및 후처리
- **Label Normalization**: 동의어→정규 라벨, taxonomy 이외 단어는 제거
- **Evidence Validation**: LLM이 제시한 근거 텍스트가 실제 본문에 존재하는지 검사 (200자 제한)
- **Score Clamping**: 모든 점수를 0~1 사이로 제한, 잘못된 값은 0.5로 대체
- **Timeline Limiting**: 최대 8개 구간, 구간당 감정 2개까지만 허용
- LLM 실패·JSON 파싱 실패 시 자동으로 규칙 기반 로직으로 전환

---

## 8. 테스트 & Smoke 테스트
```bash
# 1) 헬스 체크
curl http://localhost:8000/api/health

# 2) 회고 요약
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

LLM 활성/비활성 모두 위 요청을 반복해 보며 `emotionsDetailed`, `moodTimeline` 포함 여부가 토글되는지 확인하면 됩니다.

---

## 9. 향후 개선 아이디어
1. **비동기 처리**: Redis/RQ 등을 통한 백그라운드 리포트 생성 및 상태 조회
2. **고급 검색**: 감정·날짜·세션 필터링, JSONB 기반 검색
3. **스피커 단위 분석**: 화자별 감정 흐름, 대화 역동성 분석
4. **장기 추세**: 사용자별 감정 패턴, 대시보드, 비교 분석

이 문서를 기반으로 백엔드 구조를 이해하고 필요한 확장 작업을 진행하면 됩니다.
