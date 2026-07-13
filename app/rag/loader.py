"""
문서 로더 - 다양한 형식(txt, md, pdf, image)의 무역서류를 텍스트로 변환
"""
from pathlib import Path
import pdfplumber
import base64
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def load_txt(file_path: str) -> str:
    """txt, md 파일을 텍스트로 로드"""
    # TODO: 구현 예정
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def load_pdf(file_path: str) -> str:
    """pdf 파일에서 텍스트 추출 (텍스트 기반 pdf)"""
    text_parts = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
            else:
                # 텍스트 추출 안 되면(스캔 pdf 가능성) 표시만 해둠
                text_parts.append(f"[페이지 {i+1}: 텍스트 추출 실패 - 스캔 문서일 수 있음]")
    return "\n\n".join(text_parts)


def load_image(file_path: str, user_tag: str = None) -> dict:
    """
    이미지 파일 처리
    - user_tag가 있으면 수동 분류값 사용
    - 없으면 Gemini Vision으로 자동 판별 (스캔문서 vs 단순사진)

    Returns:
        {"is_document": bool, "text": str | None, "category": str | None}
    """
    with open(file_path, "rb") as f:
        image_bytes = f.read()

    prompt = """이 이미지를 분석해줘.
1. 이 이미지가 문서(글자가 포함된 서류, 스캔본)인지, 아니면 단순 사진(글자 없는 사물/풍경 등)인지 판별해줘.
2. 문서라면 이미지 안의 모든 텍스트를 그대로 추출해줘.

아래 형식으로만 답해줘 (다른 설명 붙이지 말고):
IS_DOCUMENT: true 또는 false
TEXT: (문서인 경우 추출한 텍스트 전체, 아니면 없음)
"""

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            prompt
        ]
    )

    result_text = response.text

    is_document = "true" in result_text.split("TEXT:")[0].lower()
    extracted_text = result_text.split("TEXT:")[-1].strip() if is_document else None

    return {
        "is_document": is_document,
        "text": extracted_text,
        "category": user_tag
    }

def load_document(file_path: str, user_tag: str = None) -> dict:
    """
    파일 확장자에 따라 적절한 로더로 분기하는 진입점 함수
    """
    path = Path(file_path)

    # 1. 파일 존재 여부 확인
    if not path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    ext = path.suffix.lower()

    try:
        if ext in [".txt", ".md"]:
            text = load_txt(file_path)
            return {"text": text, "file_type": ext, "is_document": True}

        elif ext == ".pdf":
            text = load_pdf(file_path)
            return {"text": text, "file_type": "pdf", "is_document": True}

        elif ext in [".png", ".jpg", ".jpeg"]:
            result = load_image(file_path, user_tag)
            return {"file_type": "image", **result}

        else:
            raise ValueError(f"지원하지 않는 파일 형식: {ext}")

    except Exception as e:
        # 2. 처리 중 에러가 나도 서버가 죽지 않게, 에러 정보를 담아 반환
        return {
            "text": None,
            "file_type": ext,
            "is_document": False,
            "error": str(e),
        }