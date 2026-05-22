"""
Upstage Solar Pro 3 LLM 클라이언트
- 약물 정보 기반 영양소 분석 대화
- RAG 검색 결과를 컨텍스트로 활용
"""

import sys
import os
import httpx
from config import UPSTAGE_API_KEY, UPSTAGE_CHAT_URL, UPSTAGE_MODEL

# RAG 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rag"))
try:
    from search import search_knowledge, format_knowledge_for_prompt
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

SYSTEM_PROMPT = """당신은 처방약 기반 영양제 상담 약사입니다. 사용자와 1:1 상담하듯 자연스럽게 대화하세요.

역할:
- 사용자의 처방약 목록을 바탕으로 부족해질 수 있는 영양소를 분석합니다.
- 적절한 영양제 보충을 추천합니다.
- 약물 간 상호작용, 영양소 고갈 메커니즘을 쉽게 설명합니다.

규칙:
1. 의학적 진단이나 처방 변경은 절대 하지 마세요. 필요 시 "담당 의사와 상담해보세요"를 안내하세요.
2. 근거 기반으로 답변하되, 확실하지 않은 정보는 "확인이 필요합니다"라고 말하세요.
3. 답변은 한국어로, 친절하고 이해하기 쉽게 작성하세요.
4. 영양제 추천 시 일반적인 용량 범위를 함께 안내하세요.
5. 개인정보는 절대 언급하지 마세요.
6. 참고 지식이 제공된 경우, 자연스럽게 근거를 언급하세요 (예: "연구에 따르면~").

대화 스타일:
- 약국에서 약사가 환자에게 설명하듯 따뜻하고 전문적으로 대화하세요.
- 딱딱한 보고서 형식이 아니라, 자연스러운 문장으로 설명하세요.
- 핵심 정보는 빠짐없이 전달하되, 대화 흐름에 맞게 구성하세요.
- 사용자가 추가 질문하면 이전 맥락을 이어서 답변하세요.
- 필요할 때만 간단한 목록이나 표를 사용하세요.

예시 답변 톤:
"메트포르민을 드시고 계시군요. 이 약을 오래 복용하시면 비타민B12 흡수가 줄어들 수 있어요. 
연구에 따르면 장기 복용자의 약 30%에서 B12 수치가 낮아진다고 해요. 
비타민B12 1000mcg 정도를 매일 보충해주시면 좋고, 공복에 드시는 게 흡수가 잘 됩니다.
혹시 손발 저림이나 피로감이 있으시면 한번 검사받아보시는 것도 좋아요."

---
⚠️ 본 정보는 참고용이며, 구체적인 복용은 반드시 의사 또는 약사와 상담하세요.
"""


ANALYSIS_PROMPT = """당신은 처방약 기반 영양소 분석 전문가입니다.

주어진 약물 목록과 참고 지식을 바탕으로, 아래 5개 항목을 정확하게 분석하세요.

규칙:
1. 반드시 참고 지식에 포함된 논문 출처를 인용하세요.
2. 확실하지 않은 정보는 포함하지 마세요.
3. 한국어로 작성하세요.
4. 각 항목은 간결하되 핵심 정보를 빠짐없이 포함하세요.

출력 형식 (반드시 이 JSON 형식으로만 답변):
{
  "overall_nutrients_depleted": "고갈 가능 영양소 목록 (쉼표 구분, 예: 비타민B12, CoQ10, 마그네슘)",
  "overall_supplements_recommended": "추천 영양제 + 용량 (예: 비타민B12 1000mcg/일, CoQ10 100-200mg/일)",
  "dosage_guide": "복용 가이드 (복용 시간, 간격, 식전/식후 등)",
  "warnings": "주의사항 (약물 간 상호작용, 복용 금기 등)",
  "full_report": "종합 분석 보고서 (약물별 영양소 고갈 메커니즘, 근거 논문 포함, 마크다운 형식)"
}

JSON만 출력하세요. 다른 텍스트는 포함하지 마세요.
"""


async def analyze_medications(medications_text: str) -> dict:
    """
    약물 목록을 받아 RAG + Solar로 구조화된 분석 결과를 반환

    Args:
        medications_text: 약물 목록 텍스트 (줄바꿈 구분)

    Returns:
        dict with keys: overall_nutrients_depleted, overall_supplements_recommended,
                       dosage_guide, warnings, full_report
    """
    import json

    messages = [
        {"role": "system", "content": ANALYSIS_PROMPT},
    ]

    # 약물 정보 추가
    messages.append({
        "role": "system",
        "content": f"[분석 대상 약물]\n{medications_text}",
    })

    # RAG: 약물 정보로 관련 지식 검색
    if RAG_AVAILABLE:
        try:
            results = search_knowledge(medications_text, n_results=5)
            knowledge_text = format_knowledge_for_prompt(results)
            if knowledge_text:
                messages.append({
                    "role": "system",
                    "content": knowledge_text,
                })
        except Exception:
            pass

    messages.append({
        "role": "user",
        "content": f"위 약물들에 대해 영양소 고갈 분석을 수행하고, 지정된 JSON 형식으로 결과를 반환해주세요.",
    })

    headers = {
        "Authorization": f"Bearer {UPSTAGE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": UPSTAGE_MODEL,
        "messages": messages,
        "temperature": 0.3,  # 분석은 낮은 temperature로 정확도 우선
        "max_tokens": 2048,
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(UPSTAGE_CHAT_URL, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]

    # JSON 파싱 (LLM 응답에서 JSON 추출)
    try:
        # ```json ... ``` 블록이 있을 수 있으므로 제거
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]  # 첫 줄 제거
            cleaned = cleaned.rsplit("```", 1)[0]  # 마지막 ``` 제거
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        # JSON 파싱 실패 시 전체 응답을 full_report에 넣기
        result = {
            "overall_nutrients_depleted": "",
            "overall_supplements_recommended": "",
            "dosage_guide": "",
            "warnings": "",
            "full_report": content,
        }

    # 필수 키 보장
    for key in ["overall_nutrients_depleted", "overall_supplements_recommended",
                "dosage_guide", "warnings", "full_report"]:
        if key not in result:
            result[key] = ""

    return result


async def chat(
    user_message: str,
    medications_context: str,
    conversation_history: list = None,
) -> str:
    """
    Solar Pro 3에 대화 요청 (RAG 검색 포함)

    Args:
        user_message: 사용자 질문
        medications_context: 현재 사용자의 약물 정보 요약 텍스트
        conversation_history: 이전 대화 이력 [{"role": "user"|"assistant", "content": "..."}]

    Returns:
        Solar LLM 응답 텍스트
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    # 약물 컨텍스트를 system 메시지 뒤에 추가
    if medications_context:
        messages.append({
            "role": "system",
            "content": f"[현재 사용자의 처방약 정보]\n{medications_context}",
        })

    # RAG: 질문 + 약물 정보로 관련 지식 검색
    if RAG_AVAILABLE:
        search_query = f"{user_message} {medications_context}"
        try:
            results = search_knowledge(search_query, n_results=3)
            knowledge_text = format_knowledge_for_prompt(results)
            if knowledge_text:
                messages.append({
                    "role": "system",
                    "content": knowledge_text,
                })
        except Exception:
            pass  # RAG 실패해도 기본 응답은 가능

    # 이전 대화 이력 추가
    if conversation_history:
        messages.extend(conversation_history)

    # 현재 질문
    messages.append({"role": "user", "content": user_message})

    headers = {
        "Authorization": f"Bearer {UPSTAGE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": UPSTAGE_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(UPSTAGE_CHAT_URL, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
