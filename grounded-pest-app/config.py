# config.py
import os
import streamlit as st
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드 (로컬 테스트용)
try:
    load_dotenv()
except Exception:
    pass

# --- API 키 및 엔드포인트 ---
NEWS_KEY = os.getenv("NEWSAPI_KEY")
NAVER_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_SECRET = os.getenv("NAVER_CLIENT_SECRET")

AOAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AOAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AOAI_VER = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
AOAI_DEPLOY = os.getenv("AZURE_OPENAI_DEPLOYMENT")

STORAGE_CONN = os.getenv("AZURE_STORAGE_CONN")
BLOB_CONTAINER_NAME = os.getenv("AZURE_BLOB_CONTAINER", "docs")

SEARCH_ENDPOINT = (os.getenv("AZURE_SEARCH_ENDPOINT") or "").strip().rstrip("/")
SEARCH_KEY = (os.getenv("AZURE_SEARCH_KEY") or "").strip()
SEARCH_INDEX = (os.getenv("AZURE_SEARCH_INDEX") or "").strip()
SEARCH_INDEXER = (os.getenv("AZURE_SEARCH_INDEXER") or "").strip()
SEARCH_API_VER = os.getenv("AZURE_SEARCH_API_VERSION", "2023-11-01")

# --- Azure Blob 클라이언트 초기화 ---
@st.cache_resource
def get_blob_container():
    """Blob 컨테이너 클라이언트를 반환 (캐싱됨)"""
    if not STORAGE_CONN:
        return None
    try:
        blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONN)
        container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)
        return container_client
    except Exception as e:
        st.error(f"Blob 컨테이너 연결 실패: {e}")
        return None

blob_container = get_blob_container()

# --- 세션 상태 초기화 ---
def initialize_session_state():
    """모든 페이지에서 공통으로 사용할 세션 상태를 초기화합니다."""
    defaults = {
        "news_results": [],
        "doc_hits": [],
        "last_blob_name": "",
        "search_fieldmap": None,
        "pest_swot_json": None,
        "combined_json": None,
        "last_metrics": {}
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)
