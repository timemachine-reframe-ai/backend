from __future__ import annotations

from functools import cache
from typing import Any, Dict

from app.core.config import Settings


class LangChainService:
    """Thin wrapper around LangChain components to keep FastAPI endpoints clean."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def _import_langchain(self):  # pragma: no cover - optional dependency
        try:
            from langchain_core.output_parsers import StrOutputParser
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_openai import ChatOpenAI
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "LangChain dependencies are not installed. Install 'langchain' and 'langchain-openai'."
            ) from exc

        return ChatPromptTemplate, ChatOpenAI, StrOutputParser

    @cache
    def _chat_chain(self):  # pragma: no cover - lazily constructed
        ChatPromptTemplate, ChatOpenAI, StrOutputParser = self._import_langchain()
        if not self.settings.LANGCHAIN_API_KEY:
            raise RuntimeError("LANGCHAIN_API_KEY is not configured")

        prompt = ChatPromptTemplate.from_template(
            """
            당신은 감정 회고 코치입니다. 아래 입력을 토대로 짧은 회고 인사이트를 작성하세요.
            상황: {what_happened}
            감정: {emotions}
            행동: {what_you_did}
            바랐던 결과: {desired_outcome}
            """
        )

        llm = ChatOpenAI(
            model=self.settings.LANGCHAIN_MODEL,
            api_key=self.settings.LANGCHAIN_API_KEY,
            temperature=0.2,
        )

        return prompt | llm | StrOutputParser()

    def summarize_reflection(self, payload: Dict[str, Any]) -> str:
        """Generate a short insight summary. Raises when LangChain is not configured."""
        chain = self._chat_chain()
        return chain.invoke(
            {
                "what_happened": payload.get("what_happened", ""),
                "emotions": ", ".join(payload.get("emotions", [])),
                "what_you_did": payload.get("what_you_did", ""),
                "desired_outcome": payload.get("desired_outcome", ""),
            }
        )
