"""
직전 답변을 다른 형식으로 재가공하는 기능
"""
from sqlalchemy.orm import Session
from app.db.models import Message
from app.rag.embeddings import client


def reformat_answer(session_id: str, db: Session, format_type: str = "custom", custom_instruction: str = None) -> str:
    """
    해당 세션의 가장 최근 assistant 답변을 찾아서, 지정된 형식으로 재가공

    format_type: "table" | "summary" | "bullet" | "custom"
    custom_instruction: format_type이 "custom"일 때 자연어 지시사항
    """
    # 1) 해당 세션의 가장 최근 assistant 메시지 조회
    last_answer = (
        db.query(Message)
        .filter(Message.session_id == session_id, Message.role == "assistant")
        .order_by(Message.id.desc())
        .first()
    )

    if not last_answer:
        return "재가공할 이전 답변을 찾을 수 없습니다."

    # 2) 형식별 지시사항 매핑
    format_instructions = {
        "table": "아래 내용을 마크다운 표 형식으로 재구성해줘.",
        "summary": "아래 내용을 핵심만 3줄로 요약해줘.",
        "bullet": "아래 내용을 불릿 포인트 목록으로 재구성해줘.",
        "custom": custom_instruction or "아래 내용을 더 읽기 쉽게 재구성해줘."
    }
    instruction = format_instructions.get(format_type, format_instructions["custom"])

    # 3) 프롬프트 구성 후 LLM 호출
    prompt = f"""{instruction}
내용의 사실관계는 절대 바꾸지 말고, 형식만 바꿔줘.

[원본 내용]
{last_answer.content}

[재구성된 결과]
"""

    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=prompt
    )

    return response.text