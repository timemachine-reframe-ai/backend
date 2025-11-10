import re as _re_for_report
from datetime import datetime
from typing import Optional, List, Dict, Any

# 간단 PII 마스킹(운영 전 보안/컴플라이언스 점검 권장)
_email_re = _re_for_report.compile(r"([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})")
_phone_re = _re_for_report.compile(r"(\+?\d{1,3}[-.\s]?)?(\d{2,4}[-.\s]?){1,4}\d{2,4}")
_rrn_re = _re_for_report.compile(r"\b\d{6}[-\s]?\d{7}\b")

def _mask_pii(text: Optional[str]) -> Optional[str]:
    """간단 PII 마스킹: 이메일->[EMAIL], 전화->[PHONE], 주민등록번호류->[ID]."""
    if text is None:
        return None
    t = str(text)
    t = _email_re.sub("[EMAIL]", t)
    t = _rrn_re.sub("[ID]", t)
    t = _phone_re.sub("[PHONE]", t)
    return t

# 의사결정 포인트 탐지용 한글 휴리스틱 정규식
_DECISION_RE = _re_for_report.compile(
    r"(할까요|할게요|결국|하기로|결정|선택|할래요|해볼게요|해볼까요|하기로 했어요|정했어요|결정했어요)",
    re.I,
)

def generate_alternatives_for_point(context_snippet: str, point_text: str) -> List[Dict[str, Any]]:
    """
    대안 생성(임시). LangChain 체인으로 교체 가능.
    """
    return [
        {
            "title": "의도 확인하기",
            "summary": "핵심 범위만 정해서 우선 처리 제안",
            "pros": ["부담 감소"],
            "cons": ["추가 커뮤니케이션 필요"],
            "script": "핵심으로 꼭 필요한 항목이 무엇인지 먼저 정할까요? 제가 그 부분만 맡아서 먼저 진행해볼게요.",
        },
        {
            "title": "분할·위임 제안",
            "summary": "작업을 쪼개 일부 위임하거나 기한을 조정",
            "pros": ["품질 유지", "과부하 방지"],
            "cons": ["조정 시간 필요"],
            "script": "제가 A 파트를 맡고, B 파트는 누구에게 부탁하면 어떨까요?",
        },
    ]

def generate_report_for_session(db, session_id: int, requestor: Optional[str] = None) -> Dict[str, Any]:
    """
    동기 프로토타입 리포트 생성기.
    - Chat 모델에서 해당 세션의 채팅을 조회→의사결정 포인트 탐지→대안 생성→마크다운/JSON 반환
    - 현재 DB에 저장하지 않습니다(운영 시 저장/비동기 큐로 확장 권장).
    """
    from app.models.chat import Chat  # lazy import: 실제 모델 필드명과 일치해야 합니다.

    # Chat 테이블에서 session_id에 해당하는 행을 시간순으로 조회
    chats = db.query(Chat).filter(Chat.session_id == session_id).order_by(Chat.timestamp).all()
    if not chats:
        raise ValueError(f"session_id={session_id} 에 대한 채팅 데이터가 없습니다.")

    # 간단한 컨텍스트 스니펫(상위 6개 메시지, PII 마스킹)
    snippet = " / ".join([_mask_pii(getattr(c, "message", "") or "") for c in chats[:6]])

    # 의사결정 포인트 탐지
    points = []
    for c in chats:
        if getattr(c, "sender", None) == "user" and getattr(c, "message", None) and _DECISION_RE.search(c.message):
            points.append({
                # chat_id 필드명이 다르면 id로 대체
                "chat_id": getattr(c, "chat_id", getattr(c, "id", None)),
                "ts": c.timestamp.isoformat() if hasattr(c.timestamp, "isoformat") else str(c.timestamp),
                "text": c.message,
                "sentiment_label": getattr(c, "sentiment_label", None),
                "sentiment_score": getattr(c, "sentiment_score", None),
            })

    # 각 포인트에 대해 대안 생성
    points_with_alts = []
    for p in points:
        safe_text = _mask_pii(p["text"])
        alts = generate_alternatives_for_point(snippet, safe_text)
        p["alternatives"] = alts
        p["recommended"] = alts[0]["title"] if alts else None
        points_with_alts.append(p)

    aha = f"{len(points_with_alts)}개의 의사결정 포인트를 감지했습니다." if points_with_alts else "명확한 의사결정 포인트가 발견되지 않았습니다."
    next_action = points_with_alts[0]["alternatives"][0]["script"] if points_with_alts else None

    report_json = {
        "summary": {"session_id": session_id, "aha": aha, "snippet": snippet},
        "points": points_with_alts,
        "next_action": next_action,
        "meta": {"generated_at": datetime.utcnow().isoformat(), "method": "inline-sync-kr-prototype"},
    }

    # 마크다운 생성(읽기 쉬운 한글 형식)
    md_lines = []
    md_lines.append(f"# 회고 리포트 — 세션 {session_id}")
    md_lines.append(f"기간: {chats[0].timestamp} ~ {chats[-1].timestamp}")
    md_lines.append("")
    md_lines.append("## 핵심 아하 포인트")
    md_lines.append(f"- {aha}")
    md_lines.append("")
    md_lines.append("## 주요 의사결정 포인트")
    for p in points_with_alts:
        md_lines.append(f"### [{p['ts']}] {_mask_pii(p['text'])}")
        md_lines.append(f"- 감정: {p.get('sentiment_label')}")
        for alt in p.get("alternatives", []):
            md_lines.append(f"  - **{alt['title']}**: {alt['summary']}")
            md_lines.append(f"    - 장점: {'; '.join(alt.get('pros', []))}")
            md_lines.append(f"    - 단점: {'; '.join(alt.get('cons', []))}")
            md_lines.append(f"    - 스크립트: \"{alt.get('script')}\"")
        md_lines.append("")

    if next_action:
        md_lines.append("## 다음 행동(권장)")
        md_lines.append(f"- {next_action}")
        md_lines.append("")

    report_md = "\n".join(md_lines)

    return {"report_md": report_md, "report_json": report_json}
# --- END append ---
