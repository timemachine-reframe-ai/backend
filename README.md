# 🕰️ TIMEMACHINE AI – 백엔드

FastAPI 기반 AI 상담 서버입니다. **13,234개의 실제 상담 데이터**를 RAG로 활용하여 전문 심리상담사 같은 조언을 생성합니다.

---

## 📁 프로젝트 구조

```
backend/
├── app/
│   ├── api/routes/              # FastAPI 엔드포인트
│   │   ├── reflections.py       # /api/reflections/chat, summary
│   │   ├── report_write_routes.py  # /api/reflections/reports (생성)
│   │   └── report_read_routes.py   # /api/reflections/reports (조회)
│   │
│   ├── services/
│   │   ├── reflection/
│   │   │   ├── chat_service.py      # 💬 채팅 + RAG 연동
│   │   │   └── prompt_templates.py  # 🎭 프롬프트 템플릿
│   │   ├── report_service.py        # 📊 리포트 생성
│   │   └── rag_service.py           # 🔍 RAG 서비스 (NEW)
│   │
│   ├── data/
│   │   ├── counsel_data.jsonl       # 📄 상담 데이터 (13,234개)
│   │   └── chroma_db/               # 🗄️ 벡터 DB (52MB)
│   │
│   ├── scripts/
│   │   └── build_vector_db.py       # 벡터 DB 빌드 스크립트
│   │
│   ├── models/                  # SQLAlchemy ORM
│   ├── schemas/                 # Pydantic 스키마
│   ├── core/                    # 설정, 보안
│   └── db/                      # DB 세션
│
├── requirements.txt
└── .env
```

---

## 🚀 빠른 시작

```bash
# 1. 가상환경 생성 및 활성화
cd backend
python3 -m venv .venv
source .venv/bin/activate

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 환경변수 설정
cp .env.example .env
# GEMINI_API_KEY 입력

# 4. 벡터 DB 빌드 (최초 1회)
python -m app.scripts.build_vector_db

# 5. 서버 실행
uvicorn app.main:app --reload
```

---

## 🔍 RAG 시스템

### 개요

RAG(Retrieval Augmented Generation)를 통해 유사한 상담 사례를 검색하여 LLM 응답 품질을 향상시킵니다.

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAG 동작 흐름                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1️⃣ 사용자 입력                                                 │
│  "직장에서 상사에게 부당한 지적을 받았어요"                      │
│                              │                                  │
│                              ▼                                  │
│  2️⃣ 벡터 임베딩 생성 (sentence-transformers)                   │
│  [0.23, -0.15, 0.87, ...]                                       │
│                              │                                  │
│                              ▼                                  │
│  3️⃣ ChromaDB 유사도 검색 (상위 3개)                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 📄 유사 사례 1: 회사에서 팀장이 부당하게 질책했을 때...    │  │
│  │ 📄 유사 사례 2: 직장 내 갑질을 경험했을 때...              │  │
│  │ 📄 유사 사례 3: 상사와의 갈등으로 스트레스를 받을 때...    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  4️⃣ LLM에 컨텍스트로 전달 → 전문 상담사 조언 생성              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 상담 데이터 통계

| 항목         | 값                                    |
| ------------ | ------------------------------------- |
| 총 레코드    | 13,234개                              |
| 벡터 DB 크기 | 52MB                                  |
| 임베딩 모델  | paraphrase-multilingual-MiniLM-L12-v2 |
| 검색 결과    | 상위 3개                              |

### 카테고리 분포

```
직장/취업 ████████████████████████░░░░░░  56% (7,432개)
가족      ██████████░░░░░░░░░░░░░░░░░░░░  20% (2,649개)
대인관계  █████░░░░░░░░░░░░░░░░░░░░░░░░░  13% (1,728개)
연애      ███░░░░░░░░░░░░░░░░░░░░░░░░░░░   7% (893개)
기타      █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   4% (532개)
```

### 데이터 구조

```json
{
  "user_context": "직장에서 상사가 나에게만 업무를 몰아줘요",
  "emotion": "두려움",
  "category": "직장/취업",
  "expert_solution": "지금 많이 힘드시겠어요...",
  "psychological_rationale": "조직 공정성 이론에 따르면..."
}
```

---

## 📊 API 엔드포인트

### 채팅 (시뮬레이션)

```bash
POST /api/reflections/chat
```

페르소나 기반 대화 응답 생성. RAG로 유사 상담 사례를 참고합니다.

### 리포트 생성

```bash
POST /api/reflections/reports
```

대화 내용을 분석하여 리포트 생성. **심리상담사 조언** 포함.

### 리포트 응답 구조

```json
{
  "summary": "상황 요약",
  "keyInsights": ["인사이트 1", "인사이트 2"],
  "suggestedPhrases": ["추천 표현 1", "추천 표현 2"],
  "counselorAdvice": "💙 RAG 기반 심리상담사 조언",
  "psychologicalNote": "심리학적 분석",
  "encouragement": "격려 메시지",
  "emotions": ["감정1", "감정2"],
  "confidence": 0.85
}
```

---

## 🔧 환경 변수

| 이름             | 설명                             |
| ---------------- | -------------------------------- |
| `GEMINI_API_KEY` | Google Gemini API 키 (필수)      |
| `GEMINI_MODEL`   | 모델 ID (기본: gemini-2.0-flash) |
| `DATABASE_URL`   | SQLAlchemy 연결 문자열           |
| `PROJECT_NAME`   | 프로젝트 이름                    |
| `API_PREFIX`     | API 경로 접두사 (기본: /api)     |

---

## 🛠️ 주요 명령어

```bash
# 개발 서버 실행
uvicorn app.main:app --reload

# 벡터 DB 빌드 (데이터 변경 시)
python -m app.scripts.build_vector_db

# 헬스 체크
curl http://localhost:8000/health
```

---

## 📝 주의사항

- `chroma_db/` 폴더는 `.gitignore`에 포함되어 있습니다
- 새 환경에서는 반드시 `python -m app.scripts.build_vector_db` 실행 필요
- Gemini API 키가 없으면 규칙 기반 로직으로 자동 전환됩니다

---

## 🆕 최근 업데이트 (2025.11.30)

| 기능                 | 설명                                                  |
| -------------------- | ----------------------------------------------------- |
| **RAG 시스템**       | 13,234개 상담 데이터 기반 유사 사례 검색              |
| **심리상담사 조언**  | RAG로 검색된 유사 사례를 참고한 전문 상담사 톤의 조언 |
| **사용자 이름 호칭** | 회원가입 시 입력한 이름으로 조언에서 호칭             |
| **프롬프트 개선**    | Few-shot 예시, 비언어적 표현, 심리학적 분석 강화      |
