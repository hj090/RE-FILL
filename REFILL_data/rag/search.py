"""
ChromaDB에서 약물 관련 지식을 검색하는 모듈.
챗봇 백엔드에서 import하여 사용합니다.
"""

import os
import httpx
import chromadb
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "chatbot", ".env"))

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
EMBEDDING_URL = "https://api.upstage.ai/v1/embeddings"
EMBEDDING_MODEL = "embedding-query"
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")


def get_embedding(text):
    """텍스트를 벡터로 변환"""
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


def search_knowledge(query, n_results=3):
    """
    질문과 관련된 약물-영양소 지식을 검색합니다.

    Args:
        query: 검색 쿼리 (약물명 또는 질문)
        n_results: 반환할 결과 수

    Returns:
        list of dict: 관련 지식 목록
        [
            {
                "document": "전체 텍스트",
                "metadata": {"drug_class": ..., "source": ..., ...},
                "distance": 유사도 거리
            }
        ]
    """
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        collection = client.get_collection("drug_nutrients")
    except Exception:
        return []

    query_embedding = get_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )

    output = []
    for i in range(len(results["ids"][0])):
        output.append({
            "document": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i] if results.get("distances") else None,
        })

    return output


def format_knowledge_for_prompt(results):
    """
    검색 결과를 LLM 프롬프트에 넣을 텍스트로 포맷합니다.

    Args:
        results: search_knowledge()의 반환값

    Returns:
        str: 프롬프트에 삽입할 텍스트
    """
    if not results:
        return ""

    lines = ["[참고 지식 (벡터 검색 결과)]"]
    for i, r in enumerate(results, 1):
        lines.append(f"\n--- 참고자료 {i} ---")
        lines.append(r["document"])

    return "\n".join(lines)


if __name__ == "__main__":
    # 테스트
    query = "메트포르민 복용 시 부족한 영양소"
    print(f"검색어: {query}\n")

    results = search_knowledge(query)
    for r in results:
        print(f"[{r['metadata']['drug_class']}] {r['metadata']['drug_names']}")
        print(f"  출처: {r['metadata']['source'][:50]}...")
        print(f"  거리: {r['distance']}")
        print()
