from fastmcp import FastMCP
import re

app = FastMCP("Ad Targeting Assistant")

# --- [추가] 범용 나이 제한 키워드 사전 ---
AGE_SENSITIVE_DICT = {
    "YOUTH": {
        "keywords": ["청년", "도약", "희망", "내일채움", "군인", "대학생", "신입", "YOUTH", "첫차"],
        "limit": 34,
        "msg": "청년/신입 대상 상품은 보통 만 34세 이하가 기준입니다."
    },
    "SILVER": {
        "keywords": ["시니어", "실버", "연금", "은퇴", "퇴직", "노후", "보청기"],
        "min_age": 55,
        "msg": "시니어 관련 상품은 보통 만 55세 이상이 기준입니다."
    },
    "KIDS": {
        "keywords": ["어린이", "키즈", "아동", "청소년", "수험생", "초등", "중고생"],
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

    # --- 4. [보완] 범용 키워드 기반 다시 물어보기 로직 ---
    if not product_constraint:
        for interest in interests:
            upper_i = interest.upper()
            for cat, info in AGE_SENSITIVE_DICT.items():
                if any(k in upper_i for k in info["keywords"]):
                    # 청년/아동 카테고리인데 설정 연령이 높을 때
                    if "limit" in info and age_numbers[0] > info["limit"]:
                        return {
                            "success": True,
                            "status": "다시 확인 필요",
                            "message": f"잠깐만요! 관심사 '{interest}'는 {info['msg']}",
                            "question": f"현재 설정하신 타겟(만 {age_numbers[0]}세)이 기준을 초과합니다. 실제 만 나이 제한은 몇 세인가요?",
                            "reasoning": "상품 특성과 타겟 연령의 논리적 불일치 감지."
                        }
                    # 실버 카테고리인데 설정 연령이 낮을 때
                    if "min_age" in info and age_numbers[1] < info["min_age"]:
                        return {
                            "success": True,
                            "status": "다시 확인 필요",
                            "message": f"관심사 '{interest}'는 {info['msg']}",
                            "question": f"현재 설정하신 타겟(최대 만 {age_numbers[1]}세)이 너무 낮습니다. 확인이 필요합니다.",
                            "reasoning": "실버 상품 타겟팅 연령 미달."
                        }
    else:
        # 사용자가 제약 조건을 준 경우 정밀 대조
        constraint_ages = [int(num) for num in re.findall(r'\d+', product_constraint)]
        if constraint_ages:
            max_limit = max(constraint_ages)
            if age_numbers[0] > max_limit:
                warnings.append(f"만 나이 불일치: 상품 제한(만 {max_limit}세)보다 타겟 연령(만 {age_numbers[0]}세)이 높습니다.")

    # --- 5. 지역 정밀 검증 (기존 로직 유지) ---
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
                    warnings.append(f"지역 불일치: '{region_input}'은(는) {p} 소속입니다.")

    # --- 6. 정책 및 정합성 검증 (기존 로직 유지) ---
    for interest in interests:
        upper_interest = interest.upper()
        for p in PROVINCES:
            if p[:2] in upper_interest and (not province_found or p[:2] not in province_found):
                warnings.append(f"정합성 주의: 관심사({interest})와 설정 지역({region_input})이 불일치합니다.")

    is_minor = age_numbers[0] <= 19 or age_numbers[1] <= 19
    forbidden_categories = {
        "주류": ["술", "음주", "주류", "ALCOHOL", "BEER", "WINE", "소주", "맥주"],
        "약물": ["마약", "DRUGS", "약물", "환각", "대마"],
        "성인/사행성": ["ADULT", "성인", "도박", "CASINO", "GAMBLING", "유흥"]
    }
    detected_categories = [cat for cat, ks in forbidden_categories.items() if any(k in i.upper() for i in interests for k in ks)]

    if detected_categories:
        if is_minor: warnings.append(f"정책 위반: 미성년자 대상 {detected_categories} 광고 금지")
        else: warnings.append(f"민감 카테고리 주의: {detected_categories} 가이드라인 확인 필요")

    # --- 7. 응답 구성 ---
    status = "정상"
    if any("불일치" in w or "위반" in w for w in warnings): status = "오류"
    elif warnings: status = "주의"

    return {
        "normalized_target": {
            "age_range": f"만 {age_numbers[0]}-{age_numbers[1]}세",
            "gender": normalized_gender,
            "region": region_input,
            "interests": [i.upper() for i in interests]
        },
        "status": status,
        "warnings": list(set(warnings)),
        "message": "검증 완료. 정합성을 확인하세요.",
        "reasoning": f"범용 키워드 사전 대조, 지역 불일치 분석, 정책 검증을 모두 수행했습니다."
    }

if __name__ == "__main__":
    app.run()
