# app.py
# --- Single-file Streamlit MVP: Bing News -> Azure OpenAI (PEST & SWOT) ---
# Prereqs (PowerShell example):
#   $env:AZURE_BING_KEY="..."
#   $env:AZURE_OPENAI_ENDPOINT="https://<your-aoai>.openai.azure.com"
#   $env:AZURE_OPENAI_API_KEY="..."
#   $env:AZURE_OPENAI_API_VERSION="2024-08-01-preview"
#   $env:AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini"
#
# Run:
#   streamlit run app.py

import os
import json
import time
import requests
import streamlit as st
from datetime import datetime, timedelta

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(
    page_title="Grounded Analysis MVP",
    page_icon="🧭",
    layout="wide"
)

# ---------------------------
# Helper: read env
# ---------------------------
def getenv_strict(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"환경변수 {name}가 비어 있습니다.")
    return v

def env_status():
    keys = [
        "AZURE_BING_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_API_VERSION",
        "AZURE_OPENAI_DEPLOYMENT",
    ]
    rows = []
    for k in keys:
        val = os.getenv(k)
        rows.append((k, "✅ 설정됨" if val else "❌ 없음"))
    return rows

# ---------------------------
# Bing News Search
# ---------------------------
def fetch_bing_news(query: str, count: int = 3, mkt: str = "ko-KR", freshness: str = "Week"):
    """
    Call Bing News Search v7 endpoint.
    freshness: Day | Week | Month
    """
    key = getenv_strict("AZURE_BING_KEY")
    url = "https://api.bing.microsoft.com/v7.0/news/search"
    headers = {"Ocp-Apim-Subscription-Key": key}
    params = {
        "q": query,
        "count": count,
        "mkt": mkt,
        "freshness": freshness,
        "sortBy": "Date",
        "textFormat": "Raw",
        "safeSearch": "Off",
    }
    r = requests.get(url, headers=headers, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    items = []
    for it in data.get("value", []):
        items.append({
            "title": it.get("name"),
            "snippet": it.get("description"),
            "url": it.get("url"),
            "datePublished": it.get("datePublished"),
            "provider": (it.get("provider") or [{}])[0].get("name", ""),
        })
    return items

# ---------------------------
# Azure OpenAI Chat Completion (REST)
# ---------------------------
def aoai_chat(messages, temperature=0.2, max_tokens=1200):
    endpoint = getenv_strict("AZURE_OPENAI_ENDPOINT").rstrip("/")
    api_key = getenv_strict("AZURE_OPENAI_API_KEY")
    api_version = getenv_strict("AZURE_OPENAI_API_VERSION")
    deployment = getenv_strict("AZURE_OPENAI_DEPLOYMENT")

    url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    payload = {
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
    resp.raise_for_status()
    j = resp.json()
    return j["choices"][0]["message"]["content"]

# ---------------------------
# Prompt
# ---------------------------
def build_prompt(company: str, techs: list[str], domains: list[str], news: list[dict]):
    tech_text = ", ".join(techs) if techs else "N/A"
    domain_text = ", ".join(domains) if domains else "N/A"

    # Combine news into a citation-friendly block
    lines = []
    for idx, n in enumerate(news, start=1):
        when = n.get("datePublished", "")
        try:
            when = datetime.fromisoformat(when.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
        except Exception:
            pass
        lines.append(f"[{idx}] {n['title']} — {n['provider']} — {when}\nURL: {n['url']}\n요약: {n.get('snippet','')}\n")
    news_block = "\n".join(lines) if lines else "뉴스 없음"

    user = f"""
당신은 전략/기획 전문 분석가입니다. 아래 회사/기술/도메인과 최신 뉴스 근거를 토대로
한국어로 간결하고 실행지향적인 **PEST 분석**과 **SWOT 분석**을 작성하세요.

요구사항:
1) **PEST**: 정치/정책, 경제, 사회/문화, 기술 각 2~3줄
2) **SWOT**: S/W/O/T 각 3~4개 불릿
3) **한 줄 대응전략**: KPIs 2~3개 포함 (예: 리드수, 제휴수, PoC건수, MRR 등)
4) 각 항목 끝에 괄호로 **출처 인덱스**를 표기 (예: (출처: [1],[3]))
5) 지나친 추측은 금지, 뉴스 근거에서만 도출

회사: {company}
기술(예시): {tech_text}
도메인(예시): {domain_text}

=== 최신 뉴스 (근거) ===
{news_block}
"""
    return [
        {"role": "system", "content": "You are a precise strategy analyst who writes in Korean with structured bullets."},
        {"role": "user", "content": user.strip()},
    ]

# ---------------------------
# UI
# ---------------------------
st.title("🧭 Grounded PEST & SWOT (Bing + Azure OpenAI)")
st.caption("단일 파일 MVP • Bing 뉴스 근거로 PEST·SWOT 생성")

with st.expander("환경변수 확인", expanded=False):
    for k, v in env_status():
        st.write(f"- **{k}**: {v}")
    st.info("환경변수는 VS Code 터미널에서 `echo $env:VAR` (PowerShell) 또는 `echo %VAR%`(cmd)로 확인할 수 있어요.")

cols = st.columns(3)
with cols[0]:
    company = st.selectbox(
        "회사 선택",
        ["삼성SDS", "LG CNS", "SK C&C", "현대오토에버", "카카오엔터프라이즈", "네이버클라우드", "기타(직접입력)"],
        index=0
    )
    if company == "기타(직접입력)":
        company = st.text_input("회사명 직접 입력", placeholder="예: KT DS")

with cols[1]:
    techs = st.multiselect(
        "관심 기술(선택)",
        ["GenAI", "RAG", "LangGraph", "Azure OpenAI", "Azure AI Search", "Process Mining", "MLOps", "Cloud Native", "Data Fabric"],
        default=["GenAI", "Azure OpenAI"]
    )

with cols[2]:
    domains = st.multiselect(
        "관심 도메인(선택)",
        ["금융", "제조", "리테일", "공공", "교육", "통신", "의료"],
        default=["금융"]
    )

query = st.text_input(
    "뉴스 검색 쿼리(자동 추천)",
    value=f"{company} {(' '.join(techs)) if techs else ''} {(' '.join(domains)) if domains else ''}".strip()
)

left, right = st.columns([1,1])
with left:
    freshness = st.selectbox("뉴스 신선도", ["Day", "Week", "Month"], index=1)
with right:
    k = st.slider("뉴스 개수", min_value=1, max_value=8, value=3, step=1)

run = st.button("🔎 최신 뉴스 수집 & 🧠 PEST·SWOT 생성", use_container_width=True)

news_items = []
analysis_md = ""

if run:
    try:
        with st.spinner("Bing에서 뉴스 수집 중..."):
            news_items = fetch_bing_news(query, count=k, freshness=freshness)
            if not news_items:
                st.warning("검색 결과가 없습니다. 쿼리를 바꿔보세요.")
        if news_items:
            st.success(f"뉴스 {len(news_items)}건 수집 완료")
            with st.spinner("Azure OpenAI로 분석 생성 중..."):
                messages = build_prompt(company, techs, domains, news_items)
                analysis_md = aoai_chat(messages)
            st.success("분석 생성 완료")
    except Exception as e:
        st.error(f"에러: {e}")

# ---------------------------
# Render results
# ---------------------------
if news_items:
    st.subheader("📰 뉴스 근거")
    for i, n in enumerate(news_items, start=1):
        with st.container(border=True):
            st.markdown(f"**[{i}] {n['title']}**")
            meta = []
            if n.get('provider'):
                meta.append(n['provider'])
            if n.get('datePublished'):
                meta.append(n['datePublished'])
            if meta:
                st.caption(" • ".join(meta))
            if n.get('snippet'):
                st.write(n['snippet'])
            if n.get('url'):
                st.markdown(f"[원문 링크로 이동]({n['url']})")

if analysis_md:
    st.subheader("📊 PEST & SWOT (생성 결과)")
    st.markdown(analysis_md)

    # Download button
    fname = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    st.download_button(
        "⬇️ 결과 Markdown 저장",
        data=analysis_md,
        file_name=fname,
        mime="text/markdown",
        use_container_width=True
    )

# ---------------------------
# Footer
# ---------------------------
st.divider()
st.caption("Tip: 좌측 상단 ▶ 버튼으로 사이드바를 열어 환경변수를 확인하세요. 내부 문서(Azure AI Search) 연결은 다음 단계에서 확장합니다.")
