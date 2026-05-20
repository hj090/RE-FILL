"""
약물-영양소 매핑 데이터를 ChromaDB에 임베딩하여 저장하는 스크립트.
1회 실행하면 rag/chroma_db/ 폴더에 벡터 DB가 생성됩니다.

사용법:
  cd rag
  pip install -r requirements.txt
  python build_vectordb.py
"""

import json
import os
import httpx
import chromadb
from dotenv import load_dotenv

# .env는 chatbot 폴더에 있으므로 상위에서 로드
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "chatbot", ".env"))

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
EMBEDDING_URL = "https://api.upstage.ai/v1/embeddings"
EMBEDDING_MODEL = "embedding-query"

KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), "knowledge", "drug_nutrient_mapping.json")
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")


def get_embedding(text):
    """Upstage Solar Embedding API로 텍스트 벡터화"""
    headers = {
        "Authorization": f"Bearer {UPSTAGE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": EMBEDDING_MODEL,
        "input": text,
    }
    resp = httpx.post(EMBEDDING_URL, headers=headers, json=payload, timeout=30.0)
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]


def build_document_text(item):
    """JSON 항목을 검색용 텍스트로 변환"""
    drug_names = ", ".join(item["drug_names"])
    nutrients = ", ".join(item["depleted_nutrients"])
    supplements = ", ".join(item["recommended_supplements"])

    text = (
        f"약물 계열: {item['drug_class']}\n"
        f"약물명: {drug_names}\n"
        f"고갈 영양소: {nutrients}\n"
        f"메커니즘: {item['mechanism']}\n"
        f"추천 보충제: {supplements}\n"
        f"위험도: {item['risk_level']}\n"
        f"주의사항: {item['caution']}\n"
        f"출처: {item['source']}\n"
        f"근거 수준: {item['evidence_level']}"
    )
    return text


def main():
    # 1) 지식 데이터 로드
    with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
        knowledge = json.load(f)

    print(f"[1/3] 지식 데이터 로드 완료: {len(knowledge)}건")

    # 2) ChromaDB 초기화
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # 기존 컬렉션 있으면 삭제 후 재생성
    try:
        client.delete_collection("drug_nutrients")
    except Exception:
        pass

    collection = client.create_collection(
        name="drug_nutrients",
        metadata={"description": "약물-영양소 고갈 매핑 지식베이스"},
    )

    print("[2/3] 임베딩 생성 중...")

    # 3) 각 항목을 임베딩하여 저장
    for i, item in enumerate(knowledge):
        doc_text = build_document_text(item)
        embedding = get_embedding(doc_text)

        # 메타데이터에 주요 정보 저장 (검색 후 바로 활용)
        metadata = {
            "id": item["id"],
            "drug_class": item["drug_class"],
            "drug_names": ", ".join(item["drug_names"]),
            "depleted_nutrients": ", ".join(item["depleted_nutrients"]),
            "source": item["source"],
            "evidence_level": item["evidence_level"],
        }

        collection.add(
            ids=[item["id"]],
            embeddings=[embedding],
            documents=[doc_text],
            metadatas=[metadata],
        )

        print(f"  [{i+1}/{len(knowledge)}] {item['drug_class']} - {', '.join(item['drug_names'])}")

    print(f"\n[3/3] 완료! ChromaDB 저장 위치: {CHROMA_PATH}")
    print(f"  총 {collection.count()}건 저장됨")


if __name__ == "__main__":
    main()
