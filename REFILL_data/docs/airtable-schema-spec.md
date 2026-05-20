# Airtable 스키마 명세서 (확정)

> **프로젝트**: 처방전 기반 영양제 추천 시스템  
> **작성일**: 2025-05-20  
> **상태**: ✅ 확정  
> **담당**: B(n8n 파이프라인) ↔ C(챗봇 백엔드)

---

## 1. 설계 원칙

| 원칙 | 설명 |
|------|------|
| **개인정보 미저장** | 환자명, 주민번호, 병원명, 의사명 등 일체 Drop |
| **외부 지식 미수집** | 별도 영양소 DB 구축 없이 Solar LLM 프롬프트 추론으로 커버 |
| **약물 중심 저장** | 성분명·용량·빈도·기간 + LLM 분석 결과만 보관 |

---

## 2. 전체 데이터 흐름

```
처방전 사진
  → n8n: Document Parse (Upstage)
  → n8n: Information Extract
  → n8n: 개인정보 Drop (Function 노드)
  → n8n: Solar LLM 영양소 분석
  → Airtable 저장
  → 챗봇: Airtable 조회 + Solar Pro 3 대화
```

---

## 3. 테이블 구조

### 3-1. `Prescriptions` (처방전 단위)

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|:----:|------|
| `id` | Auto Number | ✅ | PK |
| `user_id` | Single Line Text | ✅ | 익명 사용자 식별자 (해시 or 세션ID) |
| `scanned_at` | Date Time | ✅ | 처방전 스캔 시각 |
| `raw_ocr_text` | Long Text | ❌ | OCR 원문 (개인정보 마스킹 후, 디버깅용) |
| `medication_count` | Number (integer) | ✅ | 처방 약물 수 |
| `solar_summary` | Long Text | ✅ | Solar LLM 종합 분석 요약 |
| `created_at` | Created Time | auto | 레코드 생성 시각 |

### 3-2. `Medications` (약물 단위)

> Prescriptions : Medications = 1 : N

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|:----:|------|
| `id` | Auto Number | ✅ | PK |
| `prescription_id` | Link to `Prescriptions` | ✅ | FK |
| `drug_name` | Single Line Text | ✅ | 약물 성분명 (예: 메트포르민) |
| `dosage` | Single Line Text | ✅ | 용량 (예: 500mg) |
| `frequency` | Single Line Text | ✅ | 복용 빈도 (예: 1일 2회) |
| `duration_days` | Number (integer) | ❌ | 복용 기간 (일 단위) |
| `depleted_nutrients` | Single Line Text | ✅ | 고갈 가능 영양소 (쉼표 구분) |
| `recommended_supplements` | Single Line Text | ✅ | 추천 영양제 (쉼표 구분) |
| `caution_notes` | Long Text | ❌ | 주의사항 |

### 3-3. `Chat_Sessions` (챗봇 대화 로그, 선택사항)

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|:----:|------|
| `id` | Auto Number | ✅ | PK |
| `user_id` | Single Line Text | ✅ | 사용자 식별자 |
| `prescription_id` | Link to `Prescriptions` | ❌ | 참조 처방전 |
| `question` | Long Text | ✅ | 사용자 질문 |
| `answer` | Long Text | ✅ | 챗봇 응답 |
| `asked_at` | Date Time | ✅ | 질문 시각 |

---

## 4. 개인정보 Drop 명세

n8n Function 노드에서 Airtable 저장 **전에** 아래 필드를 제거합니다.

| 제거 대상 | 처리 |
|-----------|------|
| 환자 이름 | 완전 삭제 |
| 주민등록번호 | 완전 삭제 |
| 전화번호 | 완전 삭제 |
| 주소 | 완전 삭제 |
| 병원명 | 완전 삭제 |
| 의사명 | 완전 삭제 |
| 처방전 관리번호 | 완전 삭제 |

**보존 대상**: 약물 성분명, 용량, 복용 빈도, 복용 기간

---

## 5. B 담당자 확인 요청 사항

n8n 워크플로우에서 아래 JSON 구조로 출력해주세요:

```json
{
  "user_id": "anonymous_hash_or_session_id",
  "scanned_at": "2025-05-20T14:30:00Z",
  "medications": [
    {
      "drug_name": "메트포르민",
      "dosage": "500mg",
      "frequency": "1일 2회",
      "duration_days": 30
    },
    {
      "drug_name": "아토르바스타틴",
      "dosage": "10mg",
      "frequency": "1일 1회",
      "duration_days": 30
    }
  ],
  "solar_analysis": {
    "summary": "메트포르민 장기 복용 시 비타민B12 흡수 저하 가능...",
    "per_drug": [
      {
        "drug_name": "메트포르민",
        "depleted_nutrients": "비타민B12, 엽산",
        "recommended_supplements": "비타민B12 1000mcg, 엽산 400mcg",
        "caution_notes": "신장 기능 저하 시 B12 보충 필수 확인"
      },
      {
        "drug_name": "아토르바스타틴",
        "depleted_nutrients": "코엔자임Q10",
        "recommended_supplements": "CoQ10 100-200mg",
        "caution_notes": "근육통 발생 시 CoQ10 보충 고려"
      }
    ]
  }
}
```

### B 확인 완료:
1. ✅ 위 JSON 구조로 출력 가능
2. ✅ `user_id`는 **프론트(A)에서 UUID v4로 생성** → localStorage 저장 → 업로드 시 함께 전송 → n8n은 그대로 전달
3. ✅ `duration_days`가 처방전에 없는 경우 `null` 처리

---

## 6. 다음 단계 (C 파트)

| 순서 | 작업 | 선행 조건 |
|:----:|------|-----------|
| 1 | n8n → Airtable 저장 연동 | B의 JSON 출력 확정 |
| 2 | 개인정보 Drop 필터 (n8n Function or Python) | 위 스키마 확정 ✅ |
| 3 | 챗봇 백엔드 (Airtable 조회 + Solar Pro 3) | Airtable에 데이터 1건 이상 |
| 4 | 프론트(A)와 API 연동 | 챗봇 엔드포인트 완성 |

---

## 7. 기술 스택 (C 파트)

- **언어**: Python 3.11+
- **LLM**: Upstage Solar Pro 3 (chat), Solar Embedding (필요 시)
- **DB**: Airtable (via REST API)
- **배포**: 추후 결정 (Railway / Vercel Serverless / n8n 내장)
- **환경변수**: `.env` 파일로 관리 (`UPSTAGE_API_KEY`, `AIRTABLE_API_KEY`, `AIRTABLE_BASE_ID`)
