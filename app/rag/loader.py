"""
문서 로더 - 다양한 형식(txt, md, pdf, image)의 무역서류를 텍스트로 변환
"""
from pathlib import Path


def load_txt(file_path: str) -> str:
    """txt, md 파일을 텍스트로 로드"""
    # TODO: 구현 예정
    pass


def load_pdf(file_path: str) -> str:
    """pdf 파일에서 텍스트 추출 (텍스트 기반 pdf)"""
    # TODO: pdfplumber 또는 PyPDFLoader 사용 예정
    pass


def load_image(file_path: str, user_tag: str = None) -> dict:
    """
    이미지 파일 처리
    - user_tag가 있으면 수동 분류값 사용
    - 없으면 GPT-4o Vision으로 자동 판별 (스캔문서 vs 단순사진)

    Returns:
        {"is_document": bool, "text": str | None, "category": str | None}
    """
    # TODO: OpenAI Vision API 연동 예정
    pass


def load_document(file_path: str, user_tag: str = None) -> dict:
    """
    파일 확장자에 따라 적절한 로더로 분기하는 진입점 함수
    """
    ext = Path(file_path).suffix.lower()

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