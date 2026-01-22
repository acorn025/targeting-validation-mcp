from fastmcp import FastMCP
import re

app = FastMCP("Ad Targeting Assistant")

# --- [사전] 1. 검증용 연령 제한 키워드 (Hard Rules) ---
AGE_SENSITIVE_DICT = {
    "YOUTH": {
        "keywords": ["청년", "도약", "희망", "내일채움", "군인", "대학생", "신입", "사회초년생"],
        "limit": 34,
        "msg": "청년 대상 상품은 보통 만 34세 이하가 기준입니다."
    },
    "SILVER": {
        "keywords": ["시니어", "실버", "연금", "은퇴", "퇴직", "노후", "노인", "복지", "요양", "기초연금", "고령"],
        "min_age": 60,
        "msg": "노인/시니어 정책은 보통 만 60~65세 이상이 수혜 대상입니다."
    },
    "KIDS": {
        "keywords": ["어린이", "키즈", "아동", "청소년", "수험생", "초등", "중고생", "영유아"],
        "limit": 18,
        "msg": "아동/청소년 상품은 만 18세 이하가 기준입니다."
    }
}

# --- [사전] 2. 특정 상품 페르소나 DB (고정 데이터) ---
PERSONA_DB = {
    "저가 햄버거": {
        "definition": "가성비와 효율 중심의 식문화를 선호하는 집단",
        "age_trend": "10대 후반 ~ 20대(학생), 30대(직장인 가성비 점심)",
        "lifestyle": "배달 앱 헤비 유저, 혼밥 선호, 가격 민감도 높음",
        "hints": ["편의점", "저가 커피", "자취/1인 가구"]
    },
    "청년도약계좌": {
        "definition": "목돈 마련과 자산 형성에 관심이 높은 사회초년생",
        "age_trend": "만 19세 ~ 34세 (청년층 집중)",
        "lifestyle": "재테크 관심, 저축 지향, 정부 혜택 민감",
        "hints": ["적금", "청약", "재테크", "급여 관리"]
    }
}

@app.tool()
def validate_or_analyze_targeting(
    interests: list,
    age_range: str = None,
    region: str = None,
    gender: str = "성별무관",
    product_constraint: str = None
) -> dict:
    """
    관심사만 입력하면 AI가 페르소나를 즉석 분석하고, 정보가 모두 있으면 정책 적합성을 검증합니다.
    """
    
    # --- [Mode A] 페르소나 분석 모드 (나이/지역 정보가 없을 때) ---
    if not age_range or age_range.strip() == "":
        analysis_results = []
        for interest in interests:
            # 1. DB 확인
            data = PERSONA_DB.get(interest)
            
            # 2. DB에 없으면 AI가 자신의 지식으로 채우도록 가이드 반환
            if not data:
                data = {
                    "definition": f"AI 분석 요망: {interest}를 즐기는 핵심 소비자층의 정의",
                    "age_trend": f"AI 분석 요망: {interest}와 가장 연관성이 높은 연령대와 성별 경향",
                    "lifestyle": f"AI 분석 요망: {interest} 관심자의 전형적인 소비 패턴 및 라이프스타일",
                    "hints": [f"{interest}와 함께 타겟팅하면 좋은 연관 관심사 키워드들"]
                }
            analysis_results.append({"interest": interest, "analysis": data})

        return {
            "status": "SUCCESS",
            "mode": "PERSONA_ANALYSIS",
            "message": "입력하신 관심사를 바탕으로 분석한 소비자 페르소나입니다.",
            "results": analysis_results,
            "disclaimer": "본 분석은 AI의 학습 데이터를 바탕으로 한 일반적 경향성(Persona)이며, 실제 가입 자격이나 정책 적합성은 반드시 확인이 필요합니다."
        }

    # --- [Mode B] 타겟팅 검증 모드 (기존 정밀 로직) ---
    warnings = []
    logic_errors = []
    
    # 1. 입력값 정규화
    gender_map = {"남": "MALE", "여": "FEMALE", "M": "MALE", "F": "FEMALE"}
    normalized_gender = gender.upper()
    for k, v in gender_map.items():
        if k in normalized_gender:
            normalized_gender = v
            break
    if normalized_gender not in ["MALE", "FEMALE"]: normalized_gender = "ALL"

    if not region:
        return {"success": False, "error": "검증 모드에서는 지역(region) 정보가 필수입니다."}

    # 2. 연령대 파싱
    age_numbers = [0, 100]
    extracted_ages = [int(num) for num in re.findall(r'\d+', age_range)]
    if "이상" in age_range and extracted_ages: age_numbers = [extracted_ages[0], 100]
    elif "이하" in age_range and extracted_ages: age_numbers = [0, extracted_ages[0]]
    elif "대" in age_range and extracted_ages: age_numbers = [extracted_ages[0], extracted_ages[0] + 9]
    elif len(extracted_ages) >= 2: age_numbers = [min(extracted_ages), max(extracted_ages)]
    elif len(extracted_ages) == 1: age_numbers = [extracted_ages[0], extracted_ages[0]]

    # 3. 범용 키워드 기반 논리적 상충 검증
    if not product_constraint:
        for interest in interests:
            upper_i = interest.upper()
            for cat, info in AGE_SENSITIVE_DICT.items():
                if any(k in upper_i for k in info["keywords"]):
                    if "min_age" in info and age_numbers[1] < info["min_age"]:
                        logic_errors.append(f"대상자 불일치: '{interest}' 수혜 대상은 {info['msg']}")
                    if "limit" in info and age_numbers[0] > info["limit"]:
                        logic_errors.append(f"가입 자격 미달: '{interest}' 가입 조건은 {info['msg']}")
    else:
        constraint_ages = [int(num) for num in re.findall(r'\d+', product_constraint)]
        if constraint_ages:
            max_limit = max(constraint_ages)
            if age_numbers[0] > max_limit:
                logic_errors.append(f"명시적 나이 제한 불일치: 상품 제한(만 {max_limit}세)보다 타겟 연령이 높습니다.")

    # 4. 지역 정밀 검증
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

    # 5. 정책 위반 검증
    is_minor = age_numbers[0] <= 19 or age_numbers[1] <= 19
    forbidden_categories = {
        "주류": ["술", "음주", "주류", "소주", "맥주"],
        "약물": ["마약", "DRUGS", "대마"],
        "성인/사행성": ["ADULT", "성인", "도박", "유흥"]
    }
    for cat, ks in forbidden_categories.items():
        if any(k in i.upper() for i in interests for k in ks):
            if is_minor: logic_errors.append(f"정책 위반: 미성년자 대상 {cat} 관련 타켓팅 금지")
            else: warnings.append(f"민감 카테고리 알림: {cat} 관련 가이드라인 확인 필요")

    # 6. 응답 구성
    all_warnings = list(set(warnings + logic_errors))
    status = "오류" if logic_errors else ("주의" if warnings else "정상")
    final_message = "타겟팅 조합에 논리적 모순이 발견되었습니다." if logic_errors else ("타겟팅 설정 시 주의가 필요한 항목이 있습니다." if warnings else "타겟팅 조합 검증 완료")

    return {
        "status": status,
        "mode": "TARGET_VALIDATION",
        "normalized_target": {
            "age_range": f"만 {age_numbers[0]}-{age_numbers[1]}세",
            "gender": normalized_gender,
            "region": region_input,
            "interests": [i.upper() for i in interests]
        },
        "warnings": all_warnings,
        "message": final_message,
        "reasoning": "연령대 정합성, 지역 일치성, 광고 정책 준수 여부를 종합 검토했습니다."
    }

if __name__ == "__main__":
    app.run()
