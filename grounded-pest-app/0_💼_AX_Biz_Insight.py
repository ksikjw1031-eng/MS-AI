# app.py
import streamlit as st
import html
import re
from datetime import datetime

# 분리된 모듈 임포트
import config
import utils
from ui import inject_css, H1, H2, H3, render_pest_only, render_swot_only, _clean_citations, _take2

def _rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st._rerun()

# ---------------------- 공용 초기화 헬퍼 ----------------------
def _clear_analysis_state():
    for k in ("news_results", "pest_swot_json", "combined_json", "pdf_sig"):
        st.session_state.pop(k, None)
    st.cache_data.clear()
    st.cache_resource.clear()

# --- 페이지 설정 및 초기화 ---
st.set_page_config(page_title="AX Biz Insight", page_icon="💼", layout="wide")
inject_css()
config.initialize_session_state()

# ---------------------- 대제목 ----------------------
from ui import H1, H2  # 이미 임포트 되어 있으면 생략
H1("💼 AX Biz Insight")

st.caption("외부·내부 데이터 기반 AX 전략 인사이트 플랫폼")

# ---------------------- 섹션: 외부 문서 검색 ----------------------
st.subheader("📄 외부 문서 검색")
st.caption("AI가 외부 뉴스와 데이터를 분석해 핵심 인사이트를 제공합니다.")

# ---------------------- 환경 변수 상태 ----------------------
with st.expander("환경 변수 상태 보기", expanded=False):
    c1, c2, c3 = st.columns(3)
    c1.metric("NEWSAPI/NAVER", "OK" if config.NEWS_KEY or (config.NAVER_ID and config.NAVER_SECRET) else "MISSING")
    c2.metric("AZURE_OPENAI_ENDPOINT", "OK" if config.AOAI_ENDPOINT else "MISSING")
    c3.metric("AZURE_OPENAI_DEPLOYMENT", "OK" if config.AOAI_DEPLOY else "MISSING")
    st.caption("내부 문서 기능을 쓰려면 AZURE_STORAGE_CONN / AZURE_SEARCH_* 값을 설정하세요.")

# ---------------------- 📄 내부 문서(PDF) 업로드 안내 (업로드 UI 제거) ----------------------

go_label = "📄 내부 문서 분석 페이지로 이동"
clicked = st.button(go_label, use_container_width=True)
if clicked:
    try:
        # Streamlit 1.25+ 권장
        st.switch_page("pages/1_📄_내부_문서_분석.py")
    except Exception:
        # Fallback: 페이지 링크 제공 (1.31+)
        st.page_link("pages/1_📄_내부_문서_분석.py", label="📄 내부 문서 분석 열기", icon="📄")

# ---------------------- 입력 UI (뉴스) ----------------------
colA, colB, colC = st.columns(3)
with colA:
    company_choice = st.selectbox(
        "회사 선택",
        ["선택 안 함 (기술·도메인만)", "KT DS", "삼성SDS", "LG CNS", "SK C&C", "현대오토에버",
         "카카오엔터프라이즈", "네이버클라우드", "기타(직접입력)"],
        index=1, key="sel_company"
    )
    if company_choice == "기타(직접입력)":
        company = st.text_input("회사명 직접 입력", "", placeholder="예: 한화시스템, NHN, 신세계I&C 등", key="txt_company_custom")
    elif company_choice == "선택 안 함 (기술·도메인만)":
        company = ""
    else:
        company = company_choice
with colB:
    techs = st.multiselect("관심 기술",
        ["AI", "RAG", "LangGraph", "Azure OpenAI", "Process Mining", "Cloud Native", "Azure AI Search", "MLOps", "Data Fabric"],
        default=["AI"], key="ms_techs")
with colC:
    domains = st.multiselect("도메인", ["금융", "제조", "리테일", "공공", "통신", "교육", "의료"], default=["금융"], key="ms_domains")

suggested_query = " ".join([s for s in [company or "", " ".join(techs), " ".join(domains)] if s]).strip()
st.session_state["q_input"] = suggested_query  # 선택값 바뀔 때마다 자동 반영
st.text_input("뉴스 검색어", key="q_input", placeholder="예: AI 금융 / 삼성SDS AI 금융")

opt_row1 = st.columns([1, 1, 1])
with opt_row1[0]:
    freshness = st.selectbox("신선도", ["Day", "Week", "Month"], index=1, key="sel_freshness")
with opt_row1[1]:
    k = st.slider("뉴스 개수", 1, 3, 2, key="sld_news_count")
with opt_row1[2]:
    strict_and = st.checkbox("모든 키워드 반드시 포함(AND)", value=False, key="chk_and",
        help="체크 시 '단어1 AND 단어2 AND ...' 형태 (NewsAPI 전용)")

# ---------------------- 버튼 로직 (뉴스) ----------------------
col_btn1, col_btn2 = st.columns([1, 1])
with col_btn1:
    click_search = st.button("🔎 뉴스 검색", use_container_width=True, key="btn_news_search")
with col_btn2:
    analyze = st.button("📊 PEST·SWOT 생성", use_container_width=True, key="btn_pest_swot")

if click_search:
    st.session_state.pop("pest_swot_json", None)
    st.session_state.pop("combined_json", None)

    q_now = st.session_state["q_input"].strip()
    if not q_now:
        st.warning("검색어를 입력하세요.")
    else:
        try:
            if config.NAVER_ID and config.NAVER_SECRET:
                st.session_state["news_results"] = utils.fetch_news_naver(q_now, k)
            elif config.NEWS_KEY:
                st.session_state["news_results"] = utils.fetch_news_ko(q_now, k, freshness, use_and=strict_and)
            else:
                st.error("NewsAPI 또는 Naver API 키가 설정되지 않았습니다.")

            st.success(f"뉴스 {len(st.session_state['news_results'])}건 수집 완료 ✅" if st.session_state["news_results"] else "결과가 없습니다.")
        except Exception as e:
            st.error(f"에러: {e}")

if analyze:
    news_items = st.session_state.get("news_results", [])
    if not news_items:
        st.warning("먼저 '뉴스 검색'을 실행하세요.")
    else:
        try:
            answer_json_text = utils.run_aoai(utils.build_messages_news(company, techs, domains, news_items))
            st.session_state["pest_swot_json"] = answer_json_text
            st.success("분석 완료 ✅ (아래 탭에서 확인)")
        except Exception as e:
            st.error(f"분석 중 오류: {e}")

# ---------------------- 📰 수집된 뉴스 ----------------------
H2("📰 수집된 뉴스")
news_items = st.session_state.get("news_results", [])
if not news_items:
    st.caption("아직 검색된 뉴스가 없습니다. 상단에서 '뉴스 검색'을 실행하세요.")
else:
    for i, n in enumerate(news_items, 1):
        with st.container():
            st.markdown(f"**[{i}] {n['title']}**")
            meta = " · ".join([x for x in [n.get('provider', ''), n.get('datePublished', '')] if x])
            if meta:
                st.caption(meta)
            if n.get("snippet"):
                st.write(html.escape(n["snippet"]))
            if n.get("url"):
                st.link_button("원문 열기", n["url"], use_container_width=True)
st.divider()

# ---------------------- 탭: PEST / SWOT / 대응전략 ----------------------
_default_pest = {"P": [], "E": [], "S": [], "T": []}
_default_swot = {"S": [], "W": [], "O": [], "T": []}

tab_pest, tab_swot, tab_action = st.tabs(["PEST Detail", "SWOT Detail", "대응전략"])

with tab_pest:
    data = (utils.parse_json_from_session("pest_swot_json") or {})
    render_pest_only((data.get("PEST") or _default_pest))
    if not data:
        st.caption("아직 분석 결과가 없습니다. 상단에서 뉴스 검색 후 '📊 PEST·SWOT 생성'을 눌러주세요.")

with tab_swot:
    data = (utils.parse_json_from_session("pest_swot_json") or {})
    render_swot_only((data.get("SWOT") or _default_swot))
    if not data:
        st.caption("아직 분석 결과가 없습니다. 상단에서 뉴스 검색 후 '📊 PEST·SWOT 생성'을 눌러주세요.")

with tab_action:
    data = (utils.parse_json_from_session("pest_swot_json") or {})
    one = (data.get("one_liner") or "").strip()
    if one:
        one = "\n".join(
            line.strip()
            for line in one.splitlines()
            if line.strip() and not re.search(r"\[D\d+\]", line)
        )
        one = "\n".join(dict.fromkeys(one.splitlines()))
        st.markdown(
            f'<div class="card-accent">{html.escape(_clean_citations(one))}</div>',
            unsafe_allow_html=True
        )
    else:
        st.caption("한 줄 대응전략은 아직 없습니다.")

    combined_data = utils.parse_json_from_session("combined_json") or {}
    kpis = _take2(((combined_data.get("proposals") or {}).get("execution_kpis")))
    if kpis:
        H3("실행 KPI")
        for l in kpis:
            st.write(f"- {l}")
    else:
        st.caption("실행 KPI가 여기 표시됩니다.")
