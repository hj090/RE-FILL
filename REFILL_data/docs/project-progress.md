# REFILL 프로젝트 진행 현황

> **프로젝트**: 처방전 기반 영양제 추천 시스템  
> **최종 업데이트**: 2025-05-20  

---

## 팀 역할

| 담당 | 역할 | 주요 작업 |
|:----:|------|-----------|
| **A** | 프론트엔드 | 챗봇 UI, 처방전 업로드 화면, user_id(UUID) 생성 |
| **B** | 데이터 파이프라인 | n8n 워크플로우 (OCR → 추출 → 개인정보 Drop → Solar 분석 → Airtable 저장) |
| **C** | 챗봇 백엔드 | FastAPI 서버, Solar Pro 3 연동, Airtable 조회 |

---

## 전체 아키텍처

```
[프론트 A]
  │
  ├─ 처방전 사진 업로드 ──→ [n8n B]
  │                           ├─ Document Parse (Upstage)
  │                           ├─ Information Extract
  │                           ├─ 개인정보 Drop (Function 노드)
  │                           ├─ Solar LLM 영양소 분석
  │                           └─ Airtable 저장
  │
  └─ 챗봇 질문 ──→ [백엔드 C]
                      ├─ Airtable에서 약물 조회
                      ├─ Solar Pro 3 호출 (약물 컨텍스트 포함)
                      ├─ 대화 로그 저장
                      └─ 응답 반환
```

---

## ✅ 완료된 작업

### 1. Airtable 스키마 확정
- **파일**: `docs/airtable-schema-spec.md`
- **내용**: 3개 테이블 구조 (Prescriptions, Medications, Chat_Sessions)
- **핵심 결정사항**:
  - 개인정보 일체 미저장 (환자명, 주민번호, 병원명 등 Drop)
  - 외부 영양소 DB 미구축 (Solar LLM 프롬프트 추론으로 대체)
  - `user_id`는 프론트(A)에서 UUID v4 생성 → 모든 요청에 포함
  - `duration_days` 없으면 null 허용

### 2. 개인정보 Drop 필터 코드
- **파일**: `n8n/pii-drop-filter.js`
- **용도**: B가 n8n Function 노드에 붙여넣을 코드
- **동작**:
  - `patient_info`, `hospital_info` 객체 통째로 삭제
  - 이름/주민번호/전화번호 등 키 이름 기반 삭제
  - `raw_ocr_text` 내 개인정보 패턴 → `[REDACTED]` 마스킹
  - `medications` 배열과 `user_id`는 그대로 통과

### 3. 챗봇 백엔드 코드
- **폴더**: `chatbot/`
- **기술 스택**: Python + FastAPI + Upstage Solar Pro 3 + Airtable REST API
- **엔드포인트**:
  - `POST /chat` — 사용자 질문 → 영양제 추천 응답
  - `GET /health` — 헬스체크
- **특징**:
  - 시스템 프롬프트에 약물→영양소 매핑 지식 내장 (RAG 불필요)
  - 멀티턴 대화 지원 (`conversation_history` 파라미터)
  - 대화 로그 자동 저장

### 4. 환경변수 설정
- **파일**: `chatbot/.env` (실제 키 입력 완료)
- **필요한 키**: `UPSTAGE_API_KEY`, `AIRTABLE_API_KEY`, `AIRTABLE_BASE_ID`

---

## 🔜 남은 작업

| 순서 | 작업 | 담당 | 상태 |
|:----:|------|:----:|:----:|
| 5 | Airtable에 테이블 3개 생성 | C | ✅ 완료 |
| 6 | B에게 스키마 명세서 + PII 필터 코드 전달 | C | ⬜ 대기 |
| 7 | n8n에 PII 필터 적용 + 테스트 데이터 1건 저장 | B | ⬜ 대기 |
| 8 | 챗봇 서버 로컬 실행 + API 테스트 | C | ✅ 완료 |
| 8.5 | RAG 시스템 구축 (벡터 DB + 검색) | C | ✅ 완료 |
| 9 | 프론트 ↔ 백엔드 API 연동 | A + C | ⬜ 대기 |
| 10 | 배포 (Railway / Vercel / etc.) | C | ⬜ 대기 |
| 11 | (확장) RAG 지식 데이터 추가 (DUR API 등) | C | 🔮 추후 |

---

## 프로젝트 폴더 구조

```
REFILL_data/
├── docs/
│   ├── airtable-schema-spec.md   ← 스키마 명세서 (확정)
│   ├── airtable-setup-guide.md   ← Airtable 테이블 생성 가이드
│   ├── chatbot-test-log.md       ← 테스트 로그
│   └── project-progress.md       ← 이 파일
├── n8n/
│   ├── pii-drop-filter.js        ← 개인정보 Drop 필터 (B용)
│   └── README.md                 ← 적용 가이드
├── rag/
│   ├── knowledge/
│   │   └── drug_nutrient_mapping.json  ← 약물-영양소 매핑 (논문 출처 포함, 20종)
│   ├── chroma_db/                      ← 벡터 DB (빌드 후 생성, Git 제외)
│   ├── build_vectordb.py               ← 벡터 DB 빌드 스크립트
│   ├── search.py                       ← 검색 모듈
│   ├── view_db.py                      ← DB 조회 스크립트
│   ├── requirements.txt
│   └── README.md
└── chatbot/
    ├── main.py                   ← FastAPI 앱
    ├── solar_client.py           ← Solar Pro 3 호출 (보고서 형식 + RAG)
    ├── airtable_client.py        ← Airtable 조회/저장
    ├── config.py                 ← 환경변수 로드
    ├── requirements.txt          ← Python 의존성
    ├── .env                      ← 실제 API 키 (⚠️ Git 제외)
    ├── .env.example              ← 키 템플릿 (공유용)
    └── README.md                 ← 실행 가이드
```

---

## 팀원별 다음 액션

### A (프론트)
- [ ] `user_id` UUID v4 생성 로직 구현 (localStorage 저장)
- [ ] 챗봇 UI에서 `POST /chat` 호출 연동 준비
- [ ] 요청 형식 참고: `chatbot/README.md`

### B (n8n 파이프라인)
- [ ] `n8n/pii-drop-filter.js`를 Function 노드에 적용
- [ ] 처방전 1장 테스트 → Airtable에 데이터 저장 확인
- [ ] 출력 JSON이 스키마 명세서 섹션 5의 구조와 일치하는지 확인

### C (챗봇 백엔드)
- [ ] Airtable 테이블 생성
- [ ] `pip install -r requirements.txt` → `python main.py` 로컬 테스트
- [ ] B가 테스트 데이터 넣으면 `/chat` 엔드포인트 동작 확인

---

## 참고: API 호출 예시

### 프론트 → 챗봇 요청
```json
POST http://localhost:8000/chat

{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "메트포르민 먹고 있는데 어떤 영양제 먹어야 해?",
  "conversation_history": []
}
```

### 챗봇 → 프론트 응답
```json
{
  "answer": "메트포르민을 복용 중이시군요. 장기 복용 시 비타민B12와 엽산 흡수가 저하될 수 있어요...",
  "medications_used": ["메트포르민", "아토르바스타틴"]
}
```
