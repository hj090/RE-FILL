"""
식품의약품안전처 DUR 품목정보 API에서 데이터를 가져와
RAG용 JSON 파일로 저장하는 스크립트

사용법:
  cd rag
  python fetch_dur_data.py

필요 환경변수:
  DUR_API_KEY=발급받은인증키
"""

import os
import json
import time
import requests
from dotenv import load_dotenv

# chatbot/.env에서 키 로드
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "chatbot", ".env"))

DUR_API_KEY = os.getenv("DUR_API_KEY")
DUR_BASE_URL = "https://apis.data.go.kr/1471000/DURPrdlstInfoService03"

if not DUR_API_KEY:
    print("ERROR: DUR_API_KEY가 .env에 설정되지 않았습니다.")
    exit(1)


def fetch_dur_contraindications(page=1, num_of_rows=100):
    """병용금기 정보 조회"""
    url = f"{DUR_BASE_URL}/getUsjntTabooInfoList03"
    params = {
        "serviceKey": DUR_API_KEY,
        "pageNo": page,
        "numOfRows": num_of_rows,
        "type": "json",
    }
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        print(f"  병용금기 API 오류: {resp.status_code}")
        return []
    
    try:
        data = resp.json()
        body = data.get("body", {})
        items = body.get("items", [])
        return items if isinstance(items, list) else []
    except Exception as e:
        print(f"  JSON 파싱 오류: {e}")
        return []


def fetch_dur_dosage_caution(page=1, num_of_rows=100):
    """용량주의 정보 조회"""
    url = f"{DUR_BASE_URL}/getCpctyAtentInfoList03"
    params = {
        "serviceKey": DUR_API_KEY,
        "pageNo": page,
        "numOfRows": num_of_rows,
        "type": "json",
    }
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        print(f"  용량주의 API 오류: {resp.status_code}")
        return []
    
    try:
        data = resp.json()
        body = data.get("body", {})
        items = body.get("items", [])
        return items if isinstance(items, list) else []
    except Exception as e:
        print(f"  JSON 파싱 오류: {e}")
        return []


def fetch_dur_product_info(page=1, num_of_rows=100):
    """DUR 품목정보 조회"""
    url = f"{DUR_BASE_URL}/getDurPrdlstInfoList03"
    params = {
        "serviceKey": DUR_API_KEY,
        "pageNo": page,
        "numOfRows": num_of_rows,
        "type": "json",
    }
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        print(f"  품목정보 API 오류: {resp.status_code}")
        return []
    
    try:
        data = resp.json()
        body = data.get("body", {})
        items = body.get("items", [])
        return items if isinstance(items, list) else []
    except Exception as e:
        print(f"  JSON 파싱 오류: {e}")
        return []


def fetch_dur_elderly_caution(page=1, num_of_rows=100):
    """노인주의 정보 조회"""
    url = f"{DUR_BASE_URL}/getOdsnAtentInfoList03"
    params = {
        "serviceKey": DUR_API_KEY,
        "pageNo": page,
        "numOfRows": num_of_rows,
        "type": "json",
    }
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        print(f"  노인주의 API 오류: {resp.status_code}")
        return []
    
    try:
        data = resp.json()
        body = data.get("body", {})
        items = body.get("items", [])
        return items if isinstance(items, list) else []
    except Exception as e:
        print(f"  JSON 파싱 오류: {e}")
        return []


def fetch_dur_pregnancy_caution(page=1, num_of_rows=100):
    """임부금기 정보 조회"""
    url = f"{DUR_BASE_URL}/getPwnmTabooInfoList03"
    params = {
        "serviceKey": DUR_API_KEY,
        "pageNo": page,
        "numOfRows": num_of_rows,
        "type": "json",
    }
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        print(f"  임부금기 API 오류: {resp.status_code}")
        return []
    
    try:
        data = resp.json()
        body = data.get("body", {})
        items = body.get("items", [])
        return items if isinstance(items, list) else []
    except Exception as e:
        print(f"  JSON 파싱 오류: {e}")
        return []


def convert_to_rag_format(contraindications, dosage_cautions, elderly_cautions, pregnancy_cautions):
    """DUR 데이터를 RAG용 JSON 형식으로 변환"""
    rag_data = []
    
    # 병용금기 → RAG 형식
    seen_pairs = set()
    for item in contraindications:
        drug_a = item.get("ITEM_NAME_A", "") or item.get("INGR_NAME_A", "")
        drug_b = item.get("ITEM_NAME_B", "") or item.get("INGR_NAME_B", "")
        reason = item.get("PROHBT_CONTENT", "") or item.get("REMARK", "")
        
        if not drug_a or not drug_b:
            continue
        
        pair_key = f"{drug_a}_{drug_b}"
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)
        
        rag_data.append({
            "id": f"DUR_CONTRA_{len(rag_data)+1:04d}",
            "type": "병용금기",
            "drug_names": [drug_a, drug_b],
            "content": f"[병용금기] {drug_a}와(과) {drug_b}은(는) 함께 복용하면 안 됩니다. {reason}",
            "severity": "높음",
            "source": "식품의약품안전처 DUR 의약품안전사용서비스",
        })
    
    # 용량주의 → RAG 형식
    for item in dosage_cautions:
        drug_name = item.get("ITEM_NAME", "") or item.get("INGR_NAME", "")
        content = item.get("ATENT_CONTENT", "") or item.get("REMARK", "")
        
        if not drug_name:
            continue
        
        rag_data.append({
            "id": f"DUR_DOSE_{len(rag_data)+1:04d}",
            "type": "용량주의",
            "drug_names": [drug_name],
            "content": f"[용량주의] {drug_name}: {content}",
            "severity": "중간",
            "source": "식품의약품안전처 DUR 의약품안전사용서비스",
        })
    
    # 노인주의 → RAG 형식
    for item in elderly_cautions:
        drug_name = item.get("ITEM_NAME", "") or item.get("INGR_NAME", "")
        content = item.get("ATENT_CONTENT", "") or item.get("REMARK", "")
        
        if not drug_name:
            continue
        
        rag_data.append({
            "id": f"DUR_ELDERLY_{len(rag_data)+1:04d}",
            "type": "노인주의",
            "drug_names": [drug_name],
            "content": f"[노인주의] {drug_name}: 65세 이상 고령자 복용 시 주의. {content}",
            "severity": "중간",
            "source": "식품의약품안전처 DUR 의약품안전사용서비스",
        })
    
    # 임부금기 → RAG 형식
    for item in pregnancy_cautions:
        drug_name = item.get("ITEM_NAME", "") or item.get("INGR_NAME", "")
        content = item.get("PROHBT_CONTENT", "") or item.get("REMARK", "")
        grade = item.get("GRADE_NAME", "")
        
        if not drug_name:
            continue
        
        rag_data.append({
            "id": f"DUR_PREG_{len(rag_data)+1:04d}",
            "type": "임부금기",
            "drug_names": [drug_name],
            "content": f"[임부금기] {drug_name}: 임산부 복용 금기. 등급: {grade}. {content}",
            "severity": "높음",
            "source": "식품의약품안전처 DUR 의약품안전사용서비스",
        })
    
    return rag_data


def main():
    print("=" * 50)
    print("DUR 품목정보 데이터 수집 시작")
    print("=" * 50)
    
    # 각 API에서 데이터 수집 (첫 페이지씩)
    print("\n[1/4] 병용금기 정보 조회...")
    contraindications = fetch_dur_contraindications(page=1, num_of_rows=100)
    print(f"  → {len(contraindications)}건 수집")
    time.sleep(1)
    
    print("[2/4] 용량주의 정보 조회...")
    dosage_cautions = fetch_dur_dosage_caution(page=1, num_of_rows=100)
    print(f"  → {len(dosage_cautions)}건 수집")
    time.sleep(1)
    
    print("[3/4] 노인주의 정보 조회...")
    elderly_cautions = fetch_dur_elderly_caution(page=1, num_of_rows=100)
    print(f"  → {len(elderly_cautions)}건 수집")
    time.sleep(1)
    
    print("[4/4] 임부금기 정보 조회...")
    pregnancy_cautions = fetch_dur_pregnancy_caution(page=1, num_of_rows=100)
    print(f"  → {len(pregnancy_cautions)}건 수집")
    
    # RAG 형식으로 변환
    print("\n변환 중...")
    rag_data = convert_to_rag_format(
        contraindications, dosage_cautions, elderly_cautions, pregnancy_cautions
    )
    print(f"  → RAG 데이터 {len(rag_data)}건 생성")
    
    # 저장
    output_path = os.path.join(os.path.dirname(__file__), "knowledge", "dur_safety_info.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(rag_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 저장 완료: {output_path}")
    print(f"   총 {len(rag_data)}건")
    print("\n다음 단계: python build_vectordb.py 실행하여 벡터 DB에 반영")


if __name__ == "__main__":
    main()
