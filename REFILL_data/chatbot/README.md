# REFILL 챗봇 백엔드

처방약 기반 영양제 추천 챗봇 API 서버

## 구조

```
chatbot/
├── main.py              # FastAPI 앱 (엔드포인트)
├── solar_client.py      # Upstage Solar Pro 3 호출
├── airtable_client.py   # Airtable 조회/저장
├── config.py            # 환경변수 로드
├── requirements.txt     # 의존성
├── .env.example         # 환경변수 템플릿
└── README.md
```

## 설치 & 실행

```bash
cd chatbot
pip install -r requirements.txt
cp .env.example .env
# .env 파일에 실제 키 입력
python main.py
```

서버가 `http://localhost:8000` 에서 실행됩니다.

## API

### POST /chat

사용자 질문에 대해 약물 기반 영양제 추천 응답을 반환합니다.

**Request:**
```json
{
  "user_id": "uuid-from-frontend",
  "message": "메트포르민 먹고 있는데 어떤 영양제 먹어야 해?",
  "conversation_history": []
}
```

**Response:**
```json
{
  "answer": "메트포르민을 복용 중이시군요. 장기 복용 시 비타민B12와 엽산이...",
  "medications_used": ["메트포르민", "아토르바스타틴"]
}
```

### GET /health

헬스체크 엔드포인트

## 동작 흐름

```
프론트(A) → POST /chat (user_id + 질문)
  → Airtable에서 해당 user의 최근 약물 목록 조회
  → 약물 정보를 컨텍스트로 Solar Pro 3에 전달
  → LLM 응답을 Chat_Sessions에 저장
  → 응답 반환
```

## 프론트(A) 연동 가이드

- `user_id`: 프론트에서 UUID v4 생성 → localStorage 저장 → 모든 요청에 포함
- `conversation_history`: 멀티턴 대화 시 이전 대화를 배열로 전달
  ```json
  [
    {"role": "user", "content": "이전 질문"},
    {"role": "assistant", "content": "이전 답변"}
  ]
  ```
- CORS: 필요 시 main.py에 CORSMiddleware 추가 예정
