from fastapi import FastAPI, Depends
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from app.rag.chain import answer_question
import uuid
import json
from sqlalchemy.orm import Session
from app.db.database import engine, Base, get_db
from app.db.models import ChatSession, Message
from app.agent.reformat import reformat_answer
from app.agent.draft import generate_draft, TEMPLATES
from app.db.models import GeneratedDocument
from app.agent.classifier import classify_request
from app.agent.draft import extract_values_from_message, check_missing_fields
from typing import Optional


app = FastAPI(title="TradeAgent")
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 단계에서는 전체 허용, 배포 시 실제 도메인으로 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/health")
def health_check():
    return {"status": "ok"}

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

@app.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    session_id = request.session_id or str(uuid.uuid4())
    if not db.query(ChatSession).filter(ChatSession.id == session_id).first():
        db.add(ChatSession(id=session_id))
        db.commit()

    # 이 세션의 최근 대화 4개(질문+답변 2턴 정도)를 시간순으로 조회
    recent_messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.id.desc())
        .limit(4)
        .all()
    )
    recent_messages.reverse()  # 오래된 순서로 다시 정렬
    history = [{"role": m.role, "content": m.content} for m in recent_messages]

    db.add(Message(session_id=session_id, role="user", content=request.question, message_type="qna"))
    db.commit()

    # history를 함께 전달
    result = answer_question(request.question, history=history)

    db.add(Message(
        session_id=session_id,
        role="assistant",
        content=result["answer"],
        message_type="qna",
        source_chunks=json.dumps(result["sources"], ensure_ascii=False)
    ))
    db.commit()

    return {**result, "session_id": session_id}

class ReformatRequest(BaseModel):
    session_id: str
    format_type: str = "custom"
    custom_instruction: Optional[str] = None

@app.post("/reformat")
def reformat(request: ReformatRequest, db: Session = Depends(get_db)):
    result = reformat_answer(
        session_id=request.session_id,
        db=db,
        format_type=request.format_type,
        custom_instruction=request.custom_instruction
    )
    return {"reformatted_answer": result}

class DraftRequest(BaseModel):
    session_id: str
    template_type: str
    values: dict

@app.post("/draft")
def draft(request: DraftRequest, db: Session = Depends(get_db)):
    result = generate_draft(request.template_type, request.values)

    # 생성된 초안을 DB에 저장
    doc = GeneratedDocument(
        session_id=request.session_id,
        template_type=request.template_type,
        output_content=result
    )
    db.add(doc)
    db.commit()

    return {"draft": result}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"예상치 못한 에러 발생: {exc}")
    return JSONResponse(
        status_code=500,
        content={"answer": "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.", "sources": [], "session_id": None}
    )

class AskRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None

@app.post("/ask")
def ask(request: AskRequest, db: Session = Depends(get_db)):
    session_id = request.session_id or str(uuid.uuid4())
    if not db.query(ChatSession).filter(ChatSession.id == session_id).first():
        db.add(ChatSession(id=session_id))
        db.commit()

    recent_messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.id.desc())
        .limit(4)
        .all()
    )
    recent_messages.reverse()
    history = [{"role": m.role, "content": m.content} for m in recent_messages]

    db.add(Message(session_id=session_id, role="user", content=request.message, message_type="qna"))
    db.commit()

    # 1) 요청 분류
    classification = classify_request(request.message, history)
    req_type = classification.get("type", "qna")

    # 2) 분류 결과에 따라 분기 처리
    if req_type == "reformat":
        answer_text = reformat_answer(
            session_id=session_id,
            db=db,
            format_type=classification.get("format_type") or "custom",
            custom_instruction=request.message
        )
        result = {"answer": answer_text, "sources": []}

    elif req_type == "draft":
        template_type = classification.get("template_type")
        if not template_type or template_type not in TEMPLATES:
            result = {"answer": f"어떤 양식의 문서를 작성할지 확인이 필요합니다. 지원 양식: {list(TEMPLATES.keys())}", "sources": []}
        else:
            values = extract_values_from_message(request.message, template_type, history)
            missing = check_missing_fields(template_type, values)
            if missing:
                result = {"answer": f"문서 작성을 위해 아래 정보가 더 필요합니다: {', '.join(missing)}", "sources": []}
            else:
                draft_text = generate_draft(template_type, values)
                result = {"answer": draft_text, "sources": []}
                db.add(GeneratedDocument(session_id=session_id, template_type=template_type, output_content=draft_text))
                db.commit()

    else:  # qna
        result = answer_question(request.message, history=history)

    db.add(Message(
        session_id=session_id,
        role="assistant",
        content=result["answer"],
        message_type=req_type,
        source_chunks=json.dumps(result.get("sources", []), ensure_ascii=False)
    ))
    db.commit()

    return {**result, "session_id": session_id, "request_type": req_type}