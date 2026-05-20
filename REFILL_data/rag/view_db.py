"""
ChromaDB에 저장된 전체 데이터를 조회하는 스크립트.

사용법:
  python rag/view_db.py
"""

import os
import chromadb

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")


def main():
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        collection = client.get_collection("drug_nutrients")
    except Exception:
        print("벡터 DB가 없습니다. 먼저 build_vectordb.py를 실행하세요.")
        return

    print(f"=== ChromaDB: drug_nutrients ===")
    print(f"총 저장 건수: {collection.count()}건\n")

    # 전체 데이터 가져오기
    results = collection.get(include=["documents", "metadatas"])

    for i, (doc_id, metadata, document) in enumerate(
        zip(results["ids"], results["metadatas"], results["documents"]), 1
    ):
        print(f"--- [{i}] {doc_id} ---")
        print(f"  약물 계열: {metadata.get('drug_class', '')}")
        print(f"  약물명: {metadata.get('drug_names', '')}")
        print(f"  고갈 영양소: {metadata.get('depleted_nutrients', '')}")
        print(f"  근거 수준: {metadata.get('evidence_level', '')}")
        print(f"  출처: {metadata.get('source', '')[:60]}...")
        print()


if __name__ == "__main__":
    main()
