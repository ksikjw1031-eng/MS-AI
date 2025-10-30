# utils.py
import os
import json
import re
import requests
import streamlit as st
from datetime import datetime, timedelta
from openai import AzureOpenAI
import config  # config.py

# [추가 — 자사 판별 헬퍼 블록]
SELF_COMPANY = "KT DS"
SELF_ALIASES = {"KT DS", "kt ds", "케이티디에스", "KTDS", "케이티 DS", "케이티 디에스"}

def _normalize_name(name: str) -> str:
    if not name:
        return ""
    s = re.sub(r"[^0-9A-Za-z가-힣]", "", name).lower()
    return s

def is_self_company(company: str) -> bool:
    n = _normalize_name(company or "")
    if not n:
        return True  # company가 비어있다면 기본적으로 자사 관점
    for alias in SELF_ALIASES | {SELF_COMPANY}:
        if _normalize_name(alias) == n:
            return True
    return False


# ===================== 공용 유틸 (JSON) =====================
def extract_json_str(text: str):
    if not text:
        return None
    s = str(text).strip()
    m = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE).match(s)
    if m:
        s = m.group(1).strip()
    if "{" in s and "}" in s:
        start, end = s.find("{"), s.rfind("}")
        cand = re.sub(r",\s*([}\]])", r"\1", s[start:end + 1].strip())
        try:
            json.loads(cand)
            return cand
        except Exception:
            pass
    for b in re.findall(r"```json\s*(.*?)```", s, flags=re.DOTALL | re.IGNORECASE):
        b2 = re.sub(r",\s*([}\]])", r"\1", b.strip())
        try:
            json.loads(b2)
            return b2
        except Exception:
            pass
    s2 = re.sub(r",\s*([}\]])", r"\1", s)
    try:
        json.loads(s2)
        return s2
    except Exception:
        return None

# ===== 안전 JSON 파서 (추가) =====
def safe_json_loads(obj):
    """
    dict/list면 그대로 사용, 문자열이면 코드펜스 제거 후 json.loads 시도.
    실패 시 빈 dict 반환(렌더링 끊김 방지).
    """
    if obj is None:
        return {}
    if isinstance(obj, (dict, list)):
        return obj
    s = str(obj or "")
    try:
        s2 = extract_json_str(s) or s
    except Exception:
        s2 = s
    try:
        return json.loads(s2) if s2 else {}
    except Exception:
        return {}

def parse_json_from_session(key):
    """
    기존 호출부와 호환 유지. 세션의 값을 안전하게 dict로 변환.
    """
    raw = st.session_state.get(key)
    return safe_json_loads(raw)

# ===================== Azure OpenAI =====================
@st.cache_data(ttl=3600, show_spinner="Azure OpenAI 호출 중...")
def run_aoai(messages, *, max_tokens: int = 800, temperature: float = 0.2):
    if not (config.AOAI_ENDPOINT and config.AOAI_KEY and config.AOAI_DEPLOY):
        raise RuntimeError("Azure OpenAI 환경변수가 설정되지 않았습니다.")
    client = AzureOpenAI(
        api_key=config.AOAI_KEY,
        api_version=config.AOAI_VER,
        azure_endpoint=config.AOAI_ENDPOINT,
    )
    resp = client.chat.completions.create(
        model=config.AOAI_DEPLOY,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content

# ===================== PEST·SWOT / 통합 인사이트 프롬프트 =====================
NEWS_PSWOT_SCHEMA = """
{
  "PEST": {"P": ["문장1~2"], "E": ["문장1~2"], "S": ["문장1~2"], "T": ["문장1~2"]},
  "SWOT": {"S": ["문장1~2"], "W": ["문장1~2"], "O": ["문장1~2"], "T": ["문장1~2"]},
  "one_liner": "자사 한 줄 대응전략 + KPI 2~3개 예시"
}
""".strip()

# [추가 — 자사 판별 헬퍼 블록]
def build_messages_news(company, techs, domains, news):
    """뉴스 리스트를 받아 PEST·SWOT JSON을 요청하는 Chat Completions 메시지 구성
       - 자사(=KT DS)일 때 경쟁사처럼 서술되는 오류 방지 규칙 포함
    """
    # ① 자사 여부 판단 (utils 상단에 추가한 is_self_company 사용)
    self_mode = is_self_company(company)

    # ② 표시용 컨텍스트 문자열
    tech_text   = ", ".join(techs) if techs else "N/A"
    domain_text = ", ".join(domains) if domains else "N/A"
    info_lines  = [f"기술: {tech_text}", f"도메인: {domain_text}"]
    if company:
        info_lines.insert(0, f"회사: {company}")
    info_text = "\n".join(info_lines)

    # ③ 뉴스 블록
    news_block = ""
    for i, n in enumerate(news or [], 1):
        news_block += (
            f"[{i}] {n.get('title','(제목 없음)')} — {n.get('provider','')} — {n.get('datePublished','')}\n"
            f"요약: {n.get('snippet','')}\nURL: {n.get('url','')}\n\n"
        )

    # ④ 자사/타사 규칙
    if self_mode:
        persona_rules = (
            f"- 자사는 '{SELF_COMPANY}'로 정의. 뉴스에 등장하는 '{SELF_COMPANY}'는 곧 자사.\n"
            f"- '{SELF_COMPANY}'를 경쟁사로 취급 금지. "
            f"'자사 대비 {SELF_COMPANY}' 같은 표현 금지.\n"
            f"- 벤치마킹/비교 대상은 '{SELF_COMPANY}'가 아님(경쟁사 또는 개별 타사명으로 표기).\n"
            f"- 시점은 현재, 어조는 내부 전략 보고서 톤."
        )
    else:
        persona_rules = (
            f"- 자사는 '{SELF_COMPANY}'. 분석 대상 회사는 '{company}'.\n"
            f"- '자사'는 항상 '{SELF_COMPANY}'를 의미. '{SELF_COMPANY}'와 '{company}' 혼동 금지.\n"
            f"- 출력은 자사 관점(= {SELF_COMPANY})에서 '{company}'를 평가."
        )

    # ⑤ 프롬프트
    user = (
        "당신은 전략/기획 전문가입니다. 아래 정보와 뉴스 근거를 기반으로 "
        "PEST / SWOT 4사분면용 요약(각 칸 1~2문장)을 JSON으로 작성하세요.\n"
        f"{persona_rules}\n\n"
        f"JSON 스키마:\n{NEWS_PSWOT_SCHEMA}\n\n"
        "제약:\n"
        "- 각 리스트 최대 2문장, 문장 끝 마침표.\n"
        "- 필요 시 문장 끝에 (출처:[1]) 허용.\n"
        "- JSON 외 텍스트 금지.\n\n"
        f"컨텍스트:\n{info_text}\n\n=== 뉴스 근거 ===\n{news_block}"
    )

    return [
        {"role": "system", "content": "한국어로만 작성. 반드시 JSON만 출력."},
        {"role": "user",   "content": user},
    ]


COMBINED_SCHEMA = """
{
  "internal_summary": ["문장(끝에 [D#])", "문장(끝에 [D#])"],
  "strengths": ["문장(끝에 [D#])", "문장(끝에 [D#])"],
  "weaknesses": ["문장(끝에 [D#])", "문장(끝에 [D#])"],
  "external_insights": ["문장(끝에 [N#])", "문장(끝에 [N#])"],
  "proposals": {
    "benchmarking": ["문장(근거 [D#]/[N#])", "문장(근거 [D#]/[N#])"],
    "cooperation": ["문장(근거 [D#]/[N#])", "문장(근거 [D#]/[N#])"],
    "differentiation": ["문장(근거 [D#]/[N#])", "문장(근거 [D#]/[N#])"],
    "execution_kpis": ["문장(자사 KPI)", "문장(자사 KPI)"]
  }
}
""".strip()

def build_messages_combined(news_items, hits, company, techs, domains):
    """뉴스(N#)와 내부문서(D#)를 합쳐 통합 인사이트 JSON을 요청하는 메시지 구성"""
    tech_text   = ", ".join(techs) if techs else "N/A"
    domain_text = ", ".join(domains) if domains else "N/A"
    A = (company or "자사").strip()

    nb, db = "", ""
    for i, n in enumerate(news_items, 1):
        nb += (
            f"[N{i}] {n.get('title','(제목 없음)')} — {n.get('provider','')} — {n.get('datePublished','')}\n"
            f"요약:{n.get('snippet','')}\nURL:{n.get('url','')}\n\n"
        )
    for i, h in enumerate(hits, 1):
        title = h.get("title") or "(제목 없음)"
        db += f"[D{i}] {title} - {h.get('source','')}\n내용:\n{h.get('content','')}\n\n"

    user = (
        f"아래 외부 뉴스(N#)와 내부 문서(D#)를 바탕으로 자사({A}) 관점의 간결한 인사이트를 JSON으로만 출력.\n\n"
        f"JSON 스키마:\n{COMBINED_SCHEMA}\n\n"
        f"제약:\n- JSON 외 텍스트 금지.\n- 각 항목 1문장, 배열 최대 2개.\n- [N#]/[D#]만 인용.\n\n"
        f"맥락:\n회사(A): {A}\n기술: {tech_text}\n도메인: {domain_text}\n\n=== 외부 뉴스 ===\n{nb}\n=== 내부 문서 ===\n{db}"
    )
    return [
        {"role": "system", "content": "한국어로만 작성. 반드시 JSON만 출력."},
        {"role": "user",   "content": user},
    ]

# ===================== 뉴스 (메인 페이지용) =====================
@st.cache_data(ttl=3600, show_spinner="NewsAPI에서 뉴스 수집 중...")
def fetch_news_ko(query: str, cnt: int, freshness: str, use_and: bool = False):
    if not config.NEWS_KEY:
        raise RuntimeError("환경변수 NEWSAPI_KEY가 비어 있습니다.")
    days = {"Day": 1, "Week": 7, "Month": 30}.get(freshness, 7)
    from_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    q = (query or "").strip()
    if not q:
        raise RuntimeError("검색어가 비어 있습니다.")
    if use_and:
        terms = [t for t in q.split() if t]
        q = " AND ".join(terms) if terms else q

    r = requests.get(
        "https://newsapi.org/v2/everything",
        params={
            "q": q,
            "from": from_date,
            "sortBy": "publishedAt",
            "pageSize": cnt,
            "language": "ko",
            "apiKey": config.NEWS_KEY,
            "searchIn": "title,description,content",
        },
        timeout=20,
    )
    r.raise_for_status()
    out = []
    for a in r.json().get("articles", []) or []:
        out.append({
            "title": a.get("title") or "(제목 없음)",
            "snippet": a.get("description") or a.get("content") or "",
            "url": a.get("url"),
            "datePublished": a.get("publishedAt") or "",
            "provider": (a.get("source") or {}).get("name", "NewsAPI"),
        })
    return out[:cnt]

@st.cache_data(ttl=3600, show_spinner="Naver News에서 뉴스 수집 중...")
def fetch_news_naver(query: str, cnt: int = 5):
    if not (config.NAVER_ID and config.NAVER_SECRET):
        raise RuntimeError("NAVER_CLIENT_ID/SECRET가 없습니다.")
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {"X-Naver-Client-Id": config.NAVER_ID, "X-Naver-Client-Secret": config.NAVER_SECRET}
    params = {"query": (query or "").strip(), "display": cnt, "sort": "date"}
    r = requests.get(url, headers=headers, params=params, timeout=15)
    r.raise_for_status()
    out = []
    for a in r.json().get("items", []) or []:
        title = (a.get("title") or "").replace("<b>", "").replace("</b>", "")
        desc  = (a.get("description") or "").replace("<b>", "").replace("</b>", "")
        out.append({
            "title": title or "(제목 없음)",
            "snippet": desc,
            "url": a.get("link") or "",
            "datePublished": a.get("pubDate") or "",
            "provider": "Naver News",
        })
    return out[:cnt]

# ===================== Azure Search =====================
@st.cache_data(ttl=3600)
def get_index_schema(index_name: str):
    """(선택) 인덱스 점검용 — 없어도 동작함"""
    try:
        url = f"{config.SEARCH_ENDPOINT}/indexes/{index_name}?api-version={config.SEARCH_API_VER}"
        r = requests.get(url, headers={"api-key": config.SEARCH_KEY}, timeout=20)
        r.raise_for_status()
        return r.json().get("fields", []) or []
    except Exception as e:
        st.error(f"인덱스 스키마 조회 실패: {e}")
        return []

def detect_fieldmap(fields):
    """필드 자동 감지 (없어도 동작 가능)"""
    by = {f.get("name"): f for f in (fields or []) if isinstance(f, dict)}
    def pick(cands):
        for c in cands:
            if c in by:
                return c
    content = pick(["content","merged_content","text","page_content","chunk","document","body"])
    title   = pick(["title","file_name","metadata_storage_name","name","filename","doc_title"])
    blob    = pick(["metadata_storage_name","file_name","filename","blob_name","name"])
    path    = pick(["metadata_storage_path","storage_path","path","filepath"])
    url     = pick(["url","source_url","link","source"])
    blob_filterable = bool((by.get(blob) or {}).get("filterable")) if blob else False
    select_list = [x for x in [content, title, "metadata_storage_name" if "metadata_storage_name" in (by or {}) else None, path, url] if x]
    select = ",".join(dict.fromkeys(select_list)) if select_list else None
    return {
        "content": content,
        "title": title,
        "blob": blob,
        "blob_filterable": blob_filterable,
        "path": path,
        "url": url,
        "select": select or "title,url",
    }

# ===================== 검색 (blob/키워드) =====================
@st.cache_data(ttl=600, show_spinner="Blob 이름으로 문서 검색 중...")
def search_docs_by_blobname(blob_name: str, top: int = 8, *, nonce: int = 0):
    """
    업로드한 blob_name으로 문서 조각 검색 — '정확히 그 파일'만 반환.
    """
    if not (config.SEARCH_ENDPOINT and config.SEARCH_KEY and config.SEARCH_INDEX):
        st.error("Azure Search 설정이 누락되었습니다. .env의 AZURE_SEARCH_* 값을 확인하세요.")
        return []
    safe_name = (blob_name or "").strip()
    if not safe_name:
        return []
    url = f"{config.SEARCH_ENDPOINT}/indexes/{config.SEARCH_INDEX}/docs/search?api-version={config.SEARCH_API_VER}"
    headers = {"Content-Type": "application/json", "api-key": config.SEARCH_KEY}

    base = os.path.basename(safe_name)
    uuid_part = safe_name.split("_", 1)[0] if "_" in safe_name else ""

    candidates = []
    candidates.append({"search": f"\"{safe_name}\"", "top": int(top)})
    if base and base != safe_name:
        candidates.append({"search": f"\"{base}\"", "top": int(top)})
    if uuid_part and uuid_part != safe_name:
        candidates.append({"search": f"\"{uuid_part}\"", "top": int(top)})

    def _try(body):
        try:
            r = requests.post(url, headers=headers, json=body, timeout=20)
            r.raise_for_status()
            j = r.json()
            return (j.get("value") or []) if isinstance(j, dict) else []
        except requests.exceptions.HTTPError as e:
            try:
                st.error(f"문서 검색 실패: {e} · {e.response.text}")
            except Exception:
                st.error(f"문서 검색 실패: {e}")
            return []
        except Exception as e:
            st.error(f"문서 검색 실패: {e}")
            return []

    raw_vals = []
    for body in candidates:
        raw_vals = _try(body)
        if raw_vals:
            break
    if not raw_vals:
        return []

    def _match(h: dict) -> bool:
        text_name = (h.get("metadata_storage_name") or h.get("title") or "")
        text_name = str(text_name)
        return (
            (safe_name and safe_name in text_name) or
            (base and base in text_name) or
            (uuid_part and uuid_part in text_name)
        )

    filtered = [h for h in raw_vals if isinstance(h, dict) and _match(h)]

    items = []
    for h in filtered:
        title = h.get("title") or h.get("metadata_storage_name") or "(제목 없음)"
        text  = h.get("merged_content") or h.get("content") or h.get("text") or ""
        src   = h.get("url") or h.get("metadata_storage_path") or h.get("source") or ""
        items.append({
            "title": str(title) if isinstance(title, str) else "(제목 없음)",
            "content": str(text) if isinstance(text, str) else "",
            "source": str(src) if isinstance(src, str) else ""
        })
    return items

@st.cache_data(ttl=600, show_spinner="키워드로 문서 검색 중...")
def search_docs_by_keyword(query: str, top: int = 8):
    """
    키워드 검색 — 항상 list[dict] 반환.
    """
    if not (config.SEARCH_ENDPOINT and config.SEARCH_KEY and config.SEARCH_INDEX):
        st.error("Azure Search 설정이 누락되었습니다. .env의 AZURE_SEARCH_* 값을 확인하세요.")
        return []

    q = (query or "").strip()
    if not q:
        return []

    url = f"{config.SEARCH_ENDPOINT}/indexes/{config.SEARCH_INDEX}/docs/search?api-version={config.SEARCH_API_VER}"
    headers = {"Content-Type": "application/json", "api-key": config.SEARCH_KEY}

    candidates = [
        {"search": q,          "top": int(top)},
        {"search": f"\"{q}\"", "top": int(top)},
    ]

    def _try(body):
        try:
            r = requests.post(url, headers=headers, json=body, timeout=20)
            r.raise_for_status()
            j = r.json()
            return (j.get("value") or []) if isinstance(j, dict) else []
        except requests.exceptions.HTTPError as e:
            try:
                st.error(f"문서 검색 실패: {e} · {e.response.text}")
            except Exception:
                st.error(f"문서 검색 실패: {e}")
            return []
        except Exception as e:
            st.error(f"문서 검색 실패: {e}")
            return []

    vals = []
    for body in candidates:
        vals = _try(body)
        if vals:
            break

    items = []
    for h in vals:
        if not isinstance(h, dict):
            continue
        title = h.get("title") or h.get("metadata_storage_name") or "(제목 없음)"
        text  = h.get("merged_content") or h.get("content") or h.get("text") or ""
        src   = h.get("url") or h.get("metadata_storage_path") or h.get("source") or ""
        items.append({
            "title": str(title) if isinstance(title, str) else "(제목 없음)",
            "content": str(text) if isinstance(text, str) else "",
            "source": str(src) if isinstance(src, str) else ""
        })
    return items

# ===================== 문서 요약 =====================
@st.cache_data(ttl=3600, show_spinner="문서 조각 요약 중...")
def summarize_docs_combined(hits, max_chars: int = 20000) -> str:
    safe_hits = [h for h in (hits or []) if isinstance(h, dict)]
    chunks, total = [], 0
    for i, h in enumerate(safe_hits, 1):
        title = h.get("title")
        title = title if isinstance(title, str) and title.strip() else "(제목 없음)"
        content = h.get("content")
        if not isinstance(content, str):
            content = "" if content is None else str(content)
        piece = f"[D{i}] {title}\n{content}\n\n"
        if total + len(piece) > max_chars:
            remain = max_chars - total
            if remain > 0:
                chunks.append(piece[:remain])
            break
        chunks.append(piece)
        total += len(piece)

    merged = "".join(chunks) if chunks else ""
    if not (config.AOAI_ENDPOINT and config.AOAI_KEY and config.AOAI_DEPLOY):
        return merged[:600] + ("…" if len(merged) > 600 else "")

    resp = run_aoai(
        [
            {"role": "system", "content": "한국어로 작성. 중복 제거, 핵심만 간결하게."},
            {"role": "user", "content": "아래 여러 문서 조각을 3~4줄로 한글 요약하세요. 불필요한 수식어/중복은 제거:\n\n" + merged},
        ],
        max_tokens=1100,
    )
    return (resp or "").strip()

# ===================== 우선 제안 선택 =====================
@st.cache_data(ttl=3600, show_spinner="우선 제안 선택 중...")
def choose_single_proposal(proposals: dict, _take2_func):
    """
    proposals = {
      "benchmarking": [...], "cooperation": [...], "differentiation": [...],
      "execution_kpis": [...]
    }
    반환: (choice, summary_list)
    """
    if not isinstance(proposals, dict):
        return None, []

    bench = proposals.get("benchmarking") or []
    coop  = proposals.get("cooperation") or []
    diff  = proposals.get("differentiation") or []

    def _take(items, n=4):
        if callable(_take2_func):
            got = _take2_func(items or [])
            if len(got) < n:
                rest = [str(x).strip() for x in (items or []) if str(x).strip() and x not in got]
                got = (got or []) + rest[: max(0, n - len(got))]
            return [str(x).strip() for x in got if str(x).strip()]
        return [str(x).strip() for x in (items or []) if str(x).strip()][:n]

    scores = {
        "benchmarking": len([x for x in bench if str(x).strip()]),
        "cooperation": len([x for x in coop if str(x).strip()]),
        "differentiation": len([x for x in diff if str(x).strip()]),
    }
    if max(scores.values() or [0]) == 0:
        return None, []

    # 동점 우선순위: 차별화 > 협력 > 벤치
    order = sorted(
        scores.items(),
        key=lambda kv: (kv[1], kv[0] == "differentiation", kv[0] == "cooperation"),
        reverse=True,
    )
    choice = order[0][0]

    pick = {"benchmarking": bench, "cooperation": coop, "differentiation": diff}[choice]
    summary = _take(pick, n=4)
    return choice, summary or _take(bench or coop or diff, n=2)
