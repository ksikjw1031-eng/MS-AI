# app.py
# --- Streamlit MVP: 한국어 뉴스 기반 PEST & SWOT ---
# 환경변수 (.env 예시)
#   NEWSAPI_KEY=...
#   AZURE_OPENAI_ENDPOINT=https://<your-aoai>.openai.azure.com
#   AZURE_OPENAI_API_KEY=...
#   AZURE_OPENAI_API_VERSION=2024-08-01-preview
#   AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
#
# 실행:
#   streamlit run app.py

import os
from datetime import datetime, timedelta
import requests
import streamlit as st

# ---------------------- 환경 로드 ----------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

st.set_page_config(page_title="Grounded PEST·SWOT", page_icon="🧭", layout="wide")
st.title("🧭 Grounded PEST & SWOT — 한국어 뉴스 기반 분석")

# ---------------------- 환경 변수 상태 ----------------------
NEWS_KEY = os.getenv("NEWSAPI_KEY")
AOAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AOAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AOAI_VER = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
AOAI_DEPLOY = os.getenv("AZURE_OPENAI_DEPLOYMENT")

with st.expander("환경 변수 상태 보기", expanded=False):
    c1, c2, c3 = st.columns(3)
    c1.metric("NEWSAPI_KEY", "OK" if NEWS_KEY else "MISSING")
    c2.metric("AZURE_OPENAI_ENDPOINT", "OK" if AOAI_ENDPOINT else "MISSING")
    c3.metric("AZURE_OPENAI_DEPLOYMENT", "OK" if AOAI_DEPLOY else "MISSING")

# ---------------------- 세션 초기화 ----------------------
if "news_results" not in st.session_state:
    st.session_state["news_results"] = []

# ---------------------- 검색 옵션 ----------------------
colA, colB, colC = st.columns(3)
with colA:
    company = st.text_input("회사명", value="삼성SDS")
with colB:
    techs = st.multiselect(
        "관심 기술",
        ["GenAI", "RAG", "LangGraph", "Azure OpenAI", "Process Mining", "Cloud Native"],
        default=["GenAI"]
    )
with colC:
    domains = st.multiselect(
        "도메인",
        ["금융", "제조", "리테일", "공공", "통신", "교육", "의료"],
        default=["금융"]
    )

suggested_query = " ".join(
    [s for s in [company or "", " ".join(techs), " ".join(domains)] if s]
).strip()

st.text_input("뉴스 검색어", key="q_input", value=suggested_query, placeholder="예: 삼성SDS GenAI 금융")

opt1, opt2 = st.columns([1, 1])
with opt1:
    freshness = st.selectbox("신선도", ["Day", "Week", "Month"], index=1)
with opt2:
    k = st.slider("뉴스 개수", 1, 10, 5)

# ---------------------- NewsAPI 함수 ----------------------
def fetch_news_ko(query: str, cnt: int, freshness: str):
    if not NEWS_KEY:
        raise RuntimeError("환경변수 NEWSAPI_KEY가 비어 있습니다.")
    days = {"Day": 1, "Week": 7, "Month": 30}.get(freshness, 7)
    from_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

    params = {
        "q": query,
        "from": from_date,
        "sortBy": "publishedAt",
        "pageSize": cnt,
        "language": "ko",  # ✅ 한국어 뉴스만
        "apiKey": NEWS_KEY,
        "searchIn": "title,description,content",
    }
    r = requests.get("https://newsapi.org/v2/everything", params=params, timeout=20)
    r.raise_for_status()
    arts = r.json().get("articles", [])
    items = []
    for a in arts:
        items.append({
            "title": a.get("title") or "(제목 없음)",
            "snippet": a.get("description") or a.get("content") or "",
            "url": a.get("url"),
            "datePublished": a.get("publishedAt") or "",
            "provider": (a.get("source") or {}).get("name", "NewsAPI"),
        })
    return items[:cnt]

# ---------------------- GPT 프롬프트 ----------------------
def build_messages(company: str, techs: list[str], domains: list[str], news: list[dict]):
    tech_text = ", ".join(techs) if techs else "N/A"
    domain_text = ", ".join(domains) if domains else "N/A"

    news_block = ""
    for i, n in enumerate(news, start=1):
        news_block += f"[{i}] {n['title']} — {n['provider']} — {n['datePublished']}\n요약: {n['snippet']}\nURL: {n['url']}\n\n"

    user = f"""
당신은 전략/기획 전문가입니다. 아래 정보와 뉴스 근거를 기반으로
간결한 **PEST 분석**과 **SWOT 분석**, 그리고 **한 줄 대응전략**을 한국어로 작성하세요.

회사: {company}
기술: {tech_text}
도메인: {domain_text}

요구사항:
1) PEST: 정치/경제/사회/기술 각 2~3줄
2) SWOT: 각 항목 3~4개 불릿
3) 한 줄 대응전략: KPI 2~3개 포함
4) 출처 인덱스 표기 (예: (출처: [1],[3]))

=== 뉴스 근거 ===
{news_block}
"""
    return [
        {"role": "system", "content": "당신은 한국어로 비즈니스 전략 분석을 작성하는 전문가입니다."},
        {"role": "user", "content": user.strip()},
    ]

def run_aoai(messages: list[dict]) -> str:
    from openai import AzureOpenAI
    if not (AOAI_ENDPOINT and AOAI_KEY and AOAI_DEPLOY):
        raise RuntimeError("Azure OpenAI 환경변수가 설정되지 않았습니다.")
    client = AzureOpenAI(api_key=AOAI_KEY, api_version=AOAI_VER, azure_endpoint=AOAI_ENDPOINT)
    resp = client.chat.completions.create(
        model=AOAI_DEPLOY,
        messages=messages,
        temperature=0.2,
        max_tokens=1200,
    )
    return resp.choices[0].message.content

# ---------------------- 버튼 ----------------------
col_btn1, col_btn2 = st.columns([1, 1])
with col_btn1:
    click_search = st.button("🔎 뉴스 검색", use_container_width=True)
with col_btn2:
    analyze = st.button("🧠 PEST·SWOT 생성", use_container_width=True)

# ---------------------- 실행 ----------------------
if click_search:
    q_now = st.session_state["q_input"].strip()
    if not q_now:
        st.warning("검색어를 입력하세요.")
    else:
        try:
            with st.spinner("한국어 뉴스 수집 중..."):
                results = fetch_news_ko(q_now, k, freshness)
                st.session_state["news_results"] = results
            if results:
                st.success(f"뉴스 {len(results)}건 수집 완료 (한국어 전용)")
            else:
                st.warning("결과가 없습니다. 다른 검색어로 시도해보세요.")
        except Exception as e:
            st.error(f"에러: {e}")

news_items = st.session_state.get("news_results", [])
if news_items:
    st.subheader("📰 수집된 뉴스")
    for i, n in enumerate(news_items, start=1):
        with st.container(border=True):
            st.markdown(f"**[{i}] {n['title']}**")
            meta = " · ".join([x for x in [n.get('provider', ''), n.get('datePublished', '')] if x])
            if meta:
                st.caption(meta)
            if n.get("snippet"):
                st.write(n["snippet"])
            if n.get("url"):
                st.link_button("원문 열기", n["url"], use_container_width=True)
    st.divider()

if analyze:
    if not news_items:
        st.warning("먼저 '뉴스 검색'을 실행하세요.")
    else:
        try:
            with st.spinner("Azure OpenAI로 분석 중..."):
                msgs = build_messages(company, techs, domains, news_items)
                answer = run_aoai(msgs)
            st.success("분석 완료 ✅")
            st.subheader("📊 PEST & SWOT (결과)")
            st.markdown(answer)
            fname = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            st.download_button("⬇️ 결과 Markdown 저장", data=answer, file_name=fname, mime="text/markdown")
        except Exception as e:
            st.error(f"분석 중 오류: {e}")

st.divider()
st.caption("한국어 뉴스만 사용합니다. 검색어를 명확히 입력할수록 분석 품질이 향상됩니다.")
