# REFILL API 명세서 (프론트엔드 연동용)

> **Base URL**: `https://배포URL.up.railway.app`  
> **Swagger UI**: `{Base URL}/docs` ← 브라우저에서 직접 테스트 가능  
> **ReDoc**: `{Base URL}/redoc` ← 깔끔한 문서 형태로 보기  
> **최종 업데이트**: 2025-05-21

---

## 공통 사항

- 모든 응답은 JSON 형식
- 에러 시 `{"detail": "에러 메시지"}` 반환
- `user_id`는 프론트에서 생성한 UUID v4 문자열

### HTTP 상태 코드

| 코드 | 의미 |
|------|------|
| 200 | 성공 |
| 404 | 데이터 없음 |
| 422 | 요청 파라미터 오류 |
| 502 | Solar API 호출 실패 |
| 500 | 서버 내부 오류 |

---

## 1. 로딩 페이지 — `GET /loadingpage`

n8n 분석이 완료되었는지 확인 (Polling용)

### 요청

```
GET /loadingpage?user_id=유저고유ID
```

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| user_id | string | ✅ | 사용자 UUID |

### 응답

```json
// 분석 완료
{
  "status": "completed",
  "record_id": "recABC123xyz"
}

// 아직 분석 중
{
  "status": "pending",
  "record_id": null
}
```

### 프론트 구현 가이드

- 2~3초 간격으로 폴링
- `status === "completed"` 되면 `record_id`를 저장하고 리포트 페이지로 이동
- 타임아웃 설정 권장 (예: 60초 후 "분석이 지연되고 있습니다" 안내)

---

## 2. 종합 분석 리포트 — `GET /report`

처방전 상세 분석 데이터 조회

### 요청

```
GET /report?record_id=recABC123xyz
```

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| record_id | string | ✅ | 처방전 Airtable record ID (`rec`으로 시작) |

### 응답

```json
{
  "prescription": {
    "record_id": "recABC123xyz",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "scanned_at": "2025-05-20T14:30:00.000Z",
    "medication_count": 3,
    "solar_summary": "메트포르민, 아토르바스타틴, 오메프라졸 복용 시 비타민B12, CoQ10, 마그네슘 보충 권장..."
  },
  "medications": [
    {
      "drug_name": "메트포르민",
      "dosage": "500mg",
      "frequency": "1일 2회",
      "duration_days": 90,
      "depleted_nutrients": "비타민B12, 엽산",
      "recommended_supplements": "비타민B12 1000mcg, 엽산 400mcg",
      "caution_notes": "식후 복용, 비타민B12는 공복에 별도 복용"
    },
    {
      "drug_name": "아토르바스타틴",
      "dosage": "20mg",
      "frequency": "1일 1회",
      "duration_days": null,
      "depleted_nutrients": "CoQ10",
      "recommended_supplements": "CoQ10 100~200mg",
      "caution_notes": "자몽 주스와 함께 복용 금지"
    }
  ]
}
```

### 에러

```json
// record_id가 존재하지 않을 때
HTTP 404
{"detail": "해당 처방전을 찾을 수 없습니다."}
```

---

## 3. 과거 기록 조회 — `GET /history`

사용자의 모든 리포트 목록 (최신순)

### 요청

```
GET /history?user_id=유저고유ID
```

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| user_id | string | ✅ | 사용자 UUID |

### 응답

```json
[
  {
    "record_id": "recABC123xyz",
    "scanned_at": "2025-05-20T14:30:00.000Z",
    "medication_count": 3,
    "solar_summary": "메트포르민, 아토르바스타틴 기반 분석..."
  },
  {
    "record_id": "recDEF456abc",
    "scanned_at": "2025-05-18T09:00:00.000Z",
    "medication_count": 2,
    "solar_summary": "오메프라졸, 로사르탄 기반 분석..."
  }
]
```

- 데이터 없으면 빈 배열 `[]` 반환
- 각 항목의 `record_id`로 `/report` 호출하면 상세 조회 가능

---

## 4. AI 챗봇 — `POST /chatbot`

사용자 질문 → Solar LLM 영양제 추천 응답

### 요청

```
POST /chatbot
Content-Type: application/json

{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "메트포르민 먹고 있는데 어떤 영양제 먹어야 해?",
  "conversation_history": []
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|:----:|------|
| user_id | string | ✅ | 사용자 UUID |
| message | string | ✅ | 사용자 질문 텍스트 |
| conversation_history | array | ❌ | 이전 대화 이력 (멀티턴용) |

### conversation_history 형식 (멀티턴 대화 시)

```json
{
  "conversation_history": [
    {"role": "user", "content": "이전 질문"},
    {"role": "assistant", "content": "이전 답변"},
    {"role": "user", "content": "후속 질문"},
    {"role": "assistant", "content": "후속 답변"}
  ]
}
```

### 응답

```json
{
  "answer": "## 📋 영양소 분석 보고서\n\n### 💊 복용 중인 약물\n- 메트포르민 500mg...",
  "medications_used": ["메트포르민", "아토르바스타틴"]
}
```

- `answer`는 마크다운 형식 (프론트에서 마크다운 렌더링 필요)
- `medications_used`는 분석에 사용된 약물 이름 배열

### 에러

```json
// Solar API 장애 시
HTTP 502
{"detail": "Solar API 호출 실패: timeout"}
```

---

## 5. 헬스체크 — `GET /health`

서버 상태 확인

```
GET /health

응답: {"status": "ok"}
```

---

## 프론트엔드 연동 예시 (JavaScript)

```javascript
const BASE_URL = "https://배포URL.up.railway.app";

// 로딩 페이지 폴링
async function checkStatus(userId) {
  const res = await fetch(`${BASE_URL}/loadingpage?user_id=${userId}`);
  return await res.json();
}

// 리포트 조회
async function getReport(recordId) {
  const res = await fetch(`${BASE_URL}/report?record_id=${recordId}`);
  return await res.json();
}

// 히스토리 조회
async function getHistory(userId) {
  const res = await fetch(`${BASE_URL}/history?user_id=${userId}`);
  return await res.json();
}

// 챗봇 질문
async function askChatbot(userId, message, history = []) {
  const res = await fetch(`${BASE_URL}/chatbot`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      message: message,
      conversation_history: history,
    }),
  });
  return await res.json();
}
```

---

## 참고

- **Swagger UI** (`/docs`)에서 모든 API를 브라우저에서 직접 테스트할 수 있습니다
- **폴링 간격**: `/loadingpage`는 2~3초 간격 권장
- **answer 렌더링**: 챗봇 응답은 마크다운이므로 `marked.js` 등으로 렌더링
- **record_id 형식**: Airtable record ID는 항상 `rec`으로 시작하는 17자 문자열
