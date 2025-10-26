# app.py — 최소동작(NewsAPI) 버전 (필수 수정 반영)
import os
from datetime import datetime, timedelta

import requests
import streamlit as st

# .env 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

st.set_page_config(page_title="News → LLM 분석 (MVP)", layout="wide")
st.title("📰 News fetch (NewsAPI) — Sanity Check")

# 키 체크
NEWS_KEY = os.getenv("NEWSAPI_KEY")
col1, col2 = st.columns(2)
col1.metric("NEWSAPI_KEY", "OK" if NEWS_KEY else "MISSING")
# (경미 수정) 두 번째 컬럼도 활용해 Azure 설정 상태 표시
col2.metric("AZURE_OPENAI_ENDPOINT", "OK" if os.getenv("AZURE_OPENAI_ENDPOINT") else "MISSING")

st.divider()

# ✅ 세션 초기화 (GPT 버튼만 눌렀을 때 NameError 예방)
if "news_results" not in st.session_state:
    st.session_state["news_results"] = []

# 입력 UI
q = st.text_input("검색어", value="삼성SDS")
fresh = st.selectbox("신선도", ["Day", "Week", "Month"], index=1)
count = st.slider("개수", 1, 5, 3)

def fetch_news(query: str, cnt: int, freshness: str):
    if not NEWS_KEY:
        raise RuntimeError("환경변수 NEWSAPI_KEY가 비어 있습니다. (.env에 NEWSAPI_KEY=<발급키>)")

    # 신선도 → from 날짜
    days = {"Day": 1, "Week": 7, "Month": 30}.get(freshness, 7)
    from_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

    # 표기/동의어 OR 확장
    base = (query or "").strip()
    if not base:
        base = "삼성SDS"
    variants = {
        base,
        base.replace(" ", ""),
        base.replace(" ", "-"),
        base.replace(" ", "_"),
        "삼성SDS",
        "삼성 SDS",
        "Samsung SDS",
        "삼성에스디에스",
        "SDS" if "sds" in base.lower() else "",
    }
    terms = [v for v in variants if v]
    q_expanded = " OR ".join([f"\"{t}\"" if " " in t or "-" in t or "_" in t else t for t in terms])

    def call_newsapi(language: str | None):
        params = {
            "q": q_expanded,
            "from": from_date,
            "sortBy": "publishedAt",
            "pageSize": max(1, min(cnt, 10)),
            "searchIn": "title,description,content",
            "apiKey": NEWS_KEY,
        }
        if language:
            params["language"] = language
        r = requests.get("https://newsapi.org/v2/everything", params=params, timeout=20)
        r.raise_for_status()
        return r.json().get("articles", [])

    # ko → en → 제한 없음
    arts = call_newsapi("ko")
    if not arts:
        arts = call_newsapi("en")
    if not arts:
        arts = call_newsapi(None)

    items = []
    for a in arts[:cnt]:
        items.append(
            {
                "title": a.get("title") or "(제목 없음)",
                "snippet": a.get("description") or a.get("content") or "",
                "url": a.get("url"),
                "datePublished": a.get("publishedAt") or "",
                "provider": (a.get("source") or {}).get("name", "NewsAPI"),
            }
        )
    return items

if st.button("🔎 뉴스 가져오기"):
    try:
        results = fetch_news(q, count, fresh)
        st.session_state["news_results"] = results  # ✅ 세션에 저장 (GPT 단계에서 사용)
        if not results:
            st.warning("결과가 없습니다. 검색어를 단순하게 바꿔보세요. 예: '삼성', 'SDS'")
        for i, it in enumerate(results, 1):
            st.markdown(f"**[{i}] {it['title']}**")
            st.caption(f"{it['provider']} · {it['datePublished']}")
            if it["snippet"]:
                st.write(it["snippet"])
            if it["url"]:
                st.link_button("기사 열기", it["url"], use_container_width=True)
            st.divider()
    except Exception as e:
        # 어떤 오류든 화면에 보여주기
        st.error(f"오류: {e}")

# -------------------------------
# 🔹 Azure OpenAI 분석 (요약 + PEST + SWOT)
# -------------------------------
from openai import AzureOpenAI

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
# ✅ 기본값 지정 (없을 때 오류 예방)
api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

if endpoint and api_key and deployment:
    st.divider()
    st.subheader("🧠 GPT 분석 (PEST · SWOT)")

    if st.button("🪄 뉴스 기반 PEST·SWOT 생성"):
        try:
            # ✅ 세션에서 안전하게 읽기 + 빈 경우 가드
            items = st.session_state.get("news_results", [])
            if not items:
                st.warning("먼저 '🔎 뉴스 가져오기'로 뉴스를 불러오세요.")
            else:
                # 뉴스 본문 통합
                joined = "\n\n".join([f"- {it['title']}\n{it['snippet']}" for it in items])

                client = AzureOpenAI(
                    api_key=api_key,
                    api_version=api_version,
                    azure_endpoint=endpoint,
                )

                prompt = f"""
                다음 뉴스 내용을 바탕으로 PEST와 SWOT 분석을 간결히 정리하세요.
                각 요소별로 1~2줄씩 bullet로 작성하세요.
                뉴스 내용:
                {joined}
                """

                with st.spinner("GPT가 분석 중입니다..."):
                    resp = client.chat.completions.create(
                        model=deployment,
                        messages=[
                            {"role": "system", "content": "당신은 비즈니스 전략 분석 전문가입니다."},
                            {"role": "user", "content": prompt},
                        ],
                    )

                answer = resp.choices[0].message.content
                st.markdown("### 🔍 분석 결과")
                st.write(answer)
        except Exception as e:
            st.error(f"분석 중 오류 발생: {e}")
else:
    st.warning("Azure OpenAI 환경변수가 설정되지 않았습니다. (.env 확인)")
