"""
Airtable REST API 클라이언트
- 사용자의 처방전/약물 정보 조회
- 챗봇 대화 로그 저장
"""

import httpx
from config import (
    AIRTABLE_API_KEY,
    AIRTABLE_BASE_URL,
    AIRTABLE_PRESCRIPTIONS_TABLE,
    AIRTABLE_MEDICATIONS_TABLE,
    AIRTABLE_CHAT_TABLE,
)

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json",
}


async def get_prescriptions(user_id: str) -> list[dict]:
    """user_id로 해당 사용자의 처방전 목록 조회 (최신순)"""
    url = f"{AIRTABLE_BASE_URL}/{AIRTABLE_PRESCRIPTIONS_TABLE}"
    params = {
        "filterByFormula": f"{{user_id}}='{user_id}'",
        "sort[0][field]": "scanned_at",
        "sort[0][direction]": "desc",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        records = resp.json().get("records", [])
        return [r["fields"] for r in records]


async def get_medications(prescription_id: str) -> list[dict]:
    """특정 처방전에 연결된 약물 목록 조회"""
    url = f"{AIRTABLE_BASE_URL}/{AIRTABLE_MEDICATIONS_TABLE}"
    params = {
        "filterByFormula": f"{{prescription_id}}='{prescription_id}'",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        records = resp.json().get("records", [])
        return [r["fields"] for r in records]


async def get_user_medications(user_id: str) -> list[dict]:
    """user_id의 가장 최근 처방전에 포함된 약물 목록 조회"""
    prescriptions = await get_prescriptions(user_id)
    if not prescriptions:
        return []

    latest = prescriptions[0]
    # Airtable Link 필드는 record ID 배열로 저장됨
    prescription_record_ids = latest.get("id") or latest.get("Medications", [])

    # 직접 Medications 테이블에서 user의 최신 처방전 약물 조회
    url = f"{AIRTABLE_BASE_URL}/{AIRTABLE_MEDICATIONS_TABLE}"
    params = {
        "filterByFormula": f"{{prescription_id}}='{user_id}'",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        records = resp.json().get("records", [])
        return [r["fields"] for r in records]


async def save_chat_log(
    user_id: str,
    question: str,
    answer: str,
    prescription_id: str = None,
) -> None:
    """챗봇 대화 로그를 Airtable에 저장"""
    url = f"{AIRTABLE_BASE_URL}/{AIRTABLE_CHAT_TABLE}"
    fields = {
        "user_id": user_id,
        "question": question,
        "answer": answer,
        "asked_at": None,  # Airtable Created Time이 자동 처리
    }
    if prescription_id:
        fields["prescription_id"] = [prescription_id]

    payload = {"records": [{"fields": fields}]}
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=HEADERS, json=payload)
        resp.raise_for_status()
