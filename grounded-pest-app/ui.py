# ui.py
import streamlit as st
import html
import re
import json
from datetime import datetime
from utils import extract_json_str  # utils.py (아래 생성)에 의존

# ---------------------- CSS ----------------------
def inject_css():
    st.markdown("""
<style>
:root{
  --kt-red:#e60012;      /* KT 레드 */
  --kt-soft:#fff7f8;     /* 아주 연한 레드톤 배경 */
  --kt-border:#f1c9cd;   /* 연한 경계 */
  --card-bg:#fafafa;     /* 중립 카드 배경 */
  --text:#222;
}

/* ===== 타이포 레벨 ===== */
.app-h1{
  font-size:2.6rem;
  line-height:1.2;
  font-weight:900;
  margin:6px 0 10px;
  color:var(--text);
}
.app-h2{
  font-size:1.35rem;
  line-height:1.3;
  font-weight:750;
  margin:24px 0 12px;
  color:var(--text);
  border-bottom:1px solid var(--kt-border);
  padding-bottom:6px;
}
.app-h3{
  font-size:1.05rem;
  line-height:1.35;
  font-weight:700;
  margin:14px 0 8px;
  color:var(--text);
}

/* Streamlit 기본 헤더도 톤 맞춤 */
.stMarkdown h1, h1 {
  font-size: 2.4rem !important;
  font-weight: 800 !important;
  color: #222 !important;
  line-height: 1.15 !important;
  margin: 0 0 0.25rem 0 !important;
}
.stMarkdown h2, h2, .stSubheader {
  font-size: 1.35rem !important;
  font-weight: 750 !important;
  color: #333 !important;
  margin: 1.2rem 0 0.4rem 0 !important;
}

/* ===== 박스/그리드 ===== */
.grid-2, .grid-2-equal { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.grid-2-equal{ grid-auto-rows:1fr; }

/* 공통 카드 */
.card{
  border:1px solid rgba(0,0,0,.08);
  border-radius:12px;
  padding:10px 12px;
  background:var(--card-bg);
}
.card h3{ margin:0 0 6px; font-size:1rem; color:var(--text); }

/* 연한 강조 카드 (대시보드/통합 탭 공통) */
.card-accent{
  border:1px solid var(--kt-border);
  background:var(--kt-soft);
  border-radius:12px;
  padding:12px 14px;
  position:relative;
  box-shadow:0 3px 12px rgba(230,0,18,0.05);
}
.card-accent:before{ display:none; }

/* 쿼드/소프트 카드 (PEST·SWOT·강약점 그리드) */
.card-soft, .quad{
  border-radius:12px;
  padding:12px 14px;
  border:1px solid var(--kt-border);
  background:var(--kt-soft);
  box-shadow:0 3px 12px rgba(230,0,18,0.05);
  position:relative; height:100%;
}
.card-soft:before, .quad:before{
  content:""; position:absolute; left:0; top:0; bottom:0; width:6px;
  background:var(--kt-red); border-top-left-radius:12px; border-bottom-left-radius:12px; opacity:.6;
}

/* 카드 내 타이틀 통일 */
.quad h4,
.card-soft h3,
.box-title{
  margin:0 0 6px !important;
  font-size:1.05rem !important;
  font-weight:800 !important;
  color:var(--kt-red) !important;
  letter-spacing:0.01em;
}

/* 리스트(불릿) */
.quad ul, .card-soft ul{ margin:0 0 0 18px; }
.quad li, .card-soft li{ margin:4px 0; font-size:.96rem; color:var(--text); }

/* 구분선/간격 */
.section-divider{ border-top:1px dashed var(--kt-border); margin:18px 0; }
.section-gap-lg{ height:28px; }

/* 섹션 래퍼 (탭 내 제목 줄과 간격 통일) */
.section { margin: 8px 0 18px; }
.section-title{ font-size:1.05rem; font-weight:700; color:var(--text); margin:0 0 8px; padding:2px 0; }

/* === 대시보드 카드 스타일 통일 === */
.card-accent{
  margin: 8px 0 14px;       /* 카드 간 간격 */
  padding: 12px 14px;       /* 내부 여백 */
}
.card-accent .box-title{
  margin-bottom: 6px;       /* 카드 제목 아래 여백 */
}
.card-accent p{
  margin: .35rem 0;         /* 문단 간 여백 */
}

                
</style>
""", unsafe_allow_html=True)



# ---------------------- 제목 유틸 ----------------------
def H1(text): st.markdown(f'<div class="app-h1">{html.escape(text)}</div>', unsafe_allow_html=True)
def H2(text): st.markdown(f'<div class="app-h2">{html.escape(text)}</div>', unsafe_allow_html=True)
def H3(text): st.markdown(f'<div class="app-h3">{html.escape(text)}</div>', unsafe_allow_html=True)

# ---------------------- 공통 유틸 (UI 의존성) ----------------------
def _clean_citations(text: str) -> str:
    if not isinstance(text, str): text = str(text or "")
    text = re.sub(r"\s*\[(?:D|N)\d+\]\s*", "", text)
    text = re.sub(r"\s*\(출처:\s*\[\d+\]\)\s*", "", text)
    return text.strip()

def _normalize_items_for_list(items, limit=2):
    out=[]
    for x in (items or []):
        if x is None: continue
        if isinstance(x,str): s=x.strip()
        elif isinstance(x,dict): s=str(x.get("text") or x.get("summary") or x.get("description") or "").strip()
        else: s=str(x).strip()
        if not s or s.upper()=="NULL": continue
        out.append(s)
        if len(out)>=limit: break
    return out

def _html_list(items):
    norm=[_clean_citations(s) for s in _normalize_items_for_list(items, limit=2)]
    if not norm: return "<ul></ul>"
    safe="".join([f"<li>{html.escape(s)}</li>" for s in norm])
    return f"<ul>{safe}</ul>"

def _take2(items):
    return [_clean_citations(s) for s in _normalize_items_for_list(items, limit=2)]

# ---------------------- 렌더러 ----------------------
def render_pest_only(PEST):
    H3("PEST")
    st.markdown(f"""
<div class="grid-2-equal">
  <div class="quad"><h4>P (정치/제도)</h4>{_html_list((PEST or {}).get("P"))}</div>
  <div class="quad"><h4>E (경제/시장)</h4>{_html_list((PEST or {}).get("E"))}</div>
  <div class="quad"><h4>S (사회/문화)</h4>{_html_list((PEST or {}).get("S"))}</div>
  <div class="quad"><h4>T (기술/인프라)</h4>{_html_list((PEST or {}).get("T"))}</div>
</div>
""", unsafe_allow_html=True)

def render_swot_only(SWOT):
    H3("SWOT")
    st.markdown(f"""
<div class="grid-2-equal">
  <div class="quad"><h4>S (강점)</h4>{_html_list((SWOT or {}).get("S"))}</div>
  <div class="quad"><h4>W (약점)</h4>{_html_list((SWOT or {}).get("W"))}</div>
  <div class="quad"><h4>O (기회)</h4>{_html_list((SWOT or {}).get("O"))}</div>
  <div class="quad"><h4>T (위협)</h4>{_html_list((SWOT or {}).get("T"))}</div>
</div>
""", unsafe_allow_html=True)

def render_pest_swot_quadrants_from_dict(data: dict):
    H3("PEST · SWOT (4사분면)")
    render_pest_only(data.get("PEST", {}))
    render_swot_only(data.get("SWOT", {}))
    if data.get("one_liner"):
        H3("🎯 한 줄 대응전략")
        st.markdown(f'<div class="card-accent">{html.escape(_clean_citations(str(data.get("one_liner")).strip()))}</div>', unsafe_allow_html=True)

def render_pest_swot_quadrants(text: str):
    js = extract_json_str(text)
    if not js:
        st.warning("PEST·SWOT JSON 파싱에 실패했습니다."); st.code(text); return None
    try:
        data=json.loads(js)
    except Exception as e:
        st.warning(f"PEST·SWOT JSON 구문 오류: {e}"); st.code(text); return None
    render_pest_swot_quadrants_from_dict(data)
    st.download_button("⬇️ PEST·SWOT JSON 저장", data=js,
        file_name=f"pest_swot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", mime="application/json")
    return data
