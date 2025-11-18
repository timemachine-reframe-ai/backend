import json
import logging
from typing import List, Mapping, Optional, Any

from .prompt_templates import SUMMARY_JSON_PROMPT
from .emotion_postprocess import postprocess_emotions, clamp_mood_timeline

logger = logging.getLogger(__name__)


class LangChainService:
    """
    LLM/체인 초기화는 실제 프로젝트 환경에 맞게 구성하세요.
    여기서는 동작 확인용 더미 체인(_summary_chain)과, 감정/결정/액션 추출 로직을 제공합니다.
    """

    def __init__(self, settings=None, llm: Optional[Any] = None):
        self.settings = settings
        self.llm = llm

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

    def detect_emotions(self, text: str, max_items: int = 3) -> List[str]:
        """
        1) (선택) LLM 시도: JSON 배열만 반환하도록 프롬프트 (프로젝트에 맞게 연결)
        2) 실패 시: 키워드 기반 fallback
        """

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

    def _invoke_llm_summary(self, text: str) -> Optional[dict]:
        """
        Invoke LLM with SUMMARY_JSON_PROMPT if LLM is configured.
        Returns parsed dict or None if LLM not available or parsing fails.
        """
        if not self.llm:
            return None

        try:
            prompt = SUMMARY_JSON_PROMPT.format(input_text=text)
            response = self.llm.invoke(prompt)

            # Extract text from response
            if hasattr(response, "content"):
                raw_text = response.content
            else:
                raw_text = str(response)

            # Simple repair: trim leading/trailing non-JSON content
            raw_text = raw_text.strip()

            # Find JSON boundaries
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
        """
        실제 LangChain 체인을 구성해 반환하세요.
        여기서는 동작 확인용 더미 체인을 반환합니다.
        """

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
        base_text = " ".join(
            [
                str(payload.get("what_happened", "")),
                str(payload.get("what_you_did", "")),
                str(payload.get("desired_outcome", "")),
            ]
        )

        if not emotions:
            emotions = self.detect_emotions(base_text)

        # Try LLM path first
        parsed = self._invoke_llm_summary(base_text)

        if parsed:
            # Apply post-processing for emotion normalization
            parsed = postprocess_emotions(parsed, base_text)
            parsed = clamp_mood_timeline(parsed)

            # Extract public fields from LLM response
            summary = str(parsed.get("summary", "")).strip()
            key_insights = self._normalize_array(parsed.get("keyInsights"))
            suggested_phrases = self._normalize_array(parsed.get("suggestedPhrases"))
            emotions_from_llm = parsed.get("emotions", emotions)
            decision_points = self._normalize_array(parsed.get("decisionPoints"))

            action_items_raw = parsed.get("actionItems", [])
            action_items: List[dict] = []
            if isinstance(action_items_raw, list) and action_items_raw:
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
                        action_items.append(
                            {"text": ai[:150], "owner": None, "due": None}
                        )

            confidence = parsed.get("confidence", 0.5)
            try:
                confidence = float(confidence)
            except Exception:
                confidence = 0.5

            # Return public fields + optional internal fields
            result = {
                "summary": summary,
                "keyInsights": key_insights,
                "suggestedPhrases": suggested_phrases,
                "emotions": emotions_from_llm if emotions_from_llm else emotions,
                "decisionPoints": decision_points,
                "actionItems": action_items,
                "confidence": confidence,
            }

            # Include extended fields if available
            if "emotionsDetailed" in parsed:
                result["emotionsDetailed"] = parsed["emotionsDetailed"]
            if "moodTimeline" in parsed:
                result["moodTimeline"] = parsed["moodTimeline"]

            logger.info("Using LLM summary path")
            return result

        # Fallback to rule-based approach
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
        text = str(raw_response)
        parsed = self._safe_parse_json(text)

        summary = str(parsed.get("summary", "")).strip()
        key_insights = self._normalize_array(parsed.get("keyInsights"))
        suggested_phrases = self._normalize_array(parsed.get("suggestedPhrases"))

        decision_points = self._normalize_array(parsed.get("decisionPoints"))
        if not decision_points:
            decision_points = self._extract_decisions(
                " ".join([summary] + key_insights)
            )

        action_items_raw = parsed.get("actionItems", [])
        action_items: List[dict] = []
        if isinstance(action_items_raw, list) and action_items_raw:
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
            action_items = self._extract_action_items(
                " ".join([summary] + key_insights)
            )

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

    def generate_chat_reply(self, payload: Mapping[str, object]) -> str:
        last_user = payload.get("message") or ""
        return f"반영해 볼게요: {last_user}"
