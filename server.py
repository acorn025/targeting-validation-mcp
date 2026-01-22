from fastmcp import FastMCP
import re

app = FastMCP("Ad Targeting Assistant")

# --- [수정] 범용 나이 제한 키워드 사전 및 기준 강화 ---
AGE_SENSITIVE_DICT = {
    "YOUTH": {
        "keywords": ["청년", "도약", "희망", "내일채움", "군인", "대학생", "신입", "YOUTH", "첫차", "사회초년생"],
        "limit": 34,
        "msg": "청년/신입 대상 상품은 보통 만 34세 이하가 가입 기준입니다."
    },
    "SILVER": {
        "keywords": ["시니어", "실버", "연금", "은퇴", "퇴직", "노후", "보청기", "노인", "복지", "요양", "기초연금", "고령"],
        "min_age": 60,
        "msg": "노인/시니어 관련 정책 및 상품은 보통 만 60~65세 이상이 수혜 대상입니다."
    },
    "KIDS": {
        "keywords": ["어린이", "키즈", "아동", "청소년", "수험생", "초등", "중고생", "영유아"],
        "limit": 18,
        "msg": "아동/청소년 대상 상품은 만 18세 이하가 기준입니다."
    }
}

@app.tool()
def validate_targeting_conditions(
    age_range: str,
    gender: str,
    interests: list,
    region: str,
    product_constraint: str = None
) -> dict:
    warnings = []
    logic_errors = []
    
    # --- 1. 입력값 정규화 ---
    gender_map = {"남": "MALE", "여": "FEMALE", "M": "MALE", "F": "FEMALE"}
    normalized_gender = gender.upper()
    for k, v in gender_map.items():
        if k in normalized_gender:
            normalized_gender = v
            break
    if normalized_gender not in ["MALE", "FEMALE"]: normalized_gender = "ALL"

    # --- 2. 필수값 검증 ---
    if not interests or not region:
        return {"success": False, "error": "필수 타겟팅 정보가 누락되었습니다."}

    # --- 3. 연령대 파싱 ---
    age_numbers = [0, 100]
    extracted_ages = [int(num) for num in re.findall(r'\d+', age_range)]
    if "이상" in age_range and extracted_ages: age_numbers = [extracted_ages[0], 100]
    elif "이하" in age_range and extracted_ages: age_numbers = [0, extracted_ages[0]]
    elif "대" in age_range and extracted_ages: age_numbers = [extracted_ages[0], extracted_ages[0] + 9]
    elif len(extracted_ages) >= 2: age_numbers = [min(extracted_ages), max(extracted_ages)]
    elif len(extracted_ages) == 1: age_numbers = [extracted_ages[0], extracted_ages[0]]

    # --- 4. [보완] 범용 키워드 기반 논리적 상충 검증 ---
    # 사용자가 직접 제약 조건을 주지 않았더라도 '통념적 기준'으로 1차 필터링
    if not product_constraint:
        for interest in interests:
            upper_i = interest.upper()
            for cat, info in AGE_SENSITIVE_DICT.items():
                if any(k in upper_i for k in info["keywords"]):
                    # 실버 상품인데 설정 연령이 너무 낮을 때 (예: 20대 노인복지)
                    if "min_age" in info and age_numbers[1] < info["min_age"]:
                        logic_errors.append(f"대상자 불일치: '{interest}' 수혜 대상은 {info['msg']} (현재 설정: 최대 {age_numbers[1]}세)")
                    
                    # 청년/아동 상품인데 설정 연령이 너무 높을 때 (예: 40대 청년계좌)
                    if "limit" in info and age_numbers[0] > info["limit"]:
                        logic_errors.append(f"가입 자격 미달: '{interest}' 가입 조건은 {info['msg']} (현재 설정: 최소 {age_numbers[0]}세)")
    else:
        # 사용자가 수동으로 제약 조건을 준 경우 (예: "만 34세까지") 정밀 대조
        constraint_ages = [int(num) for num in re.findall(r'\d+', product_constraint)]
        if constraint_ages:
            max_limit = max(constraint_ages)
            if age_numbers[0] > max_limit:
                logic_errors.append(f"명시적 나이 제한 불일치: 상품 제한(만 {max_limit}세)보다 타겟 연령(만 {age_numbers[0]}세)이 높습니다.")

    # --- 5. 지역 및 정책 검증 (기존 로직 유지 및 보완) ---
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
        if not any(c[:2] in region_input for c in region_db[province_found]):
            for p, cities in region_db.items():
                if any(c[:2] in region_input for c in cities):
                    warnings.append(f"지역 불일치 주의: '{region_input}'은(는) {p} 소속입니다.")

    # --- 6. 정책 위반 검증 ---
    is_minor = age_numbers[0] <= 19 or age_numbers[1] <= 19
    forbidden_categories = {
        "주류": ["술", "음주", "주류", "ALCOHOL", "BEER", "WINE", "소주", "맥주"],
        "약물": ["마약", "DRUGS", "약물", "환각", "대마"],
        "성인/사행성": ["ADULT", "성인", "도박", "CASINO", "GAMBLING", "유흥"]
    }
    
    for cat, ks in forbidden_categories.items():
        if any(k in i.upper() for i in interests for k in ks):
            if is_minor: logic_errors.append(f"정책 위반: 미성년자 대상 {cat} 관련 타겟팅은 법적으로 금지됩니다.")
            else: warnings.append(f"민감 카테고리 알림: {cat} 관련 광고는 플랫폼별 가이드라인 확인이 필요합니다.")

    # --- 7. 응답 구성 (논리 오류와 경고 구분) ---
    all_warnings = list(set(warnings + logic_errors))
    
    if logic_errors:
        status = "오류"
        message = "타겟팅 조합에 심각한 논리적 모순이 발견되었습니다."
    elif warnings:
        status = "주의"
        message = "타겟팅 설정 시 주의가 필요한 항목이 있습니다."
    else:
        status = "정상"
        message = "타겟팅 조합이 논리적으로 적합합니다."

    return {
        "normalized_target": {
            "age_range": f"만 {age_numbers[0]}-{age_numbers[1]}세",
            "gender": normalized_gender,
            "region": region_input,
            "interests": [i.upper() for i in interests]
        },
        "status": status,
        "warnings": all_warnings,
        "message": message,
        "reasoning": f"입력된 관심사 키워드와 연령대의 생애주기 정합성 및 법적 정책 준수 여부를 검증했습니다."
    }

if __name__ == "__main__":
    app.run()
