from __future__ import annotations

import json
import re
from functools import cache
from typing import Mapping, Sequence

from app.core.config import Settings


def _clean_json_text(raw: str) -> str:
    """Strip markdown fences/backticks so json.loads can parse."""
    if not raw:
        return raw
    raw = raw.strip()
    code_block = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)
    match = code_block.match(raw)
    if match:
        return match.group(1).strip()
    return raw


class LangChainService:
    """Gemini-powered reflection helper built with LangChain 1.x runnables."""

    def __init__(self, settings: Settings):
        self.settings = settings

    @cache
    def _components(self):  # pragma: no cover - optional dependency
        try:
            from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
            from langchain_core.output_parsers import StrOutputParser
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "LangChain Gemini dependencies are not installed. Install 'langchain-google-genai'."
            ) from exc

        return ChatPromptTemplate, ChatGoogleGenerativeAI, StrOutputParser, SystemMessage, HumanMessage, AIMessage

    @cache
    def _llm(self):
        _, ChatGoogleGenerativeAI, _, _, _, _ = self._components()
        if not self.settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not configured")

        return ChatGoogleGenerativeAI(
            model=self.settings.GEMINI_MODEL,
            google_api_key=self.settings.GEMINI_API_KEY,
            temperature=0.2,
        )

    @cache
    def _summary_chain(self):
        ChatPromptTemplate, _, StrOutputParser, *_ = self._components()
        llm = self._llm()

        prompt = ChatPromptTemplate.from_template(
            """
            다음은 사용자가 경험한 상황입니다.
            - 발생한 일: {what_happened}
            - 감정: {emotions}
            - 실제 반응: {what_you_did}
            - 바랐던 결과: {desired_outcome}

            위 정보를 바탕으로 JSON을 생성하세요.
            형식:
            {{
              "summary": "<2-3문장 요약>",
              "keyInsights": ["통찰1", "통찰2", "통찰3"],
              "suggestedPhrases": ["추천 표현1", "추천 표현2"]
            }}
            모든 텍스트는 한국어로 작성하세요.
            """
        )

        return prompt | llm | StrOutputParser()

    def summarize_reflection(self, payload: Mapping[str, object]) -> dict:
        """Generate a structured summary with key insights and suggested phrases."""
        chain = self._summary_chain()
        raw_response = chain.invoke(
            {
                "what_happened": payload.get("what_happened", ""),
                "emotions": ", ".join(payload.get("emotions", [])),
                "what_you_did": payload.get("what_you_did", ""),
                "desired_outcome": payload.get("desired_outcome", ""),
            }
        )

        cleaned = _clean_json_text(raw_response)
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            parsed = {"summary": cleaned or raw_response}

        def _normalize_array(value: object) -> list[str]:
            if value is None:
                return []
            if isinstance(value, str):
                return [value.strip()] if value.strip() else []
            if isinstance(value, Sequence):
                return [str(item).strip() for item in value if str(item).strip()]
            return []

        return {
            "summary": str(parsed.get("summary", "")).strip(),
            "keyInsights": _normalize_array(parsed.get("keyInsights")),
            "suggestedPhrases": _normalize_array(parsed.get("suggestedPhrases")),
        }

    def generate_chat_reply(self, payload: Mapping[str, object]) -> str:
        """Produce a persona-aware chat reply for the simulation."""
        (
            _,
            _,
            _,
            SystemMessage,
            HumanMessage,
            AIMessage,
        ) = self._components()
        llm = self._llm()

        system_prompt = (
            "당신은 감정 회고 시뮬레이션을 돕는 AI로서 '{persona_name}' 역할을 완벽히 수행합니다. "
            "실제 그 사람이 말하듯 '{persona_tone}' 말투와 '{persona_personality}' 성격을 유지하세요. "
            "다음 상황 정보를 참고하여 공감적이고 실용적인 답변을 제공하되, 지나치게 장황하지 않게 3~4문장 이내로 답변하세요.\n"
            "- 발생한 일: {what_happened}\n"
            "- 감정: {emotions}\n"
            "- 실제 반응: {what_you_did}\n"
            "- 바랐던 결과: {desired_outcome}\n"
            "대화는 반드시 한국어로 진행하며, 사용자의 감정을 검증하고 상대방(즉, 당신)의 관점에서 진솔하게 반응하세요."
        ).format(
            persona_name=payload.get("persona_name", "상대방"),
            persona_tone=payload.get("persona_tone", "차분한"),
            persona_personality=payload.get("persona_personality", "공감적인"),
            what_happened=payload.get("what_happened", ""),
            emotions=", ".join(payload.get("emotions", [])),
            what_you_did=payload.get("what_you_did", ""),
            desired_outcome=payload.get("desired_outcome", ""),
        )

        messages = [SystemMessage(content=system_prompt)]
        for msg in payload.get("conversation", []):
            text = msg.get("text", "")
            if msg.get("sender") == "ai":
                messages.append(AIMessage(content=text))
            else:
                messages.append(HumanMessage(content=text))

        messages.append(HumanMessage(content=payload.get("message", "")))
        response = llm.invoke(messages)

        if isinstance(response, str):
            return response
        return getattr(response, "content", str(response))
