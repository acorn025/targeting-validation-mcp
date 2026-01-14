from fastmcp import FastMCP

app = FastMCP("Targeting Validation MCP")

@app.tool()
def validate_targeting_conditions(
    age_range: str,
    gender: str,
    interests: list,
    budget: int
) -> dict:
    warnings = []

    # 예시 정책 룰: 미성년자 + 금융/투자 관심사
    if age_range == "13-17" and any(
        interest in ["FINANCE", "INVESTMENT"] for interest in interests
    ):
        warnings.append("미성년자 연령대에 금융/투자 관심사 포함")
        warnings.append("일부 광고 정책에서 제한될 수 있음")

    # 실패 조건 예시 (입력 자체가 잘못된 경우)
    if budget <= 0:
        return {
            "success": False,
            "error": "타겟 조건 검증에 실패했습니다. 입력한 값을 다시 확인해주세요."
        }

    # 정상 / 경고 공통 응답
    response = {
        "success": True,
        "normalized_target": {
            "age_range": age_range,
            "gender": gender,
            "interests": interests,
            "budget": budget
        }
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

