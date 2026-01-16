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
    광고 타겟 설정의 데이터 정규화, 지역/연령 정합성 및 정책 준수를 통합 검증합니다.
    """
    warnings = []
    
    # --- 1. 입력값 정규화 (Normalization) ---
    gender_map = {"남": "MALE", "여": "FEMALE", "M": "MALE", "F": "FEMALE"}
    normalized_gender = gender.upper()
    for k, v in gender_map.items():
        if k in normalized_gender:
            normalized_gender = v
            break
    if normalized_gender not in ["MALE", "FEMALE"]:
        normalized_gender = "ALL"

    # --- 2. 필수값 검증 (Validation) ---
    if not interests or not region:
        return {
            "success": False,
            "error": "필수 타겟팅 정보(관심사 또는 지역)가 누락되었습니다."
        }

    # --- 3. 지역 정밀 검증 로직 (Geo-Validation) ---
    PROVINCES = ["서울특별시", "부산광역시", "대구광역시", "인천광역시", "광주광역시", "대전광역시", "울산광역시", "세종특별자치시", "경기도", "강원도", "충청북도", "충청남도", "전라북도", "전라남도", "경상북도", "경상남도", "제주특별자치도"]
    region_db = {
        "서울특별시": ["강남구", "서초구", "송파구", "종로구", "마포구"],
        "경기도": ["수원시", "용인시", "성남시", "고양시", "화성시", "안양시"],
        "경상북도": ["포항시", "구미시", "경주시", "상주시", "안동시"],
        "경상남도": ["창원시", "김해시", "양산시", "진주시"],
        "부산광역시": ["해운대구", "부산진구", "동래구"],
        "제주특별자치도": ["제주시", "서귀포시"]
    }

    region_input = region.strip()
    province_found = next((p for p in PROVINCES if p[:2] in region_input), None)

    if province_found and province_found in region_db:
        matched_city = any(c[:2] in region_input for c in region_db[province_found])
        if not matched_city:
            for other_p, other_cities in region_db.items():
                for c in other_cities:
                    if c[:2] in region_input:
                        warnings.append(f"지역 불일치: '{region_input}'은(는) 잘못된 조합입니다. '{c}'는 '{other_p}' 소속입니다.")
                        break

    # --- 4. 연령대 파싱 (Age Parsing) ---
    age_numbers = [0, 100]
    extracted_ages = [int(num) for num in re.findall(r'\d+', age_range)]
    if "이상" in age_range and extracted_ages:
        age_numbers = [extracted_ages[0], 100]
    elif "이하" in age_range and extracted_ages:
        age_numbers = [0, extracted_ages[0]]
    elif "대" in age_range and extracted_ages:
        age_numbers = [extracted_ages[0], extracted_ages[0] + 9]
    elif len(extracted_ages) >= 2:
        age_numbers = [min(extracted_ages), max(extracted_ages)]
    elif len(extracted_ages) == 1:
        age_numbers = [extracted_ages[0], extracted_ages[0]]

    # --- 5. 정책 및 정합성 검증 (Policy & Keywords) ---
    # (1) 지역명-관심사 키워드 불일치 체크
    for interest in interests:
        for p in PROVINCES:
            if p[:2] in interest.upper() and (not province_found or p[:2] not in province_found):
                warnings.append(f"정합성 주의: 관심사({interest})와 설정 지역({region_input})이 일치하지 않습니다.")

    # (2) 민감 카테고리 및 미성년자 보호 체크 (카테고리 기반 개선)
    is_minor = age_numbers[0] <= 19 or age_numbers[1] <= 19
    
    # 금칙어 카테고리 맵핑
    forbidden_categories = {
        "주류": ["술", "음주", "주류", "ALCOHOL", "BEER", "WINE", "WHISKY", "위스키", "소주", "맥주", "진로", "참이슬"],
        "약물": ["마약", "DRUGS", "약물", "환각", "대마", "CANNABIS", "필로폰"],
        "성인/사행성": ["ADULT", "성인", "도박", "CASINO", "GAMBLING", "유흥"]
    }
    
    detected_categories = []
    for interest in interests:
        upper_interest = interest.upper()
        for category, keywords in forbidden_categories.items():
            if any(k in upper_interest for k in keywords):
                detected_categories.append(category)

    detected_categories = list(set(detected_categories))

    if detected_categories:
        if is_minor:
            # 미성년자 관련 위반 시 status를 '오류'로 만들기 위한 문구
            warnings.append(f"위반: 미성년자 대상 {', '.join(detected_categories)} 관련 타겟팅은 법적으로 금지됩니다.")
        else:
            # 요청하신 중립적인 문구로 적용
            warnings.append(f"민감한 카테고리({', '.join(detected_categories)})가 포함되어 있습니다.")

    # --- 6. 응답 구성 ---
    status = "정상"
    # '위반' 또는 '불일치'가 포함된 경우 status를 '오류'로 격상
    if any("위반" in w or "불일치" in w for w in warnings):
        status = "오류"
    elif warnings:
        status = "주의"

    return {
        "normalized_target": {
            "age_range": f"{age_numbers[0]}-{age_numbers[1]}",
            "gender": normalized_gender,
            "region": region_input,
            "interests": [i.upper() for i in interests]
        },
        "status": status,
        "warnings": list(set(warnings)),
        "message": "타겟 설정에 정책 검토가 필요합니다." if status in ["오류", "주의"] else "타겟 설정이 논리적으로 유효합니다.",
        "reasoning": f"성별/지역/연령 데이터를 표준화하고 {len(PROVINCES)}개 광역지자체 기반 정합성 검토를 완료했습니다."
    }

if __name__ == "__main__":
    app.run()
