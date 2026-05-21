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


# === 처방전 관련 ===

async def get_prescriptions(user_id: str) -> list[dict]:
    """user_id로 해당 사용자의 처방전 목록 조회 (최신순), record id 포함"""
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
        # record id를 fields에 포함시켜 반환
        results = []
        for r in records:
            fields = r["fields"]
            fields["record_id"] = r["id"]
            results.append(fields)
        return results


async def get_prescription_by_record_id(record_id: str) -> dict | None:
    """Airtable record ID로 처방전 1건 조회"""
    url = f"{AIRTABLE_BASE_URL}/{AIRTABLE_PRESCRIPTIONS_TABLE}/{record_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=HEADERS)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        fields = data.get("fields", {})
        fields["record_id"] = data["id"]
        return fields


# === 약물 관련 ===

async def get_medications_by_prescription(record_id: str) -> list[dict]:
    """특정 처방전 record_id에 연결된 약물 목록 조회"""
    url = f"{AIRTABLE_BASE_URL}/{AIRTABLE_MEDICATIONS_TABLE}"
    params = {
        "filterByFormula": f"FIND('{record_id}', ARRAYJOIN({{prescription_id}}))",
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
    record_id = latest.get("record_id")

    if record_id:
        return await get_medications_by_prescription(record_id)

    # fallback: user_id로 직접 조회
    url = f"{AIRTABLE_BASE_URL}/{AIRTABLE_MEDICATIONS_TABLE}"
    params = {
        "filterByFormula": f"{{prescription_id}}='{user_id}'",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        records = resp.json().get("records", [])
        return [r["fields"] for r in records]


# === 대화 로그 ===

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
    }
    if prescription_id:
        fields["prescription_id"] = [prescription_id]

    payload = {"records": [{"fields": fields}]}
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=HEADERS, json=payload)
        resp.raise_for_status()
