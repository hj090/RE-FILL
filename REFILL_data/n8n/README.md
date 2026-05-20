# n8n 노드 코드

## pii-drop-filter.js

**용도**: 처방전 OCR/Extract 결과에서 개인정보를 제거하는 Function 노드 코드

### n8n에 적용하는 법

1. 워크플로우에서 **Information Extract** 노드 뒤에 **Function** 노드 추가
2. `pii-drop-filter.js` 내용을 Function 노드의 코드 영역에 붙여넣기
3. 이 노드의 출력을 Solar LLM 호출 노드에 연결

### 동작 방식

```
Information Extract 출력
  ↓
[PII Drop Filter]
  - patient_info 객체 삭제
  - hospital_info 객체 삭제
  - 개인정보 키(이름, 주민번호, 전화번호 등) 삭제
  - raw_ocr_text 내 개인정보 패턴 마스킹 → [REDACTED]
  ↓
약물 정보만 남은 깨끗한 JSON
  ↓
Solar LLM 분석
```

### 제거 대상

| 카테고리 | 필드 |
|----------|------|
| 환자 | 이름, 주민번호, 전화번호, 주소 |
| 병원 | 병원명, 의사명, 면허번호 |
| 관리 | 처방전번호 |

### 보존 대상

- `user_id` (프론트에서 전달된 익명 UUID)
- `medications[]` (약물 성분명, 용량, 빈도, 기간)
- `scanned_at` (스캔 시각)
