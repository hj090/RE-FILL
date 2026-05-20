"""
챗봇 백엔드 API (FastAPI)

엔드포인트:
  POST /chat  — 사용자 질문 → Solar Pro 3 응답
  GET  /health — 헬스체크
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from airtable_client import get_user_medications, save_chat_log
from solar_client import chat

app = FastAPI(
    title="REFILL 챗봇 API",
    description="처방약 기반 영양제 추천 챗봇",
    version="0.1.0",
)


# === Request / Response 모델 ===

from typing import Optional, List

class ChatRequest(BaseModel):
    user_id: str
    message: str
    conversation_history: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    answer: str
    medications_used: list[str]


# === 엔드포인트 ===

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    1. Airtable에서 user_id의 최근 약물 목록 조회
    2. 약물 정보를 컨텍스트로 Solar Pro 3에 전달
    3. 응답을 Chat_Sessions에 저장
    4. 응답 반환
    """
    # 1) 약물 정보 조회
    medications = await get_user_medications(req.user_id)

    if not medications:
        medications_context = "등록된 처방전이 없습니다."
        med_names = []
    else:
        # 약물 정보를 텍스트로 포맷
        med_lines = []
        med_names = []
        for med in medications:
            name = med.get("drug_name", "알 수 없음")
            dosage = med.get("dosage", "")
            freq = med.get("frequency", "")
            depleted = med.get("depleted_nutrients", "")
            supplements = med.get("recommended_supplements", "")

            med_names.append(name)
            line = f"- {name} {dosage} ({freq})"
            if depleted:
                line += f" → 고갈 영양소: {depleted}"
            if supplements:
                line += f" → 추천 보충: {supplements}"
            med_lines.append(line)

        medications_context = "\n".join(med_lines)

    # 2) Solar Pro 3 호출
    try:
        answer = await chat(
            user_message=req.message,
            medications_context=medications_context,
            conversation_history=req.conversation_history,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Solar API 호출 실패: {str(e)}")

    # 3) 대화 로그 저장 (비동기, 실패해도 응답은 반환)
    try:
        await save_chat_log(
            user_id=req.user_id,
            question=req.message,
            answer=answer,
        )
    except Exception:
        pass  # 로그 저장 실패는 무시

    # 4) 응답
    return ChatResponse(
        answer=answer,
        medications_used=med_names,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
