from fastmcp import FastMCP

app = FastMCP("Targeting Validation MCP")

@app.tool()
def validate_targeting_conditions(
    age_range: str,
    gender: str,
    interests: list,
    budget: int,
    region: str
) -> dict:
    warnings = []
    validation_details = []

    # -----------------
    # 실패 조건 (입력 자체 오류)
    # -----------------
    allowed_regions = ["SEOUL", "BUSAN", "ALL"]
    if region.upper() not in allowed_regions:
        return {
            "success": False,
            "error": "타겟 조건 검증 실패. 입력값을 확인해주세요."
        }

    if not (0 < budget <= 100000000):
        return {
            "success": False,
            "error": "타겟 조건 검증 실패. 입력값을 확인해주세요."
        }

    # -----------------
    # 경고 조건
    # -----------------
    if age_range == "13-17" and any(
        interest.upper() in ["FINANCE", "INVESTMENT"] for interest in interests
    ):
        warnings.append("미성년자 연령대에 금융/투자 관심사 포함")
        warnings.append("일부 광고 정책에서 제한될 수 있음")

    # -----------------
    # 검증 상세
    # -----------------
    validation_details.append({
        "age_range_valid": True if age_range else False,
        "gender_valid": True if gender else False,
        "interests_valid": True if interests else False,
        "budget_valid": True if 0 < budget <= 100000000 else False,
        "region_valid": True if region.upper() in allowed_regions else False
    })

    # -----------------
    # 응답 구성
    # -----------------
    response = {
        "normalized_target": {
            "age_range": age_range,
            "gender": gender.upper(),
            "interests": [i.upper() for i in interests],
            "budget": budget,
            "region": region.upper()
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

