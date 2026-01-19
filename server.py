from fastmcp import FastMCP
import re

app = FastMCP("Ad Targeting Assistant")

@app.tool()
def validate_targeting_conditions(
    age_range: str,
    gender: str,
    interests: list,
    region: str,
    product_constraint: str = None  # 대화 중 추가된 상품 제약 조건 (만 나이 기준 등)
) -> dict:
    """
    광고 타겟 설정의 데이터 정규화, 지역/연령 정합성 및 정책 준수를 통합 검증합니다.
    논리적 모순이 의심될 경우 사용자에게 추가 정보를 요청하며, '만 나이'를 기준으로 정밀 검증합니다.
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

    # --- 3. 연령대 파싱 (Age Parsing - 만 나이 기준) ---
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

    # --- 4. 논리적 의심 및 되묻기 로직 (만 나이 검증 포함) ---
    age_sensitive_keywords = ["청년", "도약계좌", "희망적금", "지원금", "실버", "아동", "연금", "주택청약", "대출"]
    
    # (A) 상품 제약 조건이 아직 없을 때: 의심 구간 탐색
    if not product_constraint:
        for interest in interests:
            upper_interest = interest.upper()
            if any(k in upper_interest for k in age_sensitive_keywords):
                # 논리적 의심: '청년' 키워드인데 타겟이 만 35세 이상인 경우 등
                if ("청년" in upper_interest or "도약" in upper_interest) and age_numbers[0] >= 35:
                    return {
                        "success": True,
                        "status": "추가 정보 필요",
                        "message": f"관심사 '{interest}'는 만 나이 기준의 가입 제한이 있을 가능성이 높습니다. 상품의 '만 나이 제한(예: 만 34세까지)'을 알려주시면 정확한 검증이 가능합니다.",
                        "reasoning": "설정된 타겟 연령과 상품의 일반적인 수혜 연령이 일치하지 않아 사용자 확인이 필요합니다."
                    }
    
    # (B) 사용자가 제약 조건을 준 경우: 만 나이 정밀 대조
    else:
        constraint_ages = [int(num) for num in re.findall(r'\d+', product_constraint)]
        if constraint_ages:
            max_limit = max(constraint_ages)
            if age_numbers[0] > max_limit:
                warnings.append(f"만 나이 불일치: 상품 가입 제한(만 {max_limit}세)이 설정된 타겟팅 시작 연령(만 {age_numbers[0]}세)보다 낮아 광고 효율이 없습니다.")

    # --- 5. 지역 정밀 검증 로직 (Geo-Validation) ---
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

    # --- 6. 정책 및 정합성 검증 (Policy & Keywords) ---
    # (1) 지역명-관심사 키워드 불일치 체크
    for interest in interests:
        upper_interest = interest.upper()
        for p in PROVINCES:
            if p[:2] in upper_interest and (not province_found or p[:2] not in province_found):
                warnings.append(f"정합성 주의: 관심사({interest})와 설정 지역({region_input})이 일치하지 않습니다.")

    # (2) 민감 카테고리 및 미성년자 보호 체크
    is_minor = age_numbers[0] <= 19 or age_numbers[1] <= 19
    forbidden_categories = {
        "주류": ["술", "음주", "주류", "ALCOHOL", "BEER", "WINE", "WHISKY", "위스키", "소주", "맥주", "진로", "참이슬"],
        "약물": ["마약", "DRUGS", "약물", "환각", "대마", "CANNABIS", "필로폰"],
        "성인/사행성": ["ADULT", "성인", "도박", "CASINO", "GAMBLING", "유흥", "경마"]
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
            warnings.append(f"정책 위반: 만 19세 미만 미성년자 대상 {', '.join(detected_categories)} 관련 타겟팅은 법적으로 금지됩니다.")
        else:
            warnings.append(f"민감 카테고리 주의: '{', '.join(detected_categories)}' 관련 키워드가 포함되어 있어 플랫폼별 가이드라인 확인이 필요합니다.")

    # --- 7. 응답 구성 ---
    status = "정상"
    if any("불일치" in w or "위반" in w for w in warnings):
        status = "오류"
    elif warnings:
        status = "주의"

    return {
        "normalized_target": {
            "age_range": f"만 {age_numbers[0]}-{age_numbers[1]}세",
            "gender": normalized_gender,
            "region": region_input,
            "interests": [i.upper() for i in interests]
        },
        "status": status,
        "warnings": list(set(warnings)),
        "message": "타겟 설정이 논리적으로 유효합니다." if status == "정상" else "타겟 설정에 정합성 오류 또는 주의 사항이 있습니다.",
        "reasoning": f"만 나이 정합성 검토, 지역 일치성 분석, {len(detected_categories)}개의 민감 카테고리 정책 검증을 완료했습니다."
    }

if __name__ == "__main__":
    app.run()
