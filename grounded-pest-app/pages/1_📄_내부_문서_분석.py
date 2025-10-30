# 업로드 후 자동 조회(폴링) 관련 설정
POLL_TRIES = 10       # 재시도 횟수 (기본 10회 ≈ 최대 30초)
POLL_INTERVAL = 3     # 재시도 간격(초)

# pages/1_📄_내부_문서_분석.py
import streamlit as st
import requests, uuid
import config, utils
from ui import H2, H3, _clean_citations

# ====================== 세션 기본값 ======================
if "doc_hits" not in st.session_state:
    st.session_state["doc_hits"] = []
if "last_blob_name" not in st.session_state:
    st.session_state["last_blob_name"] = ""

# ---------------------- 헬퍼: rerun/초기화 ----------------------
def _rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

def _clear_analysis_state():
    for k in ("doc_hits", "last_blob_name"):
        st.session_state.pop(k, None)
    for k in ("news_results", "pest_swot_json", "combined_json", "pdf_sig"):
        st.session_state.pop(k, None)
    st.cache_data.clear()
    st.cache_resource.clear()

# -------------------------------------------------------------------
# 유틸: 인덱서 상태 조회 (고급 기능)
# -------------------------------------------------------------------
def _get_indexer_status():
    try:
        url = f"{config.SEARCH_ENDPOINT}/indexers/{config.SEARCH_INDEXER}/status?api-version={config.SEARCH_API_VER}"
        r = requests.get(url, headers={"api-key": config.SEARCH_KEY}, timeout=20)
        r.raise_for_status()
        return r.json() or {}
    except Exception as e:
        st.error(f"상태 조회 실패: {e}")
        return {}

# -------------------------------------------------------------------
# 헤더

# -------------------------------------------------------------------
# 1) PDF 업로드 (Blob만)
# -------------------------------------------------------------------
st.subheader("📄 내부 문서 업로드")
st.caption("내가 업로드한 PDF 파일의 내용을 AI가 검색해 보여줍니다.")

upload_file = st.file_uploader("PDF 파일 선택", type=["pdf"], key="pdf_upload_for_blob")

col_up = st.columns([1, 1, 2])
with col_up[0]:
    # 🔻 운영 UX에선 숨기는 게 깔끔 — 고급 Expander로 이동
    pass

with col_up[1]:
    auto_fetch = st.checkbox("업로드 후 자동 조회", value=True, help="업로드가 성공하면 해당 파일 기준으로 바로 인덱스 검색")

with col_up[2]:
    last = st.session_state.get("last_blob_name")
    st.info(f"최근 업로드: `{last}`" if last else "최근 업로드: (없음)")

# 업로드 실행
if st.button("⬆️ 업로드 실행", use_container_width=True, key="btn_blob_upload"):
    if not upload_file:
        st.warning("파일을 먼저 선택하세요.")
    elif not config.blob_container:
        st.error("Blob 컨테이너 연결 실패. .env의 AZURE_STORAGE_CONN 확인.")
    else:
        try:
            import time, uuid
            blob_name = f"{uuid.uuid4()}_{upload_file.name}"
            upload_file.seek(0)
            config.blob_container.upload_blob(name=blob_name, data=upload_file, overwrite=True)
            st.session_state["last_blob_name"] = blob_name
            st.success(f"✅ 업로드 완료: {blob_name}")

            if auto_fetch:
                # 화면엔 스피너만 보이게
                with st.spinner("📄 인덱싱 반영 중입니다... 잠시만 기다려주세요."):
                    hits = []
                    delays = [2, 3, 5, 8, 13, 21]
                    for i, wait in enumerate(delays, start=1):
                        st.cache_data.clear()
                        try:
                            hits = utils.search_docs_by_blobname(st.session_state["last_blob_name"], top=10, nonce=i)
                        except TypeError:
                            hits = utils.search_docs_by_blobname(st.session_state["last_blob_name"], top=10)

                        if hits:
                            break

                        if i in (2, 3) and config.SEARCH_INDEXER:
                            try:
                                run_url = f"{config.SEARCH_ENDPOINT}/indexers/{config.SEARCH_INDEXER}/run?api-version={config.SEARCH_API_VER}"
                                requests.post(run_url, headers={"api-key": config.SEARCH_KEY}, timeout=10)
                            except Exception:
                                pass

                        time.sleep(wait)

                if hits:
                    st.session_state["doc_hits"] = hits
                    st.success(f"✅ 인덱싱 반영 완료! 문서 조각 {len(hits)}건")
                    st.toast(f"{len(hits)}건 로드됨")
                else:
                    st.session_state["doc_hits"] = []
                    st.warning("⚠️ 아직 인덱싱 대기 중입니다. 잠시 후 다시 시도하세요.")

        except Exception as e:
            st.error(f"업로드 오류: {e}")

# -------------------------------------------------------------------
# ⛔ 강제 재시작(Reset → Run) 후 내 파일 재조회  + 세션 초기화는 고급으로 이동
# -------------------------------------------------------------------
with st.expander("⚙️ 고급: 디버그/복구 도구", expanded=False):
    c1, c2 = st.columns(2)

    with c1:
        if st.button("🧹 세션 초기화 (앱 다시 시작)", use_container_width=True, key="btn_reset_pdf_here"):
            _clear_analysis_state()
            _rerun()

    with c2:
        if st.button("⛔ 강제 재시작(Reset→Run) 후 재조회", use_container_width=True, key="btn_force_reset_run"):
            last = st.session_state.get("last_blob_name", "")
            if not last:
                st.warning("먼저 PDF를 업로드하세요.")
            elif not (config.SEARCH_ENDPOINT and config.SEARCH_INDEXER and config.SEARCH_KEY and config.SEARCH_API_VER):
                st.error("Azure Search 설정(ENDPOINT/INDEXER/KEY/API_VER)이 누락되었습니다.")
            else:
                import time, requests
                try:
                    headers = {"api-key": config.SEARCH_KEY}
                    base = f"{config.SEARCH_ENDPOINT}/indexers/{config.SEARCH_INDEXER}"

                    # Reset → Run
                    r_reset = requests.post(f"{base}/reset?api-version={config.SEARCH_API_VER}", headers=headers, timeout=20)
                    if r_reset.status_code not in (204, 202):
                        st.warning(f"Reset 응답: {r_reset.status_code} {r_reset.text}")

                    r_run = requests.post(f"{base}/run?api-version={config.SEARCH_API_VER}", headers=headers, timeout=20)
                    if r_run.status_code not in (202, 204):
                        st.warning(f"Run 응답: {r_run.status_code} {r_run.text}")

                    with st.spinner("📄 인덱싱 반영 대기 중..."):
                        found = []
                        for i in range(12):   # 최대 ~36초
                            st.cache_data.clear()
                            try:
                                found = utils.search_docs_by_blobname(last, top=10, nonce=i)
                            except TypeError:
                                found = utils.search_docs_by_blobname(last, top=10)
                            if found:
                                break
                            time.sleep(3)

                    if found:
                        st.session_state["doc_hits"] = found
                        st.success(f"✅ 인덱싱 반영됨: 조각 {len(found)}건")
                        st.toast("요약 영역을 아래에서 확인하세요.")
                    else:
                        st.info("아직 반영되지 않았습니다. 잠시 후 다시 눌러보세요.")
                except Exception as e:
                    st.error(f"강제 재시작 실패: {e}")

    st.markdown("---")
    if st.button("🏃 인덱서 수동 실행", use_container_width=True, disabled=not config.SEARCH_INDEXER):
        try:
            run_url = f"{config.SEARCH_ENDPOINT}/indexers/{config.SEARCH_INDEXER}/run?api-version={config.SEARCH_API_VER}"
            r = requests.post(run_url, headers={"api-key": config.SEARCH_KEY}, timeout=20)
            if r.status_code == 202:
                st.success("✅ 실행 트리거 성공")
            elif r.status_code == 409:
                st.warning("⚠️ 이미 실행 중(409). 잠시 후 상태 확인하세요.")
            else:
                st.error(f"❌ 실패: {r.status_code} {r.text}")
        except Exception as e:
            st.error(f"실행 오류: {e}")

    if st.button("🔎 인덱서 상태 확인", use_container_width=True, disabled=not config.SEARCH_INDEXER):
        s = _get_indexer_status()
        top = (s.get("status") or "").lower()
        last = s.get("lastResult") or {}
        st.info(f"service={top} · last={ (last.get('status') or '').lower() }")
        with st.expander("원본 상태 JSON 보기"):
            st.json(s)

st.divider()

# -------------------------------------------------------------------
# 3) 인덱스에서 문서 가져오기 (키워드)
# -------------------------------------------------------------------
st.subheader("📄 업로드한 문서에서 찾기")
st.caption("내가 업로드한 PDF 파일의 내용을 AI가 검색해 보여줍니다.")
q_doc = st.text_input("키워드로 검색", value="", placeholder="예: 보안 요구사항, KPI, 제안서 요약", key="txt_q_doc")

if st.button("⬆️ 키워드 검색", use_container_width=True, key="btn_fetch_by_kw"):
    query = (q_doc or "").strip()
    if not query:
        st.warning("검색어를 입력하세요.")
    else:
        hits = utils.search_docs_by_keyword(query, top=8)
        st.session_state["doc_hits"] = hits
        st.success(f"키워드 검색 결과 {len(hits)}건")

st.divider()

# -------------------------------------------------------------------
# 4) 내부 문서 검색 결과 (요약 1건)
# -------------------------------------------------------------------
doc_hits = st.session_state.get("doc_hits") or []
H3("📚 내부 문서 검색 결과 (통합 요약 1건)")
if not doc_hits:
    st.caption("아직 검색된 문서가 없습니다. 업로드 후 자동 조회 또는 '키워드 검색'을 실행하세요.")
else:
    top_titles = [(h.get("title") or "(제목 없음)") for h in doc_hits[:3] if isinstance(h, dict)]
    if top_titles:
        st.caption("대표: " + " | ".join(top_titles))

    safe_hits = [h for h in doc_hits if isinstance(h, dict)]
    try:
        summary = utils.summarize_docs_combined(safe_hits, max_chars=20000)
        st.write(_clean_citations(str(summary).strip()))
    except Exception as e:
        st.warning(f"요약 실패 → 일부만 표시 ({e})")
        merged = "".join([(h.get("content") or "") for h in safe_hits])[:600]
        st.write(_clean_citations(merged + ("…" if len(merged) >= 600 else "")))

    with st.expander("조각별 원문 일부 보기"):
        for i, h in enumerate(safe_hits, 1):
            st.markdown(f"**[{i}] {h.get('title') or '(제목 없음)'}**")
            if h.get("source"):
                st.caption(h["source"])
            content_text = h.get("content") or ""
            if not isinstance(content_text, str):
                content_text = str(content_text or "")
            st.write(_clean_citations(content_text[:800] + ("…" if len(content_text) > 800 else "")))
            st.markdown("---")
