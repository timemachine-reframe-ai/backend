from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_langchain_service
from app.schemas.reflection import (
    ReflectionChatRequest,
    ReflectionChatResponse,
    ReflectionSummaryRequest,
    ReflectionSummaryResponse,
)
from app.services.langchain import LangChainService

router = APIRouter()


@router.post(
    "/summary",
    response_model=ReflectionSummaryResponse,
    summary="요약 인사이트 생성",
)
def summarize_reflection(
    payload: ReflectionSummaryRequest,
    service: LangChainService = Depends(get_langchain_service),
):
    try:
        summary = service.summarize_reflection(payload.to_chain_payload())
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - unexpected Gemini failure
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate reflection summary.",
        ) from exc

    return ReflectionSummaryResponse(**summary)


@router.post(
    "/chat",
    response_model=ReflectionChatResponse,
    summary="시뮬레이션 대화 응답 생성",
)
def chat_reflection(
    payload: ReflectionChatRequest,
    service: LangChainService = Depends(get_langchain_service),
):
    try:
        reply = service.generate_chat_reply(payload.to_chat_payload())
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - unexpected Gemini failure
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate chat response.",
        ) from exc

    return ReflectionChatResponse(reply=reply)
