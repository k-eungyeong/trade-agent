"""
대화 이력 및 생성 문서 저장을 위한 SQLAlchemy 모델
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base


class ChatSession(Base):
    """대화방(세션) 단위"""
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Message(Base):
    """개별 질문-답변 turn"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    role = Column(String)              # "user" 또는 "assistant"
    content = Column(Text)
    message_type = Column(String)      # "qna" | "reformat" | "draft"
    source_chunks = Column(Text)       # 참고한 출처 정보 (JSON 문자열로 저장)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class GeneratedDocument(Base):
    """문서초안 생성 결과 기록"""
    __tablename__ = "generated_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    message_id = Column(Integer, ForeignKey("messages.id"))
    template_type = Column(String)     # 어떤 양식 기반인지 (예: "원산지발급신청서")
    output_content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())