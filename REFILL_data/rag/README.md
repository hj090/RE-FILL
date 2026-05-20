# RAG (Retrieval-Augmented Generation) 모듈

약물-영양소 매핑 지식을 벡터 검색으로 제공하는 모듈입니다.

## 구조

```
rag/
├── knowledge/
│   └── drug_nutrient_mapping.json   ← 약물-영양소 매핑 데이터 (논문 출처 포함)
├── chroma_db/                       ← 벡터 DB (build 후 생성됨)
├── build_vectordb.py                ← 벡터 DB 빌드 스크립트
├── search.py                        ← 검색 모듈 (챗봇에서 사용)
├── requirements.txt
└── README.md
```

## 사용법

### 1. 의존성 설치
```bash
cd rag
pip install -r requirements.txt
```

### 2. 벡터 DB 빌드 (최초 1회)
```bash
python build_vectordb.py
```
- Upstage Solar Embedding API로 20개 약물 매핑 데이터를 벡터화
- `chroma_db/` 폴더에 저장됨

### 3. 검색 테스트
```bash
python search.py
```

### 4. 챗봇 연동
챗봇(`chatbot/solar_client.py`)이 자동으로 이 모듈을 import합니다.
- 벡터 DB가 있으면: RAG 검색 결과를 Solar Pro 3에 전달
- 벡터 DB가 없으면: RAG 없이 기본 동작 (에러 안 남)

## 지식 데이터 추가 방법

1. `knowledge/drug_nutrient_mapping.json`에 새 항목 추가
2. `python build_vectordb.py` 재실행
3. 챗봇 서버 재시작

## 현재 포함된 약물 (20종)

| # | 약물 계열 | 대표 약물 |
|---|-----------|-----------|
| 1 | 비구아나이드 | 메트포르민 |
| 2 | 스타틴 | 아토르바스타틴, 로수바스타틴 |
| 3 | PPI | 오메프라졸, 란소프라졸 |
| 4 | 루프이뇨제 | 푸로세미드 |
| 5 | 티아지드이뇨제 | 히드로클로로티아지드 |
| 6 | ACE 억제제 | 에날라프릴, 리시노프릴 |
| 7 | 항경련제 | 페니토인, 카르바마제핀 |
| 8 | 경구 피임약 | 에티닐에스트라디올 복합제 |
| 9 | 코르티코스테로이드 | 프레드니솔론, 덱사메타손 |
| 10 | NSAID | 이부프로펜, 나프록센 |
| 11 | 항생제 | 아목시실린, 세팔로스포린 |
| 12 | H2 길항제 | 파모티딘, 시메티딘 |
| 13 | 설폰요소제 | 글리메피리드 |
| 14 | 베타차단제 | 아테놀롤, 메토프롤롤 |
| 15 | ARB | 로사르탄, 발사르탄 |
| 16 | 칼슘채널차단제 | 암로디핀 |
| 17 | SSRI | 에스시탈로프람, 서트랄린 |
| 18 | 벤조디아제핀 | 알프라졸람, 로라제팜 |
| 19 | 비스포스포네이트 | 알렌드로네이트 |
| 20 | 갑상선 호르몬제 | 레보티록신 |
