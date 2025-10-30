# 💼 AX Biz Insight
**Azure 기반 외부·내부 데이터 통합 인사이트 시스템**

🔗 **[👉 앱 바로 실행하기 (Azure Web App)](https://proseinkim-102901.azurewebsites.net)**  

---

## 1. 프로젝트 개요

### **프로젝트명**
> AX Biz Insight  
> Azure AI 기반 외부·내부 데이터 통합 전략 분석 플랫폼  

### **기획 목적**
> 기업의 기획·전략 담당자가  
> 외부 환경 변화와 내부 문서 데이터를 통합적으로 분석하여  
> 신속하게 **PEST·SWOT 분석, 인사이트 요약, 실행 전략 제안**을 도출할 수 있도록 하는  
> **Azure AI 기반 전략 의사결정 지원 플랫폼**을 구축하는 것.

### **핵심 질문**
> “우리 회사는 어떤 외부 환경과 내부 역량 안에 있으며,   
> 이에 따라 어떤 전략적 대응을 해야 하는가?”

---
<br>

## 2. 주요 기능 요약

| 기능 구분 | 기능 설명 |
|------------|------------|
| 📰 **외부 뉴스 분석** | Naver/NewsAPI를 통해 기업·기술·도메인 관련 뉴스 수집 → AOAI (GPT-4.1-mini) 기반 PEST·SWOT 분석 |
| 📄 **내부 문서 분석** | Azure Blob Storage 업로드 → Azure AI Search로 색인 및 검색 → AOAI (GPT-4.1-mini) 요약 및 강점·약점 추출 |
| 💡 **통합 인사이트 생성** | 외부 뉴스 + 내부 문서를 교차 분석하여 강·약점 및 협력안·차별화·벤치마킹 제안, KPI 도출 |
| 🎨 **Streamlit UI 시각화** | 탭 구조(문서요약 / 강점·약점 / 우선제안) + KT 톤앤매너의 카드형 UI |
| ⚙️ **캐싱·세션 관리** | `st.cache_data`, `st.session_state`로 성능·상태 안정화 |

---
<br>

## 3. 기술 아키텍처

### 전체 구조도
```text
사용자 (Streamlit UI)
     │
     ▼
Azure Blob Storage ──> 문서 업로드
     │
     ▼
Azure AI Search ──> 문서 색인 및 검색 (/docs/search API)
     │
     ▼
Azure OpenAI Service (AOAI)
     └ GPT-4.1-mini 모델로 분석·요약·전략 생성
     │
     ▼
Streamlit App ──> 결과 탭(문서요약 / 강점·약점 / 우선제안)
```
<br>

##  4. 주요 기술 구성 요소

| 구성 요소 | 역할 | 특징 |
|------------|------|------|
| **Azure Blob Storage** | 내부 문서 업로드 및 저장 | 기업 내부 문서 자산 관리 |
| **Azure AI Search** | 문서 색인 및 검색 | `/docs/search` API 직접 호출, RAG 커스텀 구현 |
| **Azure OpenAI (AOAI)** | GPT-4.1-mini 모델로 분석·전략 생성 | JSON 기반 구조화 응답 |
| **Streamlit** | 웹 인터페이스 및 시각화 | 카드형 UI, 멀티탭 구조 |
| **NewsAPI / Naver API** | 외부 뉴스 데이터 수집 | 한글 뉴스 중심 |
| **Python SDK / OpenAI SDK** | AOAI 호출 및 JSON 파싱 | 구조화 응답(JSON 스키마) 기반 |

---
<br>

## 5. 시스템 동작 구조 요약

### ① 내부 문서 분석
➡️ Streamlit에서 PDF 업로드 → Azure Blob에 저장  
➡️ Azure AI Search 인덱서가 해당 Blob의 PDF를 색인  
➡️ Streamlit이 `/docs/search` API 호출 → `content` 필드로 본문 조회  
➡️ AOAI(GPT-4.1-mini)가 문서 요약 및 강점·약점 생성  

> 💡 On Your Data 없이 RAG 구조를 직접 구현한 **Grounded Response**

---

### ② 외부 뉴스 분석
➡️ Naver News / NewsAPI로 최신 뉴스 수집  
➡️ AOAI에 “PEST·SWOT JSON 스키마”를 프롬프트로 지정  
➡️ GPT가 JSON 형태로 분석 결과(P,E,S,T / S,W,O,T + KPI) 반환  
➡️ Streamlit UI에서 **PEST·SWOT·대응전략 카드**로 시각화  

---

### ③ 통합 인사이트 생성
➡️ 뉴스 + 내부문서를 AOAI에 함께 전달 → 교차 분석 수행  
➡️ “내부 요약 + 외부 인사이트 + 강·약점 + 협력안·차별화·벤치마킹 제안 + KPI”를 JSON으로 생성  
➡️ Streamlit 탭에 시각화 표시  

---
<br>

## 6. Azure 기술 활용 의도 

| 관점 | 설명 |
|------|------|
| **데이터 관리** | Blob Storage를 통해 문서를 안전 저장, Key 인증으로 접근 제어 |
| **지식 검색 (AI Search)** | “On Your Data” 대신 `/docs/search` API를 직접 호출해 RAG 구조 구현 |
| **LLM 추론 (AOAI)** | Azure OpenAI GPT-4.1-mini 모델로 JSON 구조화 결과 생성 |
| **보안·환경 관리** | `.env` 파일을 통해 모든 키 안전 관리 |
| **확장성** | Azure Function / App Service 기반 확장 가능 구조 설계 |

---
<br>

## 7. 발표 포인트

| 포인트 | 발표 시 강조 문장 예시 |
|---------|--------------------------|
| **기술 연동 의도** | “Azure AI Search의 검색 결과를 AOAI가 직접 받아 Grounded Response를 생성하도록 설계했습니다.” |
| **보안 관리** | “모든 Key는 환경변수로 관리되며 Azure Key Vault 연동도 가능합니다.” |
| **확장성 강조** | “현재는 Streamlit MVP지만, Azure Functions로 비동기 구조 확장도 고려했습니다.” |
| **AOAI 활용 수준** | “AOAI를 단순 응답형이 아닌, JSON 구조화 분석기로 사용했습니다.” |
| **실무 가치** | “기업 내부 문서 + 외부 시장 데이터를 결합한 전략 분석을 자동화했습니다.” |

---
<br>

## 8. 고도화 계획 (향후 발전 방향)

| 방향 | 내용 |
|------|------|
| **RAG(On Your Data)** | Word/PPT/Excel 등 Office 포맷 자동 인덱싱 및 Document Intelligence 연계 |
| **LangGraph / LangChain 도입** | PEST → SWOT → KPI 단계별 프롬프트 체인 구성 |
| **리포트 자동화** | 분석 결과를 PDF/PPT 보고서 형태로 자동 생성 |
| **속도·확장성 개선** | Streamlit → FastAPI 구조 분리, Azure Cache 도입 |
| **품질 관리** | Langfuse로 프롬프트 품질 추적 및 버전 관리 |

---
<br>

## 9. 발표용 요약 문단

> 본 프로젝트는 **Azure AI 생태계**를 기반으로  
> 외부 뉴스와 내부 문서를 통합 분석하여  
> 기업의 **PEST·SWOT 및 전략 인사이트**를 자동 생성하는 AI 시스템입니다.  
> Blob Storage → AI Search → AOAI까지 완전한 **Azure-native 파이프라인**을 구성하였으며,  
> RAG 구조를 직접 구현하여 GPT 모델이 **Grounded된 분석**을 수행합니다.  
> 모든 결과는 **Streamlit UI**에서 시각화되며,  
> 향후 **On Your Data / LangChain 기반 분석 고도화**로 확장할 예정입니다.

---
<br>

## 10. 실행 안내

### 🗂️ 폴더 구조
```text
grounded-pest-app/
├── 0_💼_AX_Biz_Insight.py     # 메인 대시보드 (PEST·SWOT·전략 탭)
├── pages/
│   ├── 1_📄_내부_문서_분석.py  # 내부문서 업로드 및 Azure Search 조회
│   └── 2_💡_통합_인사이트.py  # 뉴스+문서 기반 통합 분석
├── ui.py / utils.py / config.py
├── requirements.txt
├── .env.example
└── README.md
