from datetime import datetime
import json
from typing import Optional
from sqlalchemy.orm import Session

from app.models.report import Report
from app.services.langchain import LangChainService


def _fetch_session_text(db: Session, session_id: str | int) -> str:
    """
    TODO: 실제 Session 모델/메시지에서 텍스트를 조합.
    현재는 임시 문자열 반환.
    """
    return f"세션 {session_id} 회의에서 논의된 주요 내용 예시입니다."


def generate_report_for_session(
    db: Session,
    session_id: str | int,
    service: LangChainService,
    requestor: Optional[str] = None,
) -> dict:
    """
    동기 리포트 생성:
    - 세션 텍스트 수집
    - LangChainService summarize_reflection 호출
    - Markdown + JSON 구성
    """
    session_text = _fetch_session_text(db, session_id)
    payload = {
        "what_happened": session_text,
        "emotions": [],  # 자동 감정 추출 유도
        "what_you_did": "",
        "desired_outcome": "",
    }
    summary_struct = service.summarize_reflection(payload)

    md_lines = [
        f"# 리포트 (세션 {session_id})",
        "",
        "## 요약",
        summary_struct["summary"] or "",
    ]
    if summary_struct["keyInsights"]:
        md_lines.append("\n## 주요 인사이트")
        for ki in summary_struct["keyInsights"]:
            md_lines.append(f"- {ki}")
    if summary_struct["suggestedPhrases"]:
        md_lines.append("\n## 추천 표현")
        for sp in summary_struct["suggestedPhrases"]:
            md_lines.append(f"- {sp}")
    if summary_struct["decisionPoints"]:
        md_lines.append("\n## 결정 사항")
        for dp in summary_struct["decisionPoints"]:
            md_lines.append(f"- {dp}")
    if summary_struct["actionItems"]:
        md_lines.append("\n## 액션 아이템")
        for ai in summary_struct["actionItems"]:
            owner = f" (@{ai['owner']})" if ai.get("owner") else ""
            due = f" (due: {ai['due']})" if ai.get("due") else ""
            md_lines.append(f"- {ai['text']}{owner}{due}")
    md_lines.append("\n## 감정(추출)")
    if summary_struct["emotions"]:
        md_lines.append(", ".join(summary_struct["emotions"]))
    else:
        md_lines.append("없음")
    md_lines.append("\n## Confidence")
    md_lines.append(str(summary_struct["confidence"]))

    report_md = "\n".join(md_lines)

    report_json = {
        "summary": summary_struct["summary"],
        "keyInsights": summary_struct["keyInsights"],
        "suggestedPhrases": summary_struct["suggestedPhrases"],
        "emotions": summary_struct["emotions"],
        "decisionPoints": summary_struct["decisionPoints"],
        "actionItems": summary_struct["actionItems"],
        "confidence": summary_struct["confidence"],
    }

    return {"report_md": report_md, "report_json": report_json}
