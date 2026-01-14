from fastmcp import FastMCP

app = FastMCP("Targeting Validation MCP")

@app.tool()
def validate_targeting_conditions(
    age_range: str,
    gender: str,
    interests: list,
    region: str
) -> dict:
    warnings = []
    validation_details = []

    # -----------------
    # 실패 조건 (입력 자체 오류)
    # -----------------
    if not age_range or not gender or not interests or not region:
        return {
            "success": False,
            "error": "타겟 조건 검증 실패. 입력값을 확인해주세요."
        }

    # -----------------
    # 경고 조건
    # -----------------
    # 1. 미성년자(1~19세) 또는 민감 관심사 포함
    sensitive_interests = ["ADULT", "ALCOHOL", "DRUGS"]
    try:
        age_numbers = [int(a) for a in age_range.replace(" ", "").split("-")]
    except:
        age_numbers = [0, 0]  # 파싱 실패 시 안전 처리
    if (age_numbers[0] <= 19) or any(i.upper() in sensitive_interests for i in interests):
        warnings.append("미성년자 연령대이거나 민감 관심사 포함")
        warnings.append("일부 광고 정책에서 제한될 수 있음")

    # 2. 지역/관심사 불일치
    region_upper = region.upper()
    for interest in interests:
        for reg in ["SEOUL","BUSAN","DAEGU","INCHEON","GWANGJU","DAEJEON","GYEONGGI"]:
            if reg in interest.upper() and reg != region_upper:
                warnings.append(f"관심사 '{interest}'가 입력 지역 '{region}'과 일치하지 않음")
                warnings.append("일부 광고 정책에서 제한될 수 있음")

    # 3. 위험 상품 포함
    risk_items = ["DRUG", "ILLEGAL"]
    if any(ri in [i.upper() for i in interests] for ri in risk_items):
        warnings.append("광고 금지/위험 상품 포함")
        warnings.append("일부 광고 정책에서 제한될 수 있음")

    # -----------------
    # 검증 상세
    # -----------------
    validation_details.append({
        "age_range_valid": True if age_range else False,
        "gender_valid": True if gender else False,
        "interests_valid": True if interests else False,
        "region_valid": True if region else False
    })

    # -----------------
    # 응답 구성
    # -----------------
    response = {
        "normalized_target": {
            "age_range": age_range,
            "gender": gender.upper(),
            "interests": [i.upper() for i in interests],
            "region": region_upper
        },
        "validation_details": validation_details
    }

    if warnings:
        response["warnings"] = warnings
        response["warning_text"] = "시스템 오류는 아니나, 실제 집행 전 정책 검토를 권장합니다."
    else:
        response["success_text"] = "입력한 타겟 조건이 정책상 문제없이 검증되었습니다."

    return response

def main():
    app.run()

if __name__ == "__main__":
    main()

