"""
파일 하나를 받아서 [로드 → 청킹 → 메타데이터 부착]까지 한 번에 처리하는 통합 파이프라인
"""
from pathlib import Path
from app.rag.loader import load_txt, load_pdf_pages, load_image
from app.rag.splitter import split_text


def process_file(file_path: str, user_tag: str = None) -> list[dict]:
    """
    파일 하나를 받아 청크 리스트(텍스트+메타데이터)로 변환

    Returns:
        [{"text": "...", "metadata": {...}}, ...] 형태의 청크 리스트
        처리 실패 시 빈 리스트 반환
    """
    path = Path(file_path)
    ext = path.suffix.lower()
    source_file = path.name

    try:
        # txt, md: 페이지 개념 없이 통째로 청킹
        if ext in [".txt", ".md"]:
            text = load_txt(file_path)
            return split_text(text, source_file=source_file, file_type=ext)

        # pdf: 페이지별로 따로 청킹 (page_number를 정확히 기록하기 위해)
        elif ext == ".pdf":
            pages = load_pdf_pages(file_path)
            all_chunks = []
            for page_num, page_text in enumerate(pages, start=1):
                page_chunks = split_text(
                    page_text,
                    source_file=source_file,
                    file_type=".pdf",
                    page_number=page_num
                )
                all_chunks.extend(page_chunks)
            return all_chunks

        # 이미지: 문서로 판별된 경우에만 청킹, 사진이면 빈 리스트
        elif ext in [".png", ".jpg", ".jpeg"]:
            result = load_image(file_path, user_tag)
            if not result["is_document"]:
                return []  # 사진은 RAG 대상에서 제외
            return split_text(result["text"], source_file=source_file, file_type="image")

        else:
            raise ValueError(f"지원하지 않는 파일 형식: {ext}")

    except Exception as e:
        print(f"{source_file} 처리 실패: {e}")
        return []