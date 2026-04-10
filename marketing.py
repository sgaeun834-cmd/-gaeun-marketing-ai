import streamlit as st
import google.generativeai as genai
import pandas as pd
from io import BytesIO
import time

# 1. 전문가용 UI 스타일 (고퀄리티 디자인 유지)
st.set_page_config(page_title="AD Strategy Pro | 통합 가이드", layout="wide")

st.markdown("""
    <style>
    .report-card { 
        background-color: #ffffff; padding: 25px 35px; border-radius: 15px; 
        box-shadow: 0 10px 30px rgba(0,0,0,0.05); border-top: 6px solid #FF4B4B; 
        color: #1E1E1E; line-height: 1.7; margin-bottom: 20px; font-size: 15px;
    }
    .report-card h3 { color: #FF4B4B; font-weight: 800; margin-top: 15px; margin-bottom: 10px; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: 700; }
    .stButton>button { 
        background: #1E1E1E; color: white; font-weight: bold; border-radius: 8px; height: 3.8em; width: 100%;
    }
    .stButton>button:hover { background: #FF4B4B; }
    </style>
    """, unsafe_allow_html=True)

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='전문실무가이드')
    writer.close()
    return output.getvalue()

# 2. 사이드바 정보 입력
with st.sidebar:
    st.header("📋 캠페인 기본 정보")
    api_key = st.text_input("Gemini API Key", type="password")
    st.divider()
    keyword = st.text_input("📍 분석 키워드", "가발")
    target = st.text_input("🎯 핵심 타겟", "20대-40대 여성")
    budget = st.text_input("💰 매체 총 예산", "800만원")

st.title("🚀 AD Strategy & Execution Guide")

# 3. 실행 로직
if st.button("📊 전문 광고 실행 가이드 생성 시작"):
    if not api_key:
        st.error("사이드바에 API 키를 입력해 주세요.")
    else:
        try:
            genai.configure(api_key=api_key)
            
            # [404 에러 원천 차단] 텍스트 입력 대신 시스템에서 사용 가능한 모델 리스트를 직접 조회
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            # 1. 2.5를 배제한 1.5-flash 찾기
            # 2. 못 찾으면 1.5-pro 찾기
            # 3. 그것도 없으면 그냥 1.5가 들어간 첫 번째 모델 쓰기
            target_model = next((m for m in available_models if "1.5-flash" in m and "2.5" not in m),
                                next((m for m in available_models if "1.5-pro" in m), 
                                     next((m for m in available_models if "1.5" in m), available_models[0])))
            
            model = genai.GenerativeModel(target_model)
            
            with st.spinner(f'실시간 매칭된 최적 모델({target_model})로 전략 수립 중...'):
                prompt = f"""
                너는 15년 차 퍼포먼스 마케팅 디렉터야. {keyword}, {target}, {budget} 기반의 광고 제안서 및 실무 가이드를 작성해.
                각 섹션 사이에는 반드시 [SECTION_DELIMITER] 를 넣어주고, 인사말은 절대 하지마.

                섹션 1: 광고 예산안 및 매체 믹스
                - 추천 매체(파워링크, 쇼핑검색, 카탈로그, 메타, 구글, 모비온 등) 제안 사유와 {budget}에 대한 상세 예산 분배안(%) 및 예상 ROAS.
                [SECTION_DELIMITER]
                섹션 2: 경쟁사 및 시장 분석
                - {keyword} 주요 경쟁사 실명 언급 및 핵심 소구점 분석. 자사 필승 USP 도출.
                [SECTION_DELIMITER]
                섹션 3: 파워링크 세팅 가이드
                - 소비자 심리 퍼널에 따른 키워드 그룹핑 전략 및 제목(15자)/설명(45자) 조합 소재 5세트.
                [SECTION_DELIMITER]
                섹션 4: 쇼핑검색 광고 최적화
                - 분리 운영 팁(요일/매체/시간)과 데이터 기반 효율 증대 근거. 메인/중소형 키워드 리스트.
                [SECTION_DELIMITER]
                섹션 5: 매체별 광고 카피 및 크리에이티브
                - SNS 채널별 후킹 가이드 및 즉시 라이브 가능한 텍스트 카피.
                [SECTION_DELIMITER]
                섹션 6: 광고 운영 이슈 및 리스크 관리
                - 성수기/비수기 대응 시나리오 및 광고 정책 이슈 점검.
                """
                
                # 실행 및 429(할당량) 자동 대응
                try:
                    response = model.generate_content(prompt)
                except Exception as e:
                    if "429" in str(e):
                        st.info("💡 할당량 회복을 위해 10초만 대기합니다...")
                        time.sleep(12)
                        response = model.generate_content(prompt)
                    else: raise e

                if response:
                    contents = response.text.split("[SECTION_DELIMITER]")
                    final_contents = [c.strip() for c in contents if c.strip()][:6]
                    while len(final_contents) < 6: final_contents.append("내용 생성 중...")

                    tab_titles = ["💰 예산안", "📊 경쟁사분석", "🔍 파워링크", "🛒 쇼핑검색", "✏️ 카피", "⚠️ 이슈관리"]
                    st.success("실무 가이드 수립 완료!")
                    
                    tabs = st.tabs(tab_titles)
                    for i in range(6):
                        with tabs[i]:
                            st.markdown('<div class="report-card">', unsafe_allow_html=True)
                            st.markdown(final_contents[i])
                            st.markdown('</div>', unsafe_allow_html=True)

                    df = pd.DataFrame({"섹션": tab_titles, "내용": final_contents})
                    st.download_button("📥 엑셀 저장", data=to_excel(df), file_name=f"{keyword}_전략.xlsx")

        except Exception as e:
            st.error(f"시스템 오류: {e}")
