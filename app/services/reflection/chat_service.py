import json
import logging
from typing import List, Mapping, Optional, Any

from .prompt_templates import SUMMARY_JSON_PROMPT, CHAT_PROMPT, RAG_CONTEXT_TEMPLATE
from .emotion_postprocess import postprocess_emotions, clamp_mood_timeline

# RAG 서비스 import (옵션)
try:
    from ..rag_service import get_rag_service
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

logger = logging.getLogger(__name__)


class ChatService:
    """
    LangChain 기반 Reflection/Chat 서비스.
    - summarize_reflection: JSON 기반 회고 분석 (RAG 강화)
    - generate_chat_reply: persona 기반 대화 응답 생성
    """

    def __init__(self, settings=None, llm: Optional[Any] = None):
        self.settings = settings
        self.llm = llm
        # RAG 서비스 초기화
        self._rag_service = get_rag_service() if RAG_AVAILABLE else None
        if self._rag_service:
            logger.info("RAG 서비스가 ChatService에 통합되었습니다.")

    # --------------------------
    # Utilities
    # --------------------------

    def _safe_parse_json(self, raw: str) -> dict:
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def _normalize_array(self, value) -> List[str]:
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        return []

    def _split_sentences(self, text: str) -> List[str]:
        parts = text.replace("!", ".").replace("?", ".").split(".")
        return [p.strip() for p in parts if p.strip()]

    # --------------------------
    # Emotion & Decision Extraction (fallback)
    # --------------------------

    def detect_emotions(self, text: str, max_items: int = 3) -> List[str]:
        lowered = text.lower()
        rules = [
            ("불안", ["불안", "걱정", "초조", "anx"]),
            ("당황", ["당황", "황당", "embarrass", "awkward"]),
            ("화남", ["화나", "짜증", "분노", "angry"]),
            ("슬픔", ["슬픔", "우울", "sad"]),
            ("기쁨", ["기쁨", "행복", "즐거", "happy"]),
            ("죄책감", ["죄책", "미안", "guilt"]),
        ]
        found = []
        for label, keys in rules:
            if any(k in lowered for k in keys):
                found.append(label)
        if not found:
            found = ["불안"]

        dedup, seen = [], set()
        for f in found:
            if f not in seen:
                dedup.append(f)
                seen.add(f)

        return dedup[:max_items]

    def _extract_decisions(self, base_text: str) -> List[str]:
        sentences = self._split_sentences(base_text)
        keywords = ["결정", "하기로", "선택", "결론", "합의", "정하기"]
        result = []
        for s in sentences:
            if any(k in s for k in keywords):
                result.append(s[:150])
        return result[:5]

    def _extract_action_items(self, base_text: str) -> List[dict]:
        sentences = self._split_sentences(base_text)
        keywords = ["해야", "준비", "정리", "확인", "작성", "검토", "추가"]
        items = []
        import re

        for s in sentences:
            if any(k in s for k in keywords):
                item = {"text": s[:150], "owner": None, "due": None}

                if "@" in s:
                    owner_part = s.split("@", 1)[1].split(" ", 1)[0]
                    if owner_part:
                        item["owner"] = owner_part[:30]

                m = re.search(r"\d{4}-\d{2}-\d{2}", s)
                if m:
                    item["due"] = m.group(0)

                items.append(item)

        return items[:10]

    # --------------------------
    # LLM Summary (RAG Enhanced)
    # --------------------------

    def _get_rag_context(self, text: str, emotions: List[str] = None) -> str:
        """RAG를 사용하여 유사 상담 사례 컨텍스트 생성"""
        if not self._rag_service:
            return ""

        try:
            context = self._rag_service.get_context_for_report(
                conversation_text=text,
                emotions=emotions,
                n_results=3,
            )
            if context:
                return RAG_CONTEXT_TEMPLATE.format(similar_cases=context)
            return ""
        except Exception as e:
            logger.warning(f"RAG 컨텍스트 생성 실패: {e}")
            return ""

    def _invoke_llm_summary(self, text: str, emotions: List[str] = None, user_name: str = "사용자") -> Optional[dict]:
        if not self.llm:
            return None

        try:
            # RAG 컨텍스트 추가
            rag_context = self._get_rag_context(text, emotions)

            prompt = SUMMARY_JSON_PROMPT.format(
                input_text=text,
                rag_context=rag_context,
                user_name=user_name,
            )
            response = self.llm.invoke(prompt)

            raw_text = response.content if hasattr(response, "content") else str(response)
            raw_text = raw_text.strip()

            start = raw_text.find("{")
            end = raw_text.rfind("}")
            if start >= 0 and end >= start:
                raw_text = raw_text[start : end + 1]

            parsed = json.loads(raw_text)
            logger.info("LLM summary parsed successfully")
            return parsed

        except json.JSONDecodeError as e:
            logger.warning(f"LLM response JSON parse failed: {e}")
            return None
        except Exception as e:
            logger.warning(f"LLM invocation failed: {e}")
            return None

    def _summary_chain(self):
        class DummyChain:
            def invoke(self, vars):
                return json.dumps(
                    {
                        "summary": f"{vars.get('what_happened', '')[:80]} 요약",
                        "keyInsights": ["인사이트 예시"],
                        "suggestedPhrases": ["표현 예시"],
                    },
                    ensure_ascii=False,
                )

        return DummyChain()

    def summarize_reflection(self, payload: Mapping[str, object]) -> dict:
        emotions: List[str] = list(payload.get("emotions", []) or [])
        user_name: str = str(payload.get("user_name", "사용자"))
        base_text = " ".join(
            [
                str(payload.get("what_happened", "")),
                str(payload.get("what_you_did", "")),
                str(payload.get("desired_outcome", "")),
            ]
        )

        if not emotions:
            emotions = self.detect_emotions(base_text)

        # RAG 컨텍스트와 함께 LLM 호출 (사용자 이름 포함)
        parsed = self._invoke_llm_summary(base_text, emotions, user_name)

        if parsed:
            parsed = postprocess_emotions(parsed, base_text)
            parsed = clamp_mood_timeline(parsed)

            summary = str(parsed.get("summary", "")).strip()
            key_insights = self._normalize_array(parsed.get("keyInsights"))
            suggested_phrases = self._normalize_array(parsed.get("suggestedPhrases"))
            decision_points = self._normalize_array(parsed.get("decisionPoints"))
            emotions_from_llm = parsed.get("emotions", emotions)

            action_items_raw = parsed.get("actionItems", [])
            action_items = []
            if isinstance(action_items_raw, list):
                for ai in action_items_raw:
                    if isinstance(ai, dict) and "text" in ai:
                        action_items.append(
                            {
                                "text": str(ai.get("text"))[:150],
                                "owner": ai.get("owner"),
                                "due": ai.get("due"),
                            }
                        )
                    elif isinstance(ai, str):
                        action_items.append({"text": ai[:150], "owner": None, "due": None})

            confidence = parsed.get("confidence", 0.5)
            try:
                confidence = float(confidence)
            except Exception:
                confidence = 0.5

            result = {
                "summary": summary,
                "keyInsights": key_insights,
                "suggestedPhrases": suggested_phrases,
                "emotions": emotions_from_llm if emotions_from_llm else emotions,
                "decisionPoints": decision_points,
                "actionItems": action_items,
                "confidence": confidence,
            }

            # RAG 기반 심리상담사 조언 필드들 추가
            if "counselorAdvice" in parsed:
                result["counselorAdvice"] = str(parsed["counselorAdvice"]).strip()
            if "psychologicalNote" in parsed:
                result["psychologicalNote"] = str(parsed["psychologicalNote"]).strip()
            if "encouragement" in parsed:
                result["encouragement"] = str(parsed["encouragement"]).strip()

            if "emotionsDetailed" in parsed:
                result["emotionsDetailed"] = parsed["emotionsDetailed"]
            if "moodTimeline" in parsed:
                result["moodTimeline"] = parsed["moodTimeline"]

            logger.info("Using LLM summary path with RAG-enhanced fields")
            return result

        logger.info("Using rule-based fallback")
        chain = self._summary_chain()
        raw_response = chain.invoke(
            {
                "what_happened": payload.get("what_happened", ""),
                "emotions": ", ".join(emotions),
                "what_you_did": payload.get("what_you_did", ""),
                "desired_outcome": payload.get("desired_outcome", ""),
            }
        )

        parsed = self._safe_parse_json(str(raw_response))
        summary = str(parsed.get("summary", "")).strip()
        key_insights = self._normalize_array(parsed.get("keyInsights"))
        suggested_phrases = self._normalize_array(parsed.get("suggestedPhrases"))

        decision_points = self._normalize_array(parsed.get("decisionPoints"))
        if not decision_points:
            decision_points = self._extract_decisions(" ".join([summary] + key_insights))

        action_items_raw = parsed.get("actionItems", [])
        action_items = []
        if isinstance(action_items_raw, list):
            for ai in action_items_raw:
                if isinstance(ai, dict) and "text" in ai:
                    action_items.append(
                        {
                            "text": str(ai.get("text"))[:150],
                            "owner": ai.get("owner"),
                            "due": ai.get("due"),
                        }
                    )
                elif isinstance(ai, str):
                    action_items.append({"text": ai[:150], "owner": None, "due": None})

        if not action_items:
            action_items = self._extract_action_items(" ".join([summary] + key_insights))

        confidence = parsed.get("confidence", 0.5)
        try:
            confidence = float(confidence)
        except Exception:
            confidence = 0.5

        return {
            "summary": summary,
            "keyInsights": key_insights,
            "suggestedPhrases": suggested_phrases,
            "emotions": emotions,
            "decisionPoints": decision_points,
            "actionItems": action_items,
            "confidence": confidence,
        }

    # --------------------------
    # PERSONA CHAT REPLY
    # --------------------------

    def generate_chat_reply(self, payload: Mapping[str, object]) -> str:
        """
        persona 기반 대화 응답 생성.
        """
        logger.info(f"[CHAT_PAYLOAD] {payload}")

        user_msg = str(payload.get("message") or "").strip()

        if not self.llm:
            return f"반영해 볼게요: {user_msg}"

        try:
            persona_name = str(payload.get("persona_name") or payload.get("personaName") or "상대방").strip()
            persona_tone = str(payload.get("persona_tone") or payload.get("personaTone") or "평범한 말투").strip()
            persona_personality = str(
                payload.get("persona_personality") or payload.get("personaPersonality") or "평범한 성격"
            ).strip()
            relationship = str(payload.get("relationship") or "지인").strip()

            situation_parts = []
            what_happened = str(payload.get("what_happened") or payload.get("situation") or "").strip()
            if what_happened:
                situation_parts.append(f"사용자의 기록(사건): {what_happened}")
            what_you_did = str(payload.get("what_you_did") or "").strip()
            if what_you_did:
                situation_parts.append(f"사용자가 한 행동: {what_you_did}")
            emotions = payload.get("emotions") or []
            if emotions:
                situation_parts.append(f"당시 사용자의 감정: {', '.join(emotions)}")
            situation_text = "\n".join(situation_parts) or "상황 정보가 충분히 제공되지 않았습니다."

            desired_outcome = str(payload.get("desired_outcome") or payload.get("direction") or "").strip()
            if not desired_outcome:
                desired_outcome = "사용자가 원하는 방향에 대해 특별한 지시가 없습니다."

            history_list = payload.get("conversation", [])
            history_lines = []
            if isinstance(history_list, list):
                for message in history_list:
                    if not isinstance(message, dict):
                        continue
                    sender = message.get("sender")
                    text = str(message.get("text") or "").strip()
                    if not text:
                        continue
                    speaker = "나(User)" if sender == "user" else persona_name
                    history_lines.append(f"{speaker}: {text}")
            history = "\n".join(history_lines) or "대화 기록 없음"

            system_prompt = CHAT_PROMPT.format(
                persona_name=persona_name,
                persona_tone=persona_tone,
                persona_personality=persona_personality,
                relationship=relationship,
                situation=situation_text,
                direction=desired_outcome,
            )
            user_prompt = f"""
--- 이전 대화 기록 ---
{history}

--- 현재 메시지 ---
나(User): {user_msg}

(위 맥락을 고려하여 {persona_name}의 입장에서 답변하세요.)
"""

            response = self.llm.invoke(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            )

            if hasattr(response, "content"):
                return str(response.content).strip()

            return str(response).strip()

        except Exception as e:
            logger.warning(f"Chat reply LLM invocation failed: {e}")
            return "잠시 생각이 정리되지 않네요. 다시 말씀해 줄래요?"
