"""
REFILL 챗봇 백엔드 API (FastAPI)

엔드포인트:
  GET  /health        — 헬스체크
  GET  /loadingpage   — 분석 완료 여부 확인 (Polling)
  GET  /history       — 과거 리포트 목록
  POST /analyze       — 처방전 분석 (n8n용, RAG 포함)
  POST /chatbot       — AI 챗봇 질의응답
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from airtable_client import (
    get_prescriptions,
    get_user_medications,
    save_chat_log,
)
from solar_client import chat, analyze_medications

app = FastAPI(
    title="REFILL API",
    description="처방약 기반 영양제 추천 서비스 백엔드 API",
    version="0.3.0",
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc
)

# CORS 설정 — Softr 프론트엔드에서 API 호출 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dawna91343.softr.app",   # Softr 프론트엔드
        "http://localhost:3000",          # 로컬 테스트용
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Request / Response 모델
# ============================================================

class ChatRequest(BaseModel):
    user_id: str
    message: str
    conversation_history: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    answer: str
    medications_used: list[str]


class LoadingResponse(BaseModel):
    status: str  # "completed" | "pending"
    record_id: Optional[str] = None


class HistoryItem(BaseModel):
    record_id: str
    scanned_at: Optional[str] = None
    medication_count: Optional[int] = None
    solar_summary: Optional[str] = None


class AnalyzeRequest(BaseModel):
    user_id: str
    medications: List[dict]  # [{"drug_name": "메트포르민", "dosage": "500mg", "frequency": "1일2회"}, ...]


class AnalyzeResponse(BaseModel):
    overall_nutrients_depleted: str
    overall_supplements_recommended: str
    dosage_guide: str
    warnings: str
    full_report: str


# ============================================================
# 엔드포인트
# ============================================================

@app.get("/health")
async def health():
    """헬스체크"""
    return {"status": "ok"}


# --- 1. 로딩 페이지 (Polling) ---

@app.get("/loadingpage", response_model=LoadingResponse)
async def loadingpage(user_id: str = Query(..., description="사용자 고유 ID")):
    """
    n8n 분석 완료 여부를 확인합니다.
    - solar_summary가 존재하면 completed + record_id 반환
    - 없으면 pending 반환
    프론트에서 2~3초 간격으로 폴링하세요.
    """
    prescriptions = await get_prescriptions(user_id)

    if not prescriptions:
        return LoadingResponse(status="pending")

    latest = prescriptions[0]

    # solar_summary가 채워져 있으면 분석 완료
    if latest.get("solar_summary"):
        return LoadingResponse(
            status="completed",
            record_id=latest.get("record_id"),
        )

    return LoadingResponse(status="pending")


# --- 2. 과거 기록 조회 ---

@app.get("/history", response_model=List[HistoryItem])
async def history(user_id: str = Query(..., description="사용자 고유 ID")):
    """
    해당 사용자의 모든 처방전 리포트 목록을 최신순으로 반환합니다.
    """
    prescriptions = await get_prescriptions(user_id)

    if not prescriptions:
        return []

    return [
        HistoryItem(
            record_id=p.get("record_id", ""),
            scanned_at=p.get("scanned_at"),
            medication_count=p.get("medication_count"),
            solar_summary=p.get("solar_summary"),
        )
        for p in prescriptions
    ]


# --- 3. 처방전 분석 (n8n용, RAG 포함) ---

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_endpoint(req: AnalyzeRequest):
    """
    n8n에서 호출하는 처방전 분석 엔드포인트.
    - 약물 목록을 받아서 RAG 검색 + Solar LLM으로 구조화된 분석 결과 반환
    - 논문 출처 포함된 근거 기반 분석
    
    n8n에서 이 응답을 받아 Analysis_Reports 테이블에 저장하면 됩니다.
    """
    if not req.medications:
        raise HTTPException(status_code=400, detail="약물 목록이 비어있습니다.")

    # 약물 정보를 텍스트로 포맷
    med_lines = []
    drug_names = []
    for med in req.medications:
        name = med.get("drug_name", "")
        dosage = med.get("dosage", "")
        frequency = med.get("frequency", "")
        drug_names.append(name)
        line = f"- {name}"
        if dosage:
            line += f" {dosage}"
        if frequency:
            line += f" ({frequency})"
        med_lines.append(line)

    medications_text = "\n".join(med_lines)

    # Solar + RAG 분석 호출
    try:
        result = await analyze_medications(medications_text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Solar API 호출 실패: {str(e)}")

    return AnalyzeResponse(**result)


# --- 4. AI 챗봇 (solar_summary 참조) ---

@app.post("/chatbot", response_model=ChatResponse)
async def chatbot_endpoint(req: ChatRequest):
    """
    사용자 질문을 Solar LLM에 전달하고 영양제 추천 응답을 반환합니다.
    - Airtable에서 user_id의 최근 약물 목록 자동 조회
    - Prescriptions의 solar_summary를 컨텍스트에 포함
    - RAG 검색 결과 포함
    - 대화 로그 자동 저장
    """
    # 1) 처방전 정보 조회 (solar_summary 포함)
    prescriptions = await get_prescriptions(req.user_id)
    solar_summary = ""
    if prescriptions:
        solar_summary = prescriptions[0].get("solar_summary", "") or ""

    # 2) 약물 정보 조회
    medications = await get_user_medications(req.user_id)

    if not medications:
        medications_context = "등록된 처방전이 없습니다."
        med_names = []
    else:
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

    # 3) solar_summary를 컨텍스트에 추가
    if solar_summary:
        medications_context += f"\n\n[이전 분석 요약]\n{solar_summary}"

    # 4) Solar Pro 3 호출
    try:
        answer = await chat(
            user_message=req.message,
            medications_context=medications_context,
            conversation_history=req.conversation_history,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Solar API 호출 실패: {str(e)}")

    # 5) 대화 로그 저장 (실패해도 응답은 반환)
    try:
        await save_chat_log(
            user_id=req.user_id,
            question=req.message,
            answer=answer,
        )
    except Exception:
        pass

    # 6) 응답
    return ChatResponse(
        answer=answer,
        medications_used=med_names,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
