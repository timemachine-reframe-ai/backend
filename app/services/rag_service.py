"""
RAG (Retrieval Augmented Generation) 서비스
ChromaDB에서 유사한 상담 사례를 검색하여 프롬프트에 컨텍스트로 제공합니다.
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# 프로젝트 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DB_PATH = DATA_DIR / "chroma_db"


class RAGService:
    """
    RAG 서비스 클래스
    유사한 상담 사례를 검색하여 LLM 프롬프트에 컨텍스트로 제공합니다.
    """

    def __init__(self):
        self._client = None
        self._collection = None
        self._initialized = False

    def _ensure_initialized(self) -> bool:
        """ChromaDB 초기화 확인 및 수행"""
        if self._initialized:
            return True

        try:
            import chromadb
            from chromadb.config import Settings

            if not CHROMA_DB_PATH.exists():
                logger.warning(
                    f"ChromaDB 경로가 존재하지 않습니다: {CHROMA_DB_PATH}. "
                    "python -m app.scripts.build_vector_db 를 실행하세요."
                )
                return False

            self._client = chromadb.PersistentClient(
                path=str(CHROMA_DB_PATH),
                settings=Settings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_collection("counsel_cases")
            self._initialized = True
            logger.info(
                f"RAG 서비스 초기화 완료. 총 {self._collection.count()}개 사례 로드됨."
            )
            return True

        except ImportError:
            logger.warning("ChromaDB가 설치되어 있지 않습니다. RAG 기능이 비활성화됩니다.")
            return False
        except Exception as e:
            logger.warning(f"RAG 서비스 초기화 실패: {e}")
            return False

    def search_similar_cases(
        self,
        query: str,
        n_results: int = 3,
        category_filter: Optional[str] = None,
        emotion_filter: Optional[str] = None,
    ) -> List[Dict]:
        """
        유사한 상담 사례 검색

        Args:
            query: 검색 쿼리 (사용자 상황 설명)
            n_results: 반환할 결과 수
            category_filter: 카테고리 필터 (직장, 대인관계, 가족 등)
            emotion_filter: 감정 필터 (두려움, 슬픔, 분노 등)

        Returns:
            유사 사례 리스트 [{
                'category': str,
                'emotion': str,
                'user_context': str,
                'expert_solution': str,
                'psychological_rationale': str,
                'distance': float
            }]
        """
        if not self._ensure_initialized():
            return []

        try:
            # 필터 조건 구성
            where_filter = None
            if category_filter or emotion_filter:
                conditions = []
                if category_filter:
                    conditions.append({"category": category_filter})
                if emotion_filter:
                    conditions.append({"emotion": emotion_filter})

                if len(conditions) == 1:
                    where_filter = conditions[0]
                else:
                    where_filter = {"$and": conditions}

            # 검색 수행
            results = self._collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter,
            )

            # 결과 포맷팅
            cases = []
            if results and results["metadatas"]:
                for i, metadata in enumerate(results["metadatas"][0]):
                    case = {
                        "category": metadata.get("category", ""),
                        "emotion": metadata.get("emotion", ""),
                        "user_context": metadata.get("user_context", ""),
                        "expert_solution": metadata.get("expert_solution", ""),
                        "psychological_rationale": metadata.get(
                            "psychological_rationale", ""
                        ),
                        "distance": (
                            results["distances"][0][i]
                            if results.get("distances")
                            else None
                        ),
                    }
                    cases.append(case)

            logger.debug(f"RAG 검색 완료: {len(cases)}개 사례 발견")
            return cases

        except Exception as e:
            logger.error(f"RAG 검색 실패: {e}")
            return []

    def format_context_for_prompt(
        self,
        cases: List[Dict],
        include_rationale: bool = True,
    ) -> str:
        """
        검색 결과를 프롬프트에 삽입할 형태로 포맷팅

        Args:
            cases: 검색된 사례 리스트
            include_rationale: 심리학적 근거 포함 여부

        Returns:
            프롬프트에 삽입할 문자열
        """
        if not cases:
            return ""

        formatted_parts = []
        for i, case in enumerate(cases, 1):
            part = f"""
**사례 {i}** [{case['category']} / {case['emotion']}]
- 상황: {case['user_context'][:200]}...
- 전문가 조언: {case['expert_solution'][:300]}...
"""
            if include_rationale and case.get("psychological_rationale"):
                part += f"- 심리학적 근거: {case['psychological_rationale'][:200]}...\n"

            formatted_parts.append(part.strip())

        return "\n\n".join(formatted_parts)

    def get_context_for_chat(
        self,
        situation: str,
        emotions: List[str] = None,
        n_results: int = 2,
    ) -> str:
        """
        채팅용 RAG 컨텍스트 생성

        Args:
            situation: 사용자 상황 설명
            emotions: 감정 리스트
            n_results: 검색할 사례 수

        Returns:
            채팅 프롬프트에 삽입할 컨텍스트
        """
        # 감정 필터 적용 (첫 번째 감정 사용)
        emotion_filter = emotions[0] if emotions else None

        cases = self.search_similar_cases(
            query=situation,
            n_results=n_results,
            emotion_filter=emotion_filter,
        )

        if not cases:
            return ""

        return self.format_context_for_prompt(cases, include_rationale=False)

    def get_context_for_report(
        self,
        conversation_text: str,
        emotions: List[str] = None,
        n_results: int = 3,
    ) -> str:
        """
        리포트용 RAG 컨텍스트 생성

        Args:
            conversation_text: 대화 전문
            emotions: 감정 리스트
            n_results: 검색할 사례 수

        Returns:
            리포트 프롬프트에 삽입할 컨텍스트
        """
        emotion_filter = emotions[0] if emotions else None

        cases = self.search_similar_cases(
            query=conversation_text[:500],  # 검색 쿼리 길이 제한
            n_results=n_results,
            emotion_filter=emotion_filter,
        )

        if not cases:
            return ""

        return self.format_context_for_prompt(cases, include_rationale=True)


# 싱글톤 인스턴스
_rag_service_instance: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """RAG 서비스 싱글톤 인스턴스 반환"""
    global _rag_service_instance
    if _rag_service_instance is None:
        _rag_service_instance = RAGService()
    return _rag_service_instance

