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
| ⚙️  **성능/안정** | `st.cache_data`, `st.session_state` 기반 캐싱/상태관리 |

---
<br>

## 3️. 기술 아키텍처

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

---
<br>

## 4. 시스템 동작 흐름
```text
① 내부 문서 업로드 → Blob 저장  
② Azure AI Search 인덱싱 및 /docs/search API 조회  
③ 외부 뉴스 수집 (NewsAPI/Naver API)  
④ AOAI가 뉴스+문서 기반으로 JSON 분석 (PEST·SWOT·KPI)  
⑤ Streamlit UI에 카드형으로 시각화 (문서요약 / 강점·약점 / 우선제안)
```

---

<br>

## 5. Azure 기술 활용 의도
| 영역                    | 활용 포인트                                |
| --------------------- | ------------------------------------- |
| **데이터 관리**            | Blob Storage로 안전 저장 + Key 인증          |
| **검색 구조 (AI Search)** | 커스텀 API 호출로 검색 결과를 직접 제어              |
| **LLM 추론 (AOAI)**     | GPT-4.1-mini로 JSON 구조화된 인사이트 생성       |
| **보안·환경 관리**          | `.env` 기반 Key 관리, 향후 Key Vault 연동 고려  |
| **확장성**               | Azure Function·App Service로 확장 가능한 구조 |


---

<br>

## 6. 핵심 포인트
| 관점            | 강조 문장                                                   |
| ------------- | ------------------------------------------------------- |
| **기술 연동**     | AI Search의 검색 결과를 AOAI가 직접 Grounded Response로 활용 |
| **LLM 활용 수준** | AOAI를 단순 응답형이 아닌 JSON 구조화 분석기로 사용                |
| **확장성**       | 현재 Streamlit MVP지만, Functions로 비동기 구조 확장이 가능      |
| **실무 가치**     | 내부 문서와 외부 뉴스를 결합한 전략 인사이트 자동화 시스템                 |

---

<br>

## 7. 고도화 계획 (향후 발전 방향)

| 방향 | 내용 |
|------|------|
| **RAG(On Your Data)** | Word/PPT/Excel 등 Office 포맷 자동 인덱싱 및 Document Intelligence 연계 |
| **LangGraph / LangChain 도입** | PEST → SWOT → KPI 단계별 프롬프트 체인 구성 |
| **리포트 자동화** | 분석 결과를 PDF/PPT 보고서 형태로 자동 생성 |
| **속도·확장성 개선** | Streamlit → FastAPI 구조 분리, Azure Cache 도입 |
| **품질 관리** | Langfuse로 프롬프트 품질 추적 및 버전 관리 |

---
<br>

## 8. 프로젝트 핵심 요약 (Summary)

본 프로젝트는 **Azure AI 생태계**를 기반으로  
외부 뉴스와 내부 문서를 통합 분석하여  
기업의 **PEST·SWOT 및 전략 인사이트**를 자동 생성하는 **AI 시스템**입니다.  

**Azure Blob Storage → Azure AI Search → Azure OpenAI(AOAI)** 까지  
완전한 **Azure-native 파이프라인**을 구성하였으며,  
직접 **RAG 구조를 구현**해 GPT 모델이 **Grounded된 분석**을 수행합니다.  

모든 결과는 **Streamlit UI**에서 시각화되며,  
향후 **On Your Data** 및 **LangChain 기반 분석 고도화**로 확장할 예정입니다.


---
<br>

## 9. 실행 안내

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
