# pages/2_💡_통합_인사이트.py
import streamlit as st
import html
import json
import re
from datetime import datetime
import config  # config.py 임포트
import utils   # utils.py 임포트
from ui import H2, H3, _take2, _html_list  # ui.py 임포트

from ui import inject_css  # ⬅ 추가
inject_css()              # ⬅ 추가(초기화 직후면 어디든 OK)


# 세션 상태가 초기화되었는지 확인 (app.py를 먼저 실행해야 함)
if "news_results" not in st.session_state:
    config.initialize_session_state()

# ---------------------- 헬퍼: [D*]/[N*] 제거 + 중복 제거 ----------------------
def _dedup_strip_refs_list(items):
    """
    - [D1], [N23] 같은 근거 태그 제거
    - 공백/마침표/대소문자 차이는 무시하고 중복 제거
    - 원본 순서 유지
    """
    seen, out = set(), []
    for it in (items or []):
        s = str(it).strip()
        if not s:
            continue
        cleaned = re.sub(r"\[(?:D|N)\d+\]", "", s).strip()
        norm = re.sub(r"\s+", " ", cleaned).strip().rstrip(".").lower()
        if norm and norm not in seen:
            seen.add(norm)
            out.append(cleaned)
    return out

# ---------------------- 통합 인사이트 생성 버튼 ----------------------
col_ci1, col_ci2 = st.columns([1, 2])
with col_ci1:
    run_combined = st.button("💡 통합 인사이트 생성", use_container_width=True, key="btn_run_combined")
with col_ci2:
    st.caption("뉴스 검색 결과와 내부 문서 검색 결과가 모두 필요합니다.")

if run_combined:
    news_items = st.session_state.get("news_results", [])
    hits = st.session_state.get("doc_hits", [])

    # UI에서 현재 값 가져오기 (app.py에서 설정된 값)
    company = st.session_state.get("txt_company_custom", st.session_state.get("sel_company", ""))
    if company == "선택 안 함 (기술·도메인만)":
        company = ""
    techs = st.session_state.get("ms_techs", [])
    domains = st.session_state.get("ms_domains", [])

    if not news_items:
        st.warning("먼저 메인(홈) 페이지에서 '🔎 뉴스 검색'을 실행해 뉴스 근거를 준비하세요.")
    elif not hits:
        st.warning("먼저 '📄 내부 문서 분석' 페이지에서 문서를 조회해 근거를 준비하세요.")
    else:
        try:
            combined_json_text = utils.run_aoai(
                utils.build_messages_combined(news_items, hits, company, techs, domains)
            )
            st.session_state["combined_json"] = combined_json_text
            st.success("통합 인사이트 완료 ✅ (아래 결과 확인)")
        except Exception as e:
            st.error(f"생성 오류: {e}")

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

combined_data = utils.parse_json_from_session("combined_json") or {}
has_combined = bool(st.session_state.get("combined_json")) 

# ====================== 인사이트 섹션 (탭 UI: 항상 고정) ======================
combined_data = utils.parse_json_from_session("combined_json") or {}

# (옵션) 디버그 — 필요 없으면 삭제해도 됨
with st.expander("디버그: 통합 인사이트 원본 보기", expanded=False):
    raw = st.session_state.get("combined_json", None)
    st.write("raw type:", type(raw).__name__)
    if isinstance(raw, (str, bytes)):
        s = raw if len(raw) < 2000 else (raw[:2000] + "...")
        st.code(s, language="json")
    else:
        st.json(raw)
    st.write("parsed keys:", list(combined_data.keys()))

tab_sum, tab_sw, tab_prop = st.tabs(["📝 문서 요약", "💪 강점·약점", "🎯 우선 제안"])

# ── 탭1: 문서 요약 ───────────────────────────────────────────
with tab_sum:
    H3("문서 요약")

    if not has_combined:
        # 빈 상태(placeholder) — 버튼 누르기 전에도 탭이 보이도록
        st.markdown(
            '<div class="card-accent"><div class="box-title">내부 문서 요약</div>'
            '<p>결과가 아직 없습니다. 상단에서 <b>💡 통합 인사이트 생성</b>을 실행하세요.</p>'
            '</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="card-accent"><div class="box-title">외부(뉴스) 요약</div>'
            '<p>결과가 아직 없습니다. 뉴스 검색 결과와 내부 문서 검색 결과가 필요합니다.</p>'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        # 내부 요약
        inner = _take2(combined_data.get("internal_summary"))
        if inner:
            st.markdown(
                f'<div class="card-accent"><div class="box-title">내부 문서 요약</div>{_html_list(inner)}</div>',
                unsafe_allow_html=True
            )

        # 외부/뉴스 요약 (후보 키 스캔)
        outer_candidates = [
            combined_data.get("news_summary"),
            combined_data.get("external_summary"),
            combined_data.get("summary_from_news"),
            combined_data.get("summary_external"),
            combined_data.get("external_insights"),
        ]
        outer = []
        for c in outer_candidates:
            got = _take2(c)
            if got:
                outer.extend(got)
        if outer:
            st.markdown(
                f'<div class="card-accent"><div class="box-title">외부(뉴스) 요약</div>{_html_list(outer)}</div>',
                unsafe_allow_html=True
            )
        if not (inner or outer):
            st.caption("내부/외부 요약이 여기에 표시됩니다. 먼저 '💡 통합 인사이트 생성'을 실행하세요.")

# ── 탭2: 강점·약점 ───────────────────────────────────────────
with tab_sw:
    H3("강점·약점")
    if not has_combined:
        # 대시보드와 동일한 레이아웃의 빈 타일
        st.markdown(
            '<div class="grid-2-equal">'
            '<div class="quad"><h4>S (강점)</h4><ul><li>결과가 준비되면 여기에 표시됩니다.</li></ul></div>'
            '<div class="quad"><h4>W (약점)</h4><ul><li>결과가 준비되면 여기에 표시됩니다.</li></ul></div>'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        strengths = _take2(combined_data.get("strengths"))
        weaknesses = _take2(combined_data.get("weaknesses"))
        integ = combined_data.get("integrated_insights") or {}
        strengths_ext = _take2(integ.get("strengths")) or _take2(integ.get("강점"))
        weaknesses_ext = _take2(integ.get("weaknesses")) or _take2(integ.get("약점"))
        strengths_all = _dedup_strip_refs_list((strengths or []) + (strengths_ext or []))
        weaknesses_all = _dedup_strip_refs_list((weaknesses or []) + (weaknesses_ext or []))

        st.markdown(
            '<div class="grid-2-equal">'
            f'<div class="quad"><h4>S (강점)</h4>{_html_list(strengths_all or [""])}</div>'
            f'<div class="quad"><h4>W (약점)</h4>{_html_list(weaknesses_all or [""])}</div>'
            '</div>',
            unsafe_allow_html=True
        )

# ── 탭3: 우선 제안 ───────────────────────────────────────────
with tab_prop:
    H3("우선 제안")
    if not has_combined:
        st.markdown(
            '<div class="card-accent"><div class="box-title">우선 제안</div>'
            '<p>결과가 아직 없습니다. 상단의 <b>💡 통합 인사이트 생성</b>을 실행하면 내용이 표시됩니다.</p>'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        proposals = (combined_data.get("proposals") or {})
        insights = (combined_data.get("integrated_insights") or {})

        choice, one_summary = utils.choose_single_proposal(proposals, _take2_func=_take2)
        if not one_summary:
            candidates = []
            candidates += _take2(proposals.get("priorities"))
            candidates += _take2(proposals.get("priority_suggestions"))
            candidates += _take2(proposals.get("우선제안"))
            candidates += _take2(proposals.get("differentiation"))
            candidates += _take2(proposals.get("cooperation"))
            candidates += _take2(proposals.get("benchmarking"))
            candidates += _take2(insights.get("priorities"))
            candidates += _take2(insights.get("priority_suggestions"))
            candidates += _take2(insights.get("우선제안"))
            for k in ["cooperation", "benchmarking", "differentiation", "협력안", "벤치마킹", "차별화"]:
                candidates += _take2(insights.get(k))
            one_summary = candidates
            if not choice:
                choice = "cooperation"

        one_summary = _dedup_strip_refs_list(one_summary)

        if one_summary:
            label_map = {"benchmarking": "벤치마킹", "cooperation": "협력안", "differentiation": "차별화"}
            label = label_map.get(choice, "우선 제안")
            joined = "<br>".join([html.escape(l.strip()) for l in one_summary if l])
            st.markdown(
                f'<div class="card-accent"><div class="box-title">우선 제안: {html.escape(label)}</div>{joined}</div>',
                unsafe_allow_html=True
            )
        else:
            st.caption("우선 제안(협력안/벤치마킹/차별화)이 아직 없습니다.")