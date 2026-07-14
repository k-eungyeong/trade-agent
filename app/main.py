from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from app.rag.chain import answer_question
import uuid
import json
from sqlalchemy.orm import Session
from app.db.database import engine, Base, get_db
from app.db.models import ChatSession, Message
from app.agent.reformat import reformat_answer

app = FastAPI(title="TradeAgent")
Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/health")
def health_check():
    return {"status": "ok"}

class ChatRequest(BaseModel):
    question: str
    session_id: str = None   # 없으면 새 세션 시작

@app.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    # 세션이 없으면 새로 생성
    session_id = request.session_id or str(uuid.uuid4())
    if not db.query(ChatSession).filter(ChatSession.id == session_id).first():
        db.add(ChatSession(id=session_id))
        db.commit()

    # 사용자 질문 저장
    db.add(Message(session_id=session_id, role="user", content=request.question, message_type="qna"))
    db.commit()

    # 답변 생성
    result = answer_question(request.question)

    # AI 답변 저장 (출처 정보는 JSON 문자열로 변환해서 저장)
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
    custom_instruction: str = None

@app.post("/reformat")
def reformat(request: ReformatRequest, db: Session = Depends(get_db)):
    result = reformat_answer(
        session_id=request.session_id,
        db=db,
        format_type=request.format_type,
        custom_instruction=request.custom_instruction
    )
    return {"reformatted_answer": result}