"""
벡터 DB 구축 스크립트
counsel_data.jsonl의 13,235개 상담 데이터를 ChromaDB에 임베딩하여 저장합니다.

사용법:
    cd backend
    python -m app.scripts.build_vector_db
"""

import json
import os
from pathlib import Path

# ChromaDB import
try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("ChromaDB가 설치되어 있지 않습니다. 다음 명령어로 설치하세요:")
    print("pip install chromadb sentence-transformers")
    exit(1)

# 프로젝트 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
COUNSEL_DATA_PATH = DATA_DIR / "counsel_data.jsonl"
CHROMA_DB_PATH = DATA_DIR / "chroma_db"


def load_counsel_data():
    """상담 데이터 로드"""
    data = []
    with open(COUNSEL_DATA_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line.strip())
                data.append(record)
            except json.JSONDecodeError:
                continue
    return data


def build_vector_db():
    """벡터 DB 구축"""
    print("=" * 60)
    print("🚀 벡터 DB 구축 시작")
    print("=" * 60)

    # 데이터 로드
    print(f"\n📂 데이터 로드 중: {COUNSEL_DATA_PATH}")
    data = load_counsel_data()
    print(f"✅ 로드 완료: {len(data)}개 레코드")

    # ChromaDB 클라이언트 생성
    print(f"\n📁 ChromaDB 초기화: {CHROMA_DB_PATH}")
    os.makedirs(CHROMA_DB_PATH, exist_ok=True)

    client = chromadb.PersistentClient(
        path=str(CHROMA_DB_PATH),
        settings=Settings(anonymized_telemetry=False),
    )

    # 기존 컬렉션 삭제 후 재생성
    try:
        client.delete_collection("counsel_cases")
        print("🗑️ 기존 컬렉션 삭제")
    except Exception:
        pass

    # 컬렉션 생성 (기본 임베딩 함수 사용)
    collection = client.create_collection(
        name="counsel_cases",
        metadata={"description": "전문 상담 사례 데이터베이스"},
    )
    print("✅ 컬렉션 생성 완료")

    # 데이터 준비
    print("\n📝 데이터 준비 중...")
    documents = []
    metadatas = []
    ids = []

    for i, record in enumerate(data):
        # 검색용 텍스트 (상황 + 감정 + 카테고리)
        search_text = f"""
카테고리: {record.get('category', '')}
감정: {record.get('emotion', '')}
상황: {record.get('user_context', '')}
""".strip()

        # 메타데이터 (검색 결과로 반환할 정보)
        metadata = {
            "category": record.get("category", ""),
            "emotion": record.get("emotion", ""),
            "user_context": record.get("user_context", "")[:500],  # 길이 제한
            "expert_solution": record.get("expert_solution", "")[:1000],
            "psychological_rationale": record.get("psychological_rationale", "")[:500],
        }

        documents.append(search_text)
        metadatas.append(metadata)
        ids.append(f"case_{i}")

        # 진행 상황 출력
        if (i + 1) % 1000 == 0:
            print(f"  준비 완료: {i + 1}/{len(data)}")

    # 배치로 추가 (ChromaDB는 한 번에 많은 양 추가 가능)
    print("\n⬆️ 벡터 DB에 데이터 추가 중...")
    batch_size = 1000
    for i in range(0, len(documents), batch_size):
        end_idx = min(i + batch_size, len(documents))
        collection.add(
            documents=documents[i:end_idx],
            metadatas=metadatas[i:end_idx],
            ids=ids[i:end_idx],
        )
        print(f"  추가 완료: {end_idx}/{len(documents)}")

    print("\n" + "=" * 60)
    print("✅ 벡터 DB 구축 완료!")
    print(f"📁 저장 위치: {CHROMA_DB_PATH}")
    print(f"📊 총 레코드: {collection.count()}개")
    print("=" * 60)

    # 테스트 검색
    print("\n🔍 테스트 검색...")
    results = collection.query(
        query_texts=["직장에서 상사와의 갈등으로 스트레스받아요"],
        n_results=2,
    )
    print("검색어: '직장에서 상사와의 갈등으로 스트레스받아요'")
    print(f"검색 결과: {len(results['documents'][0])}개")
    for i, (doc, meta) in enumerate(
        zip(results["documents"][0], results["metadatas"][0])
    ):
        print(f"\n  결과 {i + 1}:")
        print(f"    카테고리: {meta['category']}")
        print(f"    감정: {meta['emotion']}")
        print(f"    조언: {meta['expert_solution'][:100]}...")


if __name__ == "__main__":
    build_vector_db()

