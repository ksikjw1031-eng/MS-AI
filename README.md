# 💼 AX Biz Insight
**Azure 기반 외부·내부 데이터 통합 인사이트 시스템**

🔗 **[👉 앱 바로 실행하기 (Azure Web App)](https://proseinkim-102901.azurewebsites.net)**  

---

## 1. 프로젝트 개요

### **기획 목적**
> 기업의 기획·전략 담당자가 외부 환경 변화와 내부 데이터를 통합 분석하여  
> '**PEST·SWOT 분석, 인사이트 요약, 실행 전략 제안**'을 도출할 수 있도록 돕는  
> **내부 문서와 외부 뉴스를 결합한 전략 인사이트 자동화 시스템**입니다.

### **핵심 질문**
> “우리 회사는 어떤 외부 환경과 내부 역량 안에 있으며,   
> 이에 따라 어떤 전략적 대응을 해야 하는가?”

---

## 2. 주요 기능 요약

| 기능 구분 | 기능 설명 |
|------------|------------|
| 📰 **외부 뉴스 분석** | Naver/NewsAPI를 통해 기업·기술·도메인 관련 뉴스 수집 → Azure OpenAI(GPT-4.1-mini) 기반 PEST·SWOT 분석 |
| 📄 **내부 문서 분석** | Azure Blob Storage 업로드 → Azure AI Search로 색인 및 검색 → Azure OpenAI(GPT-4.1-mini) 기반 요약 및 강·약점 추출 |
| 💡 **통합 인사이트 생성** | 외부·내부 데이터를 교차 분석 → 벤치마킹·협력안·KPI 자동 제안 |
| 🎨 **Streamlit UI 시각화** | 탭 구조(문서요약 / SWOT / 전략제안) + KT 톤앤매너 카드형 시각화 |

---

## 3. 기술 아키텍처 (Architecture Overview)

### 전체 구조도
```text
사용자 (Streamlit UI)
        │
        ▼
 ┌─────────────── 외부 뉴스 파이프라인 ─────────────────┐
 │  NewsAPI / Naver → (전처리) → Azure OpenAI          │
 │     └ GPT-4.1-mini: PEST·SWOT(외부) JSON 생성       │
 └────────────────────────────────────────────────────┘
        │
        │  (병렬)
        ▼
 ┌─────────────── 내부 문서 파이프라인 ────────────────┐
 │  Blob Storage 업로드 → Azure AI Search(인덱싱/검색) │
 │     → Azure OpenAI                                 │
 │     └ GPT-4.1-mini: 문서 요약 및 내부 강·약점 생성   │
 └────────────────────────────────────────────────────┘
        │
        ▼
 [교차 분석 / 인사이트 엔진]
 - 외부(PEST·SWOT) + 내부 요약 결합
 - 벤치마킹·협력안·차별화·KPI 도출 (JSON)
        │
        ▼
 Streamlit App → 결과 탭 (문서요약 / 강점·약점 / 우선제안)


```
---

## 4. 시스템 동작 흐름 (System Workflow)

### (1) 외부 뉴스 분석
- **NewsAPI / Naver**를 통해 최신 뉴스 수집  
- **Azure OpenAI (GPT-4.1-mini)** 로 PEST·SWOT(외부) JSON 생성  


### (2) 내부 문서 분석
- 문서 업로드 → **Azure Blob Storage** 저장  
- **Azure AI Search** 인덱싱 및 **REST Search API** 호출  
- **GPT-4.1-mini** 로 내부 문서 요약 및 강·약점 생성  


### (3) 교차 분석 및 전략 도출
- 외부(PEST·SWOT) + 내부 요약 결합  
- **벤치마킹 · 협력안 · 차별화 · KPI** 자동 도출  


### (4) 결과 시각화 (Streamlit UI)
- 탭별로 결과 표시  
  → **외부 뉴스 / 내부 문서 / 통합 인사이트**

---


## 5. Azure 기술 활용 포인트
| 영역                    | 활용 포인트                                |
| --------------------- | ------------------------------------- |
| **데이터 관리**            | Blob Storage로 안전 저장 및 Key 인증          |
| **검색 구조 (AI Search)** | 문서 chunk 기반 색인 + 커스텀 검색 API              |
| **LLM 추론 (AOAI)**     | GPT-4.1-mini를 JSON 분석기로 활용       |
| **보안·환경 관리**          | `.env` 기반 Key 관리, 향후 Key Vault 연동 고려  |
| **확장성**               | Azure Function·App Service로 비동기 구조 확장이 가능 |


---


## 6. 최근 개선 내역 (Recent Enhancements)
| 구분                             | 개선 내용                                       | 효과                                   |
| -------------------------------- | ------------------------------------------- | ------------------------------------ |
| **Blob ↔ AI Search 자동 연동**  | 문서 업로드 시 Indexer 자동 실행 및 상태 폴링으로 처리         | 업로드 후 자동 분석 반영 → 사용자 조작 최소화          |
| **Azure OpenAI 기반 RAG 안정화** | AI Search 결과를 GPT-4.1-mini에 직접 Grounding    | PEST·SWOT·KPI 생성의 정확도 및 일관성 향상       |
| **자사 인식 AI 프롬프트 적용**        | `is_self_company()`로 KT DS 자사 여부 인식 및 문맥 제어 | “자사 대비 KT DS” 오류 제거 → 내부 관점 분석 품질 개선 |
| **통합 인사이트 페이지 완성**          | 외부 뉴스 + 내부 문서 데이터를 결합한 통합 분석 UI 구축          | SWOT + KPI + 전략 제안을 한 화면에서 시각화       |


---

## 7. 고도화 계획 (향후 발전 방향)

| 방향 | 내용 |
|------|------|
| 📊 **리포트 자동화** | 분석 결과를 **PDF / Word / Excel** 등 다양한 형식으로 자동 추출 |
| 📂 **문서 조회 확장** | **Word·Excel 원문 미리보기 및 요약 분석** 기능 추가 |
| ⚙️ **RAG On Your Data** | Office 문서 자동 인덱싱 및 **Azure Document Intelligence** 연동 |
| 🧩 **LangChain / LangGraph 고도화** | PEST → SWOT → KPI 단계별 **프롬프트 체인 구성**으로 분석 정밀도 향상 |
---

## 8. 프로젝트 핵심 요약 (Summary)

### 💡 핵심 구조
- **Azure Blob Storage** → 내부 문서 업로드 및 저장  
- **Azure AI Search** → 문서 인덱싱 및 검색  
- **Azure OpenAI (GPT-4.1-mini)** → 분석·요약·전략 생성  
- **Streamlit UI** → 결과 시각화 (문서요약 / 강점·약점 / 우선제안)


### 🚀 특징 및 확장성
- **Azure-native RAG 파이프라인**으로 Grounded 분석 수행  
- **모든 결과를 Streamlit UI에서 시각화**  
- **향후 On Your Data 및 LangChain 기반 분석 고도화 예정**



---

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
