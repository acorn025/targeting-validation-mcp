# Targeting Validation MCP

## 개요
광고 타겟 조건을 입력받아:
- 구조를 정규화하고
- 명백한 오류/위험 조건을 검증하며
- 실패 시 항상 동일한 메시지 정책으로 응답

하는 MCP입니다.  
운영, 기획, BM 관점에서 **예측 가능하고 일관된 결과**를 제공합니다.

---

## 기능

1. **정규화된 타겟 구조 제공**
    - 연령, 성별, 관심사, 지역을 표준화
2. **검증**
    - 필수 입력값 체크
    - 구조 오류/부적합 입력 감지
3. **경고(Warnings)**
    - 미성년자 + 민감 관심사
    - 지역과 관심사 불일치
    - 광고 금지/위험 상품 포함
    - 경고 발생 시: `"시스템 오류는 아니나, 실제 집행 전 정책 검토를 권장합니다."`
4. **실패(Failure)**
    - 입력 자체가 잘못된 경우
    - 실패 메시지는 항상 동일:
      `"타겟 조건 검증 실패. 입력값을 확인해주세요."`
5. **성공(Success)**
    - 모든 조건이 유효한 경우
    - 메시지: `"입력한 타겟 조건이 정책상 문제없이 검증되었습니다."`

---

## 사용법

```python
from fastmcp import FastMCP

app = FastMCP("Targeting Validation MCP")

@app.tool()
def validate_targeting_conditions(
    age_range: str,
    gender: str,
    interests: list,
    region: str
) -> dict:
    ...
    return response

def main():
    app.run()

if __name__ == "__main__":
    main()
입력 예시
python
코드 복사
age_range = "20-29"
gender = "여자"
interests = ["인천월세지원정책"]
region = "상주"
반환 예시
성공
json
코드 복사
{
    "success_text": "입력한 타겟 조건이 정책상 문제없이 검증되었습니다.",
    "normalized_target": {
        "age_range": "20-29",
        "gender": "여자",
        "interests": ["인천월세지원정책"],
        "region": "SANGJU"
    }
}
경고
json
코드 복사
{
    "warnings": [
        "관심사 '인천월세지원정책'가 입력 지역 '상주'과 일치하지 않음",
        "일부 광고 정책에서 제한될 수 있음"
    ],
    "warning_text": "시스템 오류는 아니나, 실제 집행 전 정책 검토를 권장합니다.",
    "normalized_target": {
        "age_range": "20-29",
        "gender": "여자",
        "interests": ["인천월세지원정책"],
        "region": "SANGJU"
    }
}
실패
json
코드 복사
{
    "success": False,
    "error": "타겟 조건 검증 실패. 입력값을 확인해주세요."
}
