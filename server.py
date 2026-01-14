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
    광고 타겟 설정의 유효성을 검사하고 데이터 표준화를 수행합니다.
    """
    warnings = []
    
    # 1. 입력값 정규화 (자연어 입력 대응)
    # 성별: '남성', '남자', 'male' 등 대응
    gender_map = {"남": "MALE", "여": "FEMALE", "M": "MALE", "F": "FEMALE"}
    normalized_gender = gender.upper()
    for k, v in gender_map.items():
        if k in normalized_gender:
            normalized_gender = v
            break
    if normalized_gender not in ["MALE", "FEMALE"]:
        normalized_gender = "ALL"

    # 지역: '서울시', 'seoul' 등 대응
    region_upper = region.upper().replace(" ", "").replace("시", "").replace("도", "")

    # 2. 연령대 파싱 로직 강화 (정규표현식 사용)
    age_numbers = [0, 100] # 기본값: 전연령
    try:
        # 숫자만 추출 (예: "20-30대" -> [20, 30])
        extracted_ages = re.findall(r'\d+', age_range)
        if len(extracted_ages) >= 2:
            age_numbers = [int(extracted_ages[0]), int(extracted_ages[1])]
        elif len(extracted_ages) == 1:
            age_numbers = [int(extracted_ages[0]), int(extracted_ages[0])]
    except Exception:
        pass # 파싱 실패 시 기본값(0-100) 유지

    # 3. 검증 로직 (실패 조건)
    if not interests or not region:
        return {
            "success": False,
            "error": "관심사와 지역 정보는 필수입니다."
        }

    # 4. 경고 조건 (정책 및 정합성)
    # 미성년자 및 민감 관심사
    sensitive_interests = ["ADULT", "ALCOHOL", "DRUGS", "술", "성인", "도박"]
    is_minor = age_numbers[0] <= 19 or age_numbers[1] <= 19
    has_sensitive = any(si in i.upper() for i in interests for si in sensitive_interests)
    
    if is_minor and has_sensitive:
        warnings.append("미성년자 타겟팅에 부적절한 키워드가 포함되어 있습니다.")
    elif has_sensitive:
        warnings.append("민감한 관심사 키워드가 포함되어 있어 플랫폼 심사가 엄격할 수 있습니다.")

    # 지역-관심사 불일치 (예: 서울 거주자에게 제주도 맛집 광고)
    for interest in interests:
        for reg_key in ["SEOUL", "BUSAN", "JEJU", "DAEGU", "INCHEON"]:
            if reg_key in interest.upper() and reg_key != region_upper:
                warnings.append(f"타겟 지역({region_upper})과 관심사 키워드({interest})가 일치하지 않습니다.")

    # 5. 응답 구성
    response = {
        "normalized_target": {
            "age_range": f"{age_numbers[0]}-{age_numbers[1]}",
            "gender": normalized_gender,
            "interests": [i.upper() for i in interests],
            "region": region_upper
        }
    }

    if warnings:
        response["warnings"] = list(set(warnings)) # 중복 제거
        response["status"] = "주의"
        response["message"] = "설정된 타겟 조합에 보충 가이드가 있습니다."
    else:
        response["status"] = "정상"
        response["message"] = "타겟 설정이 논리적으로 유효합니다."

    return response

if __name__ == "__main__":
    app.run()
