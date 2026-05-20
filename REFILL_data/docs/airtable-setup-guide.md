# Airtable 테이블 생성 가이드

> **상태**: ✅ 생성 완료 (2025-05-20)  
> **Base 이름**: REFILL

---

## 생성된 테이블 구조

### 테이블 1: `Prescriptions`

| 필드명 | 타입 | Primary | 비고 |
|--------|------|:-------:|------|
| `user_id` | Single line text | ✅ | 프론트에서 전달하는 UUID |
| `scanned_at` | Date (time 포함) | | 처방전 스캔 시각 |
| `raw_ocr_text` | Long text | | OCR 원문 (개인정보 마스킹 후) |
| `medication_count` | Number (Integer) | | 처방 약물 수 |
| `solar_summary` | Long text | | Solar LLM 분석 요약 |
| `created_at` | Created time | | 자동 생성 |

### 테이블 2: `Medications`

| 필드명 | 타입 | Primary | 비고 |
|--------|------|:-------:|------|
| `drug_name` | Single line text | ✅ | 약물 성분명 |
| `prescription_id` | Link to Prescriptions | | FK (처방전 연결) |
| `dosage` | Single line text | | 용량 (예: 500mg) |
| `frequency` | Single line text | | 복용 빈도 (예: 1일 2회) |
| `duration_days` | Number (Integer) | | 복용 기간 (일), 없으면 비워둠 |
| `depleted_nutrients` | Single line text | | 고갈 영양소 (쉼표 구분) |
| `recommended_supplements` | Single line text | | 추천 영양제 (쉼표 구분) |
| `caution_notes` | Long text | | 주의사항 |

### 테이블 3: `Chat_Sessions`

| 필드명 | 타입 | Primary | 비고 |
|--------|------|:-------:|------|
| `user_id` | Single line text | ✅ | 사용자 식별자 |
| `prescription_id` | Link to Prescriptions | | 참조 처방전 (선택) |
| `question` | Long text | | 사용자 질문 |
| `answer` | Long text | | 챗봇 응답 |
| `asked_at` | Date (time 포함) | | 질문 시각 |

---

## 테이블 관계도

```
Prescriptions (1) ──→ (N) Medications
      │
      └──────────────→ (N) Chat_Sessions
```

- 하나의 처방전에 여러 약물이 연결됨
- 하나의 처방전에 여러 대화가 연결될 수 있음

---

## Airtable 제약사항 참고

- **Primary 필드**(첫 번째 필드)는 Link to another record 타입 불가
  - 그래서 `Medications`의 Primary는 `drug_name`, `prescription_id`는 두 번째 필드
- 코드에서는 필드 이름으로 조회하므로 필드 순서는 동작에 영향 없음

---

## 환경변수 연결

Airtable Base ID 확인 방법:
1. 브라우저에서 해당 Base 열기
2. URL: `https://airtable.com/appXXXXXXXXX/...`
3. `app`으로 시작하는 부분 = Base ID

이 값을 `chatbot/.env`에 입력:
```
AIRTABLE_BASE_ID=appXXXXXXXXX
```

---

## 팀원 참고

- **B (n8n)**: 데이터 저장 시 위 필드명과 정확히 일치하게 매핑해주세요
- **A (프론트)**: `user_id`는 UUID v4로 생성해서 모든 요청에 포함
- **C (백엔드)**: `chatbot/airtable_client.py`가 위 테이블을 조회/저장합니다
