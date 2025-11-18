# Reflection Reporting Feature

## Overview

The reflection reporting feature provides deep emotion analysis for user reflections, generating comprehensive reports with emotion taxonomy, detailed insights, and action items. The system uses a fixed Korean emotion taxonomy and supports both LLM-based analysis and rule-based fallback.

## Goal

Enhance the existing synchronous reflection report feature with:
- Deeper emotion analysis using a fixed Korean emotion taxonomy
- JSON-only LLM prompt with robust post-processing
- Production-safe P0 implementation
- Public API compatibility preservation
- No database schema changes

## Emotion Taxonomy

The system uses a fixed set of 16 Korean emotion labels:

| Label | English | Polarity |
|-------|---------|----------|
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

### Synonym Mapping

The system normalizes common synonyms to canonical labels:
- 걱정 → 불안
- 초조 → 불안
- 부끄러움 → 수치심
- 짜증남 → 짜증
- 분노 → 화남
- 희열 → 기쁨
- 즐거움 → 기쁨

## Model Fields

### Core Fields (Always Present)
- `summary` (string): 1-3 sentence summary
- `keyInsights` (array of strings): 2-5 key insights
- `suggestedPhrases` (array of strings): 2-5 suggested phrases
- `emotions` (array of strings): Top 1-3 emotion labels from taxonomy
- `decisionPoints` (array of strings): 1-5 decision points
- `actionItems` (array of objects): 1-10 action items with optional owner/due date
- `confidence` (float): Confidence score between 0.0-1.0

### Extended Fields (Available Only When LLM is Enabled)

**Note:** These fields are only included when `GEMINI_API_KEY` is configured and the LLM successfully processes the request.

- `emotionsDetailed` (array of objects): Detailed emotion analysis with:
  - `label` (string): Emotion from taxonomy
  - `score` (float): Confidence score 0-1
  - `polarity` (string): "neg", "neu", or "pos"
  - `vad` (object): Valence, arousal, dominance values
  - `evidence` (string): Supporting text (max 200 chars)
  - `spans` (array): Text position markers
- `moodTimeline` (array of objects): 3-6 temporal segments with:
  - `t` (integer): Time segment index
  - `labels` (array): Top 2 emotions with scores

## API Usage

### POST /api/reflections/summary

Generate a reflection summary without persistence.

**Request:**
```json
{
  "whatHappened": "회의에서 의견 충돌이 있었다",
  "emotions": ["불안", "화남"],
  "whatYouDid": "즉각 반박했다",
  "howYouWishItHadGone": "차분하게 근거를 설명하고 싶었다"
}
```

**Response (Public Fields):**
```json
{
  "summary": "회의 중 의견 충돌로 감정적 반응을 보였으며, 더 차분한 대응을 원했습니다.",
  "keyInsights": [
    "즉각적인 방어 반응이 갈등을 키웠습니다",
    "차분한 커뮤니케이션의 필요성을 인식했습니다"
  ],
  "suggestedPhrases": [
    "제 의견을 정리해서 다시 말씀드려도 될까요?",
    "감정적으로 대응해서 죄송합니다"
  ],
  "emotions": ["불안", "화남", "후회"],
  "decisionPoints": ["향후 유사 상황에서 먼저 심호흡하기로 결정"],
  "actionItems": [
    {
      "text": "팀장님께 사과 메일 보내기",
      "owner": null,
      "due": "2025-01-20"
    }
  ],
  "confidence": 0.85
}
```

### POST /api/reflections/reports

Create and persist a report with extended fields.

**Request:**
```json
{
  "sessionId": 123,
  "requestor": "user@example.com"
}
```

**Response:**
```json
{
  "report_id": 1,
  "session_id": "123",
  "status": "finished",
  "created_at": "2025-01-15T10:30:00Z",
  "processed_at": "2025-01-15T10:30:05Z",
  "report_json": {
    "summary": "...",
    "keyInsights": [...],
    "emotions": ["불안", "화남"],
    "emotionsDetailed": [
      {
        "label": "불안",
        "score": 0.8,
        "polarity": "neg",
        "vad": {"valence": 0.2, "arousal": 0.7, "dominance": 0.3},
        "evidence": "회의에서 의견 충돌",
        "spans": [{"start": 0, "end": 12}]
      }
    ],
    "moodTimeline": [
      {
        "t": 0,
        "labels": [
          {"label": "긴장", "score": 0.7},
          {"label": "불안", "score": 0.6}
        ]
      }
    ]
  },
  "report_md": "# 리포트..."
}
```

### GET /api/reflections/reports/{reportId}

Retrieve a report.

**Query Parameters:**
- `format`: "json" (default) or "md"

**Response (format=json):**
```json
{
  "report_id": 1,
  "session_id": "123",
  "status": "finished",
  "created_at": "2025-01-15T10:30:00Z",
  "processed_at": "2025-01-15T10:30:05Z",
  "report_json": {
    "summary": "...",
    "emotionsDetailed": [...],
    "moodTimeline": [...]
  }
}
```

**Response (format=md):**
Returns plain Markdown text.

## Architecture

### Components

1. **emotion_taxonomy.py**: Fixed Korean emotion labels, synonyms, polarity, and VAD mappings
2. **prompt_templates.py**: Strict JSON-only LLM prompts
3. **emotion_postprocess.py**: Validation and normalization utilities
4. **langchain.py**: LLM integration with rule-based fallback
5. **report_service.py**: Report generation and persistence

### Processing Flow

```
User Input
    ↓
LangChainService.summarize_reflection()
    ↓
[Try LLM Path]
    ↓
_invoke_llm_summary() → Parse JSON
    ↓
postprocess_emotions() → Normalize labels, validate evidence
    ↓
clamp_mood_timeline() → Limit segments
    ↓
Return with extended fields
    
[Fallback: Rule-Based Path]
    ↓
DummyChain/existing logic
    ↓
Return core fields only
```

### Backwards Compatibility

- If no LLM configured: System uses existing rule-based approach
- Public API fields unchanged
- Extended fields (emotionsDetailed, moodTimeline) are optional
- Existing clients continue to work without changes

## Configuration

### Enabling the LLM Path

The system supports two analysis modes:

1. **LLM-based analysis (with `GEMINI_API_KEY`):**
   - Provides richer results with `emotionsDetailed` and `moodTimeline`
   - More accurate insights and suggestions
   - Requires valid Google Generative AI API key

2. **Rule-based fallback (without `GEMINI_API_KEY`):**
   - Works without any API key
   - Returns core fields only
   - No errors or degradation

To enable the LLM path:

1. Get an API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Set the environment variable:
   ```bash
   GEMINI_API_KEY=your_api_key_here
   GEMINI_MODEL=gemini-2.0-flash  # Optional, this is the default
   ```
3. Restart the server

The LangChainService is automatically configured by the dependency injection system:

```python
# app/api/dependencies.py
def get_langchain_service(settings: Settings = Depends(get_settings_dependency)):
    llm = create_llm(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)
    return LangChainService(settings=settings, llm=llm)
```

If `GEMINI_API_KEY` is not set or the LLM fails to initialize, `create_llm()` returns `None` and the service gracefully falls back to rule-based analysis.

## Validation and Post-Processing

### Label Normalization
- Applies synonym mapping
- Validates against EMOTION_TAXONOMY_KO
- Rejects invalid labels

### Evidence Validation
- Ensures evidence substring exists in full text
- Limits evidence to 200 characters
- Generates span positions if found
- Returns empty evidence if not found

### Score Clamping
- All scores clamped to [0, 1] range
- Invalid scores default to 0.5

### Timeline Limiting
- Maximum 8 time segments
- Maximum 2 emotions per segment
- Emotions sorted by score

## Future Work

Out of scope for P0, planned for future iterations:

1. **Asynchronous Processing**
   - Background worker for report generation
   - /status endpoint for progress tracking
   - Queue-based architecture

2. **Advanced Search**
   - Filter reports by emotion, date range, session
   - JSONB migration for efficient querying
   - Full-text search on report content

3. **Speaker-Level Analysis**
   - Per-speaker emotion tracking
   - Conversation dynamics analysis
   - Turn-by-turn emotion flow

4. **Long-Term Trends**
   - User emotion patterns over time
   - Trend dashboards
   - Comparative analytics

## Testing

Manual smoke tests should verify:

1. **POST /api/reflections/summary** returns valid public schema
2. **POST /api/reflections/reports** persists with extended fields when LLM available
3. **GET /api/reflections/reports/{id}?format=json** returns persisted JSON
4. **GET /api/reflections/reports/{id}?format=md** returns Markdown with `Content-Type: text/markdown`
5. No LLM configuration: System uses fallback without errors

### Testing with LLM Enabled

Set `GEMINI_API_KEY` in `.env` and run:

```bash
# Summary endpoint - should include emotionsDetailed and moodTimeline in response
curl -X POST http://localhost:8000/api/reflections/summary \
  -H "Content-Type: application/json" \
  -d '{
    "whatHappened": "회의에서 충돌",
    "whatYouDid": "반박했다",
    "howYouWishItHadGone": "차분하게 설명"
  }'

# Create report - should persist extended fields
curl -X POST http://localhost:8000/api/reflections/reports \
  -H "Content-Type: application/json" \
  -d '{"sessionId": 123}'

# Get report (JSON) - should show emotionsDetailed and moodTimeline
curl http://localhost:8000/api/reflections/reports/1

# Get report (Markdown) - should return text/markdown content type
curl -i http://localhost:8000/api/reflections/reports/1?format=md
```

### Testing with LLM Disabled (Fallback Mode)

Remove or comment out `GEMINI_API_KEY` in `.env` and run the same commands:

```bash
# Summary endpoint - should return core fields only (no emotionsDetailed/moodTimeline)
curl -X POST http://localhost:8000/api/reflections/summary \
  -H "Content-Type: application/json" \
  -d '{
    "whatHappened": "회의에서 충돌",
    "whatYouDid": "반박했다",
    "howYouWishItHadGone": "차분하게 설명"
  }'

# Create report
curl -X POST http://localhost:8000/api/reflections/reports \
  -H "Content-Type: application/json" \
  -d '{"sessionId": 123}'

# Get report (JSON)
curl http://localhost:8000/api/reflections/reports/1

# Get report (Markdown)
curl http://localhost:8000/api/reflections/reports/1?format=md
```

## Error Handling

- LLM failures gracefully fall back to rule-based approach
- JSON parsing errors trigger fallback
- Invalid emotion labels are filtered out
- Missing evidence is handled with empty strings
- All errors logged for monitoring
