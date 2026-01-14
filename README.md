# Targeting Validation MCP

**설명**  
이 MCP는 광고 타겟 조건을 입력받아 **정규화된 구조**로 변환하고, 명백한 **오류/위험 조건**을 검증합니다.  
- 성공/경고/실패 메시지가 명확히 구분됨  
- 실패 시 항상 동일한 메시지 반환  
- LLM이 제공하기 어려운 **재현성, 검증 가능성, 외부 상태 반영** 기능 제공  

---

## 사용법

### 입력 파라미터
| 파라미터   | 타입 | 설명 |
| ---------- | ---- | ---- |
| age_range  | str  | 연령 범위 (예: "20-30") |
| gender     | str  | 성별 ("남자", "여자", "무관") |
| interests  | list | 관심사 목록 (예: ["패션", "온라인쇼핑"]) |
| region     | str  | 지역 ("서울", "부산", "전체" 등) |

### 반환 구조
- `normalized_target`: 정규화된 입력 데이터  
- `validation_details`: 각 입력 항목 검증 여부  
- `warnings` (선택적): 경고 항목  
- `warning_text` (선택적): 경고 설명  
- `success_text` (선택적): 성공 메시지  
- `error` (선택적): 실패 메시지  

---

## 예시

### 성공 케이스
```json
{
  "normalized_target": {
    "age_range": "25-34",
    "gender": "남자",
    "interests": ["온라인쇼핑", "패션"],
    "region": "SEOUL"
  },
  "validation_details": [
    {
      "age_range_valid": true,
      "gender_valid": true,
      "interests_valid": true,
      "region_valid": true
    }
  ],
  "success_text": "입력한 타겟 조건이 정책상 문제없이 검증되었습니다."
}

### 경고 케이스

{
  "normalized_target": {
    "age_range": "40-60",
    "gender": "여자",
    "interests": ["인천보증금지원정책"],
    "region": "SEOUL"
  },
  "validation_details": [
    {
      "age_range_valid": true,
      "gender_valid": true,
      "interests_valid": true,
      "region_valid": true
    }
  ],
  "warnings": [
    "관심사 '인천보증금지원정책'이 입력 지역 'SEOUL'과 일치하지 않음",
    "광고 금지/위험 상품 포함"
  ],
  "warning_text": "시스템 오류는 아니나, 실제 집행 전 정책 검토를 권장합니다."
}

### 실패 케이스

{
  "error": "타겟 조건 검증 실패. 입력값을 확인해주세요."
}

