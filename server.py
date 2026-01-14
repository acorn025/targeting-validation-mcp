from fastmcp import FastMCP
import re

app = FastMCP("Ad Targeting Assistant")

@app.tool()
def validate_targeting_conditions(
    age_range: str,
    gender: str,
    interests: list,
    region: str
) -> dict:
    """
    광고 타겟 설정의 데이터 정규화 및 설정 오류를 검증합니다.
    """
    warnings = []
    
    # 1. 입력값 정규화 (Normalization)
    gender_map = {"남": "MALE", "여": "FEMALE", "M": "MALE", "F": "FEMALE"}
    normalized_gender = gender.upper()
    for k, v in gender_map.items():
        if k in normalized_gender:
            normalized_gender = v
            break
    if normalized_gender not in ["MALE", "FEMALE"]:
        normalized_gender = "ALL"

    region_upper = region.upper().replace(" ", "").replace("시", "").replace("도", "")

    # 2. 연령대 파싱 로직 개선 (범위 인식)
    age_numbers = [0, 100]
    try:
        extracted_ages = re.findall(r'\d+', age_range)
        if len(extracted_ages) >= 2:
            # "20-30" -> [20, 30]
            age_numbers = [int(extracted_ages[0]), int(extracted_ages[1])]
        elif len(extracted_ages) == 1:
            age_val = int(extracted_ages[0])
            if "대" in age_range:
                # "20대" -> [20, 29]
                age_numbers = [age_val, age_val + 9]
            else:
                # "20세" -> [20, 20]
                age_numbers = [age_val, age_val]
    except Exception:
        pass

    # 3. 필수값 검증
    if not interests or not region:
        return {
            "success": False,
            "error": "필수 타겟팅 정보(관심사 또는 지역)가 누락되었습니다."
        }

    # 4. 정합성 및 키워드 검증
    sensitive_keywords = ["ADULT", "ALCOHOL", "DRUGS", "술", "성인", "도박", "진로", "참이슬"]
    is_minor = age_numbers[0] <= 19 or age_numbers[1] <= 19
    has_sensitive = any(sk in i.upper() for i in interests for sk in sensitive_keywords)
    
    if is_minor and has_sensitive:
        warnings.append("미성년자 타겟팅에 민감한 관심사 키워드가 포함되어 있습니다.")
    elif has_sensitive:
        warnings.append("민감한 관심사 키워드가 포함되어 있습니다.")

    major_regions = ["SEOUL", "BUSAN", "JEJU", "DAEGU", "INCHEON", "GYEONGGI", "GUMI"]
    for interest in interests:
        for reg_key in major_regions:
            if reg_key in interest.upper() and reg_key != region_upper:
                warnings.append(f"설정 지역({region_upper})과 관심사 키워드({interest}) 간의 지역 정보가 일치하지 않습니다.")

    # 5. 응답 구성
    response = {
        "normalized_target": {
            "age_range": f"{age_numbers[0]}-{age_numbers[1]}",
            "gender": normalized_gender,
            "interests": [i.upper() for i in interests],
            "region": region_upper
        },
        "status": "주의" if warnings else "정상",
        "message": "설정된 타겟 조합에 보충 가이드가 있습니다." if warnings else "타겟 설정이 논리적으로 유효합니다."
    }

    if warnings:
        response["warnings"] = list(set(warnings))

    return response

if __name__ == "__main__":
    app.run()
