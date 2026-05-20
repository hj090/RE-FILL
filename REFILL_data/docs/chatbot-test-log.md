# 챗봇 백엔드 테스트 로그

> **일시**: 2025-05-20  
> **상태**: ✅ 로컬 테스트 성공

---

## 실행 환경

| 항목 | 값 |
|------|-----|
| OS | Windows |
| Python | 3.9.13 |
| 서버 | FastAPI + Uvicorn |
| LLM | Upstage Solar Pro 3 (`solar-pro3`) |
| DB | Airtable REST API |

---

## 실행 방법

```bash
cd C:\Users\ASUS\REFILL_data\chatbot
pip install -r requirements.txt
python main.py
```

서버 주소: `http://localhost:8000`  
Swagger UI: `http://localhost:8000/docs`

---

## 테스트 결과

### GET /health ✅
```json
{"status": "ok"}
```

### POST /chat ✅
**요청:**
```json
{
  "user_id": "test-user-1",
  "message": "메트포르민 먹고 있는데 어떤 영양제 먹어야 해?",
  "conversation_history": []
}
```
**결과:** Solar Pro 3가 정상 응답 반환

---

## 해결한 이슈들

### 이슈 1: Python 3.9 타입 힌트 호환
- **증상**: `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'`
- **원인**: `str | None` 문법은 Python 3.10+ 전용
- **해결**: `Optional[str]` 또는 `= None` 방식으로 변경
- **수정 파일**: `main.py`, `solar_client.py`, `airtable_client.py`

### 이슈 2: Airtable 404 Not Found
- **증상**: `Client error '404 Not Found'`
- **원인**: `.env`에서 `AIRTABLE_BASE_ID`에 API Key(`pat...`)를 넣음
- **해결**: Base ID는 `app...`으로 시작하는 값 (Airtable URL에서 확인)

### 이슈 3: Solar API 502 Bad Gateway
- **증상**: `502 Bad Gateway`
- **원인**: 모델명이 `solar-pro3-preview`로 잘못 설정됨
- **해결**: `config.py`에서 `solar-pro3`으로 수정

---

## 현재 제약사항

- Airtable에 테스트 데이터가 없어서, 챗봇이 "등록된 처방전이 없습니다"로 컨텍스트 없이 응답함
- B가 n8n으로 처방전 데이터 1건 넣으면 실제 약물 기반 응답 테스트 가능

---

## 다음 할 일

1. B에게 스키마 명세서 + PII 필터 코드 전달
2. B가 n8n으로 테스트 데이터 1건 Airtable에 저장
3. 실제 약물 데이터 기반 챗봇 응답 확인
4. 프론트(A)와 API 연동
