/**
 * n8n Function 노드: 개인정보 Drop 필터
 * 
 * 위치: Document Parse → Information Extract → [이 노드] → Solar LLM
 * 
 * 역할:
 * - OCR/Extract 결과에서 개인정보 필드를 완전 제거
 * - 약물 정보만 남겨서 다음 노드로 전달
 * - raw_ocr_text에서도 개인정보 패턴을 마스킹
 */

// === 제거할 필드 키 목록 ===
const PII_FIELDS = [
  // 환자 정보
  'patient_name', 'name', '환자명', '성명',
  'resident_number', 'rrn', '주민등록번호', '주민번호',
  'phone', 'phone_number', 'tel', '전화번호', '연락처',
  'address', '주소', '거주지',
  
  // 병원/의사 정보
  'hospital', 'hospital_name', '병원명', '의료기관',
  'doctor', 'doctor_name', '의사명', '처방의',
  'license_number', '면허번호',
  
  // 처방전 관리
  'prescription_number', 'prescription_id', '처방전번호', '관리번호',
];

// === OCR 텍스트에서 마스킹할 정규식 패턴 ===
const PII_PATTERNS = [
  // 주민등록번호: 000000-0000000
  /\d{6}\s*[-–]\s*\d{7}/g,
  // 전화번호: 010-0000-0000, 02-000-0000 등
  /\d{2,3}\s*[-–]\s*\d{3,4}\s*[-–]\s*\d{4}/g,
  // 이름 패턴 (성명: 홍길동)
  /(성명|환자명|이름)\s*[:：]\s*[가-힣]{2,5}/g,
  // 병원명 패턴
  /(병원|의료기관|의원|클리닉)\s*[:：]\s*[가-힣a-zA-Z\s]{2,20}/g,
  // 의사명 패턴
  /(의사|처방의|담당의)\s*[:：]\s*[가-힣]{2,5}/g,
  // 주소 패턴 (시/도로 시작)
  /(주소)\s*[:：]\s*.{5,50}/g,
];

// === 메인 로직 ===
const items = $input.all();
const output = [];

for (const item of items) {
  const data = { ...item.json };
  
  // 1) 최상위 필드에서 개인정보 제거
  for (const key of Object.keys(data)) {
    if (PII_FIELDS.includes(key.toLowerCase())) {
      delete data[key];
    }
  }
  
  // 2) patient_info 객체가 있으면 통째로 제거
  if (data.patient_info) {
    delete data.patient_info;
  }
  
  // 3) hospital_info 객체가 있으면 통째로 제거
  if (data.hospital_info) {
    delete data.hospital_info;
  }
  
  // 4) raw_ocr_text가 있으면 패턴 마스킹
  if (data.raw_ocr_text) {
    let masked = data.raw_ocr_text;
    for (const pattern of PII_PATTERNS) {
      masked = masked.replace(pattern, '[REDACTED]');
    }
    data.raw_ocr_text = masked;
  }
  
  // 5) medications 배열은 그대로 보존 (약물 정보 = 핵심 데이터)
  // drug_name, dosage, frequency, duration_days 등
  
  // 6) user_id가 없으면 경고 로그
  if (!data.user_id) {
    console.warn('[PII Filter] user_id가 없습니다. 프론트에서 전달되었는지 확인하세요.');
  }
  
  output.push({ json: data });
}

return output;
