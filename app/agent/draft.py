"""
빈 양식에 값을 채워서 문서초안을 생성하는 기능
"""
from app.rag.embeddings import client, search_similar
import json


# 원산지발급신청서 템플릿 정의
TEMPLATES = {
    "원산지발급신청서": {
        "required_fields": [
            "신청인_상호",
            "사업자등록번호",
            "수출신고번호",
            "수출신고수리일",
            "수출자_상호",
            "수입자_상호",
            "수입자_국가",
            "품명",
            "HS_Code"
        ],
        "description": "원산지증명서 발급을 위한 신청서"
    }
}


def get_required_fields(template_type: str) -> list[str]:
    """해당 양식에 필요한 필드 목록 반환 (사용자에게 뭘 물어봐야 할지 확인용)"""
    template = TEMPLATES.get(template_type)
    if not template:
        return []
    return template["required_fields"]


def check_missing_fields(template_type: str, provided_values: dict) -> list[str]:
    """사용자가 입력한 값 중 빠진 필드가 있는지 확인"""
    required = get_required_fields(template_type)
    return [f for f in required if f not in provided_values or not provided_values[f]]


def generate_draft(template_type: str, values: dict) -> str:
    """
    양식 종류와 입력값을 받아서 문서초안 생성

    values: {"신청인_상호": "OO무역", "사업자등록번호": "123-45-67890", ...}
    """
    template = TEMPLATES.get(template_type)
    if not template:
        return f"지원하지 않는 양식입니다: {template_type}"

    # 빠진 필드 확인
    missing = check_missing_fields(template_type, values)
    if missing:
        return f"다음 정보가 부족합니다: {', '.join(missing)}"

    # RAG 검색으로 작성 규칙/양식 참고자료 가져오기
    reference = search_similar(f"{template_type} 작성 방법", top_k=2)
    reference_text = "\n\n".join(reference["documents"][0]) if reference["documents"][0] else ""

    # 입력값을 텍스트로 정리
    values_text = "\n".join([f"- {k}: {v}" for k, v in values.items()])

    prompt = f"""아래 정보를 바탕으로 "{template_type}" 문서 초안을 작성해줘.
실제 공문서 형식에 맞게, 항목별로 정리된 형태로 작성해줘.

[작성 참고자료]
{reference_text}

[입력된 정보]
{values_text}

[문서 초안]
"""

    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=prompt
    )

    return response.text

def extract_values_from_message(message: str, template_type: str, history: list[dict] = None) -> dict:
    """
    사용자의 자연어 메시지(+이전 대화)에서 문서초안에 필요한 값들을 추출
    """
    required = get_required_fields(template_type)
    if not required:
        return {}

    history_text = ""
    if history:
        lines = [f"{'사용자' if h['role'] == 'user' else 'AI'}: {h['content']}" for h in history]
        history_text = "\n".join(lines)

    prompt = f"""아래 대화에서 "{template_type}" 작성에 필요한 정보를 찾아 추출해줘.
필요한 항목: {required}

[이전 대화]
{history_text if history_text else "(없음)"}

[현재 메시지]
{message}

찾은 정보만 JSON으로 답해줘 (없는 항목은 포함하지 마):
"""
    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=prompt
    )
    text = response.text.strip().replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}