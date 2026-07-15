# TradeAgent

무역서류 기반 RAG + 요청 처리 에이전트

물류무역 관련 공개 자료(관세, 통관, 원산지증명, 인코텀즈 등)를 학습한 AI가
사용자의 질문에 답변하고, 답변을 받은 사용자가 이어서 요청하는 후속 작업
(재가공, 문서 초안 생성 등)까지 처리하는 RAG 기반 에이전트 웹 서비스

## 주요 기능

- 무역서류 기반 질의응답 (RAG)
- 이전 대화 맥락을 반영한 연속 질의응답
- 답변 재가공 (요약 / 표 / 불릿 변환)
- 문서 초안 생성 (원산지증명서 신청서 등 템플릿 기반)
- 대화 이력 저장 및 조회 (SQLite)

## 기술 스택

| 영역 | 기술 |
|---|---|
| 프론트엔드 | HTML, CSS, Vanilla JS |
| 백엔드 | FastAPI |
| RAG / 에이전트 | LangChain, Chroma |
| LLM / 임베딩 | Google Gemini API (gemini-flash-lite-latest, gemini-embedding-001) |
| 데이터베이스 | SQLite (SQLAlchemy) |
| 배포 | Render / Railway |

## 폴더 구조

```
trade-agent/
├── app/
│   ├── main.py                # FastAPI 진입점
│   ├── agent/                 # 요청 분류, 재가공(reformat), 문서초안 생성(draft)
│   │   ├── draft.py
│   │   └── reformat.py
│   ├── db/                    # SQLite 모델 및 세션 관리
│   │   ├── database.py
│   │   └── models.py
│   └── rag/                   # 문서 로딩, 청킹, 임베딩, 검색, RAG 체인
│       ├── chain.py
│       ├── embeddings.py
│       ├── loader.py
│       ├── pipeline.py
│       └── splitter.py
├── data/
│   ├── raw/                   # 원본 수집 자료 (16개)
│   ├── processed/             # 전처리 데이터 (예정)
│   ├── chroma_db/             # Chroma 벡터 저장소
│   └── trade_agent.db         # SQLite 대화 이력 DB
├── static/                    # 정적 파일 (채팅 UI)
├── tests/                     # 테스트 코드 (예정)
├── build_index.py             # data/raw/ 전체를 Chroma에 인덱싱하는 배치 스크립트
├── .env                       # 환경변수 (git 제외)
├── .env.example               # 환경변수 예시
├── requirements.txt
└── README.md

## 실행 방법

```bash
# 1. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 환경변수 설정 (.env 파일에 GEMINI_API_KEY 입력)
cp .env.example .env

# 4. 문서 인덱싱 (최초 1회, data/raw/ 전체를 Chroma에 저장)
python build_index.py

# 5. 서버 실행
uvicorn app.main:app --reload
```

## 개발 일정

- 1주차: 데이터 수집 + RAG 코어 구축
- 2주차: API 서버 + 요청 처리(재가공·문서초안) 기능
- 3주차: 프론트엔드 + 배포

## 자료 목록 (data/raw/)

**정리 문서 (11개)**
1. 원산지증명서_발급절차.md
2. 인코텀즈_2020_정리.md
3. 선하증권_BL_정리.md
4. 수출입_통관절차.md
5. HS코드_품목분류_기준.md
6. 상업송장_패킹리스트_정리.md
7. 신용장_LC_기초개념.md
8. 관세환급_제도.md
9. 무역계약_기본조항.md
10. AEO_제도.md
11. 관세_불복_이의신청_절차.md

**공식 서식 원본 (관세청 UNI-PASS, 5개)**
12. 원산지증명서_발급_재발급_정정발급_신청서.PDF
13. 원산지증명서_발급대장.PDF
14. 화면_설명_상세_-_신고서작성목록_FTA_.pdf
15. 화면_설명_상세_-_신고서작성목록_수입통관_.pdf
16. 화면_설명_상세_-_신고서작성목록_수출통관_.pdf

## 진행 상황

- [x] 무역서류 자료 수집 (16개)
- [x] RAG 파이프라인 구축 (로딩 → 청킹 → 임베딩 → 검색)
- [x] FastAPI 서버 구현 (/chat, /reformat, /draft)
- [x] 요청 분류 로직 (/ask 엔드포인트로 qna/reformat/draft 자동 분류)
- [x] 대화 이력 저장 및 맥락 반영 (SQLite)
- [ ] 프론트엔드 UI
- [ ] 배포

## 트러블슈팅 노트

- **Gemini 모델 세대교체 이슈**: 개발 중 Google이 2.5 시리즈 전체를 유료 전용으로 전환하면서,
  기존 모델(gemini-2.5-flash 등)이 신규 계정에서 404 에러로 막히는 상황을 겪음.
  특정 버전을 하드코딩하지 않고 `-latest` 별칭을 쓰되, 무료 티어 일일 한도가 모델마다
  크게 다르다는 점(gemini-flash-latest: 20회/일 vs gemini-flash-lite-latest: 훨씬 여유)을
  확인하고 요청 빈도가 높은 구조(분류+검색어재구성+답변생성)에 맞춰 flash-lite 계열로 전환.
- **RAG 검색의 대명사 처리 한계**: "방금 그거 요약해줘" 같은 질문은 LLM은 문맥을 이해해도
  벡터 검색 단계에서는 원문 그대로 비교되어 엉뚱한 문서가 검색되는 문제 발견.
  검색 전에 이전 대화를 참고해 질문을 완전한 형태로 재구성(query rewriting)하는 단계를
  추가해 해결.

## License

MIT
