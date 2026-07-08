# TradeAgent

무역서류 기반 RAG + 요청 처리 에이전트

물류무역 관련 공개 자료(관세, 통관, 원산지증명, 인코텀즈 등)를 학습한 AI가
사용자의 질문에 답변하고, 답변을 받은 사용자가 이어서 요청하는 후속 작업
(재가공, 문서 초안 생성 등)까지 처리하는 RAG 기반 에이전트 웹 서비스

## 주요 기능

- 무역서류 기반 질의응답 (RAG)
- 답변 재가공 (요약 / 표 / 체크리스트 변환)
- 문서 초안 생성 (원산지증명서 신청서 등 템플릿 기반)
- 대화 이력 저장 및 조회

## 기술 스택

| 영역 | 기술 |
|---|---|
| 프론트엔드 | HTML, CSS, Vanilla JS |
| 백엔드 | FastAPI |
| RAG / 에이전트 | LangChain, Chroma |
| LLM | OpenAI API |
| 데이터베이스 | SQLite |
| 배포 | Render / Railway |

## 폴더 구조

```
trade-agent/
├── app/
│   ├── main.py              # FastAPI 진입점
│   ├── rag/                 # 문서 로딩, 임베딩, 검색
│   ├── agent/                # 요청 분류, 재가공, 문서 생성
│   └── db/                   # SQLite 모델 및 CRUD
├── data/
│   ├── raw/                  # 원본 수집 자료
│   └── processed/            # 전처리된 텍스트
├── frontend/                 # 채팅 UI
└── tests/
```

## 실행 방법

```bash
# 1. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 환경변수 설정 (.env 파일에 OPENAI_API_KEY 입력)
cp .env.example .env

# 4. 서버 실행
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
- [ ] RAG 파이프라인 구축
- [ ] FastAPI 서버 구현
- [ ] 요청 분류 및 처리 로직
- [ ] 프론트엔드 UI
- [ ] 배포

## License

MIT
