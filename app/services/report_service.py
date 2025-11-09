"""
Report service skeleton integrated to existing FastAPI + LangChain codebase.

- enqueue_report_generation: insert Reports row (pending) and enqueue an RQ job
- generate_report_sync: worker function (sync) that produces report_md and report_json
- call_gemini_alternatives: stub that should be replaced by existing LangChain Runnable chain
"""

import json
import re
from datetime import datetime
from sqlalchemy import insert, select, update
from app.models.report import Report
from app.models.chat import Chat  # adjust import to the repo's Chat model path
from app.db.session import get_db_sync  # implement or reuse sync DB helper for worker
from app.utils.pii import mask_pii  # implement or reuse masking util
from app.core.config import get_settings
from redis import Redis
from rq import Queue

settings = get_settings()

# Redis queue
REDIS_URL = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
redis_conn = Redis.from_url(REDIS_URL)
queue = Queue("reports", connection=redis_conn, default_timeout=1800)

# decision point regex (Korean)
DECISION_RE = re.compile(r"(할까요|할게요|결국|하기로|결정|선택|할래요|해볼게요|해볼까요|하기로 했어요|정했어요|결정했어요)", re.I)

async def enqueue_report_generation(db: 'AsyncSession', session_id: int, requestor: str = None):
    q = insert(Report).values(session_id=session_id, status="pending", requested_by=requestor, created_at=datetime.utcnow()).returning(Report.report_id)
    res = await db.execute(q)
    report_id = res.scalar_one()
    # enqueue background job (worker executes generate_report_sync)
    queue.enqueue("app.services.report_service.generate_report_sync", report_id, session_id)
    return report_id

def generate_report_sync(report_id: int, session_id: int):
    """
    Worker entrypoint (sync). Steps:
      - fetch chats for session
      - detect decision points
      - ensure sentiment info available (use Chat.sentiment_label if present)
      - call LangChain/Gemini (adapter) to generate alternatives
      - assemble markdown + json and update Reports row
    """
    db = get_db_sync()
    chats = db.execute(select(Chat).where(Chat.session_id == session_id).order_by(Chat.timestamp)).scalars().all()
    if not chats:
        db.execute(update(Report).where(Report.report_id == report_id).values(status="failed", report_md="No chats found", processed_at=datetime.utcnow()))
        db.commit()
        return

    # detect decision points
    points = []
    for c in chats:
        if c.sender == "user" and c.message and DECISION_RE.search(c.message):
            points.append({"chat_id": c.chat_id, "ts": c.timestamp.isoformat(), "text": c.message, "sentiment_label": getattr(c, "sentiment_label", None), "sentiment_score": getattr(c, "sentiment_score", None)})

    snippet = " / ".join([mask_pii(m.message) for m in chats[:6]])

    points_with_alts = []
    for p in points:
        safe_text = mask_pii(p["text"])
        alts = call_gemini_alternatives(snippet, safe_text)
        p["alternatives"] = alts
        p["recommended"] = alts[0]["title"] if alts else None
        points_with_alts.append(p)

    aha = f"{len(points_with_alts)} decision points detected." if points_with_alts else "No clear decision points detected."
    next_action = points_with_alts[0]["alternatives"][0]["script"] if points_with_alts else None

    report_json = {"summary": {"session_id": session_id, "aha": aha, "snippet": snippet}, "points": points_with_alts, "next_action": next_action}
    report_md = build_markdown(report_json)

    db.execute(update(Report).where(Report.report_id == report_id).values(status="done", report_md=report_md, report_json=json.dumps(report_json), processed_at=datetime.utcnow()))
    db.commit()

def build_markdown(report_json: dict) -> str:
    lines = []
    s = report_json["summary"]
    lines.append(f"# 회고 리포트 — 세션 {s['session_id']}")
    lines.append(f"## 핵심 아하 포인트\n- {s.get('aha')}\n")
    for p in report_json.get("points", []):
        lines.append(f"### [{p['ts']}] {p['text']}")
        lines.append(f"- 감정: {p.get('sentiment_label')}")
        for alt in p.get("alternatives", []):
            lines.append(f"  - **{alt['title']}**: {alt['summary']}")
            lines.append(f"    - 장점: {'; '.join(alt.get('pros', []))}")
            lines.append(f"    - 단점: {'; '.join(alt.get('cons', []))}")
            lines.append(f"    - 스크립트: \"{alt.get('script')}\"")
        lines.append("")
    if report_json.get("next_action"):
        lines.append("## 다음 행동\n")
        lines.append(f"- {report_json['next_action']}\n")
    return "\n".join(lines)

# Adapter stub: integrate with your existing LangChain Runnable chain
def call_gemini_alternatives(context_snippet: str, point_text: str):
    """
    Replace this stub with a call into your existing LangChain Runnable/chains that use Gemini.
    Example integration point: app.services.reflection_chains.generate_alternatives(context, point)
    For now this returns fallback alternatives.
    """
    fallback = [
        {"title":"의도 확인하기", "summary":"핵심 범위를 확인하고 맡기기", "pros":["부담 감소"], "cons":["추가 커뮤니케이션"], "script":"핵심으로 꼭 필요한 항목이 무엇인지 먼저 정할까요?"},
        {"title":"분할·위임 제안", "summary":"작업을 쪼개 일부 위임/기한 조정", "pros":["품질 유지"], "cons":["조정 시간"], "script":"제가 A 파트를 맡고, B 파트는 누구에게 부탁하면 어떨까요?"}
    ]
    return fallback

# helper to fetch report by id (used by API)
def get_report_by_id(db):
    # simple helper – implement properly (or use repository pattern)
    q = select(Report).where(Report.report_id == db)  # placeholder, implement based on your DB helpers
    return None
