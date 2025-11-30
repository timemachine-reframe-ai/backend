from typing import Optional
from sqlalchemy.orm import Session

from app.services import ChatService


def generate_report_for_session(
    db: Session,
    session_id: str | int,
    conversation_text: str,
    service: ChatService,
    requestor: Optional[str] = None,
    user_name: str = "사용자",
) -> dict:
    """
    동기 리포트 생성:
    - 프런트에서 전달한 대화 전문을 사용
    - ChatService summarize_reflection 호출
    - Markdown + JSON 구성
    """
    if not conversation_text.strip():
        raise ValueError("conversation_text must not be empty")

    payload = {
        "what_happened": conversation_text,
        "emotions": [],  # 자동 감정 추출 유도
        "what_you_did": "",
        "desired_outcome": "",
        "user_name": user_name,  # 사용자 이름 전달
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
        "decisionPoints": summary_struct.get("decisionPoints", []),
        "actionItems": summary_struct.get("actionItems", []),
        "confidence": summary_struct["confidence"],
    }

    # Include extended fields if available from LLM path
    if "emotionsDetailed" in summary_struct:
        report_json["emotionsDetailed"] = summary_struct["emotionsDetailed"]
    if "moodTimeline" in summary_struct:
        report_json["moodTimeline"] = summary_struct["moodTimeline"]

    # RAG 강화된 새 필드들
    
    # 심리상담사의 조언 (핵심 필드)
    if "counselorAdvice" in summary_struct:
        report_json["counselorAdvice"] = summary_struct["counselorAdvice"]
        md_lines.insert(4, "\n## 💙 심리상담사의 조언")
        md_lines.insert(5, summary_struct["counselorAdvice"])
    
    # 심리학적 분석
    if "psychologicalNote" in summary_struct:
        report_json["psychologicalNote"] = summary_struct["psychologicalNote"]
        md_lines.append("\n## 심리학적 분석")
        md_lines.append(summary_struct["psychologicalNote"])
    
    # 격려 메시지
    if "encouragement" in summary_struct:
        report_json["encouragement"] = summary_struct["encouragement"]
        md_lines.append("\n## 상담사의 한마디")
        md_lines.append(summary_struct["encouragement"])

    return {"report_md": report_md, "report_json": report_json}
