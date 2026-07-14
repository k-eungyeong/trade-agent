"""
사용자 요청이 질문(Q&A)인지, 재가공인지, 문서초안 생성인지 분류
"""
import json
from app.rag.embeddings import client
from app.agent.draft import TEMPLATES


def classify_request(message: str, history: list[dict] = None) -> dict:
    """
    사용자 메시지를 분석해서 요청 타입과 필요한 세부 정보를 함께 추출

    Returns:
        {"type": "qna" | "reformat" | "draft", ...추가 정보}
    """
    history_text = ""
    if history:
        lines = [f"{'사용자' if h['role'] == 'user' else 'AI'}: {h['content']}" for h in history]
        history_text = "\n".join(lines)

    template_names = list(TEMPLATES.keys())

    prompt = f"""아래 사용자 메시지를 분석해서, 세 가지 유형 중 하나로 분류해줘.

- "qna": 무역 지식에 대한 새로운 질문
- "reformat": 이전 답변을 표/요약/불릿 등 다른 형식으로 바꿔달라는 요청
- "draft": 신청서/문서 초안을 작성해달라는 요청 (지원 양식: {template_names})

[이전 대화]
{history_text if history_text else "(없음)"}

[사용자 메시지]
{message}

아래 JSON 형식으로만 답해줘 (다른 설명 붙이지 말고):
{{
  "type": "qna 또는 reformat 또는 draft",
  "format_type": "reformat일 경우 table/summary/bullet/custom 중 하나, 아니면 null",
  "template_type": "draft일 경우 해당 양식명({template_names}), 아니면 null"
}}
"""

    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=prompt
    )

    # LLM 응답에서 JSON 부분만 추출 (```json 같은 마크다운 코드블록 제거)
    text = response.text.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 분류 실패 시 기본값은 qna로 처리 (제일 안전한 fallback)
        return {"type": "qna", "format_type": None, "template_type": None}