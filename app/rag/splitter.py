"""
텍스트 청킹 - 로더가 추출한 텍스트를 검색 가능한 작은 단위로 분할
"""
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter


def split_text(text: str, source_file: str, file_type: str, page_number: int = None) -> list[dict]:
    """
    텍스트를 청크 단위로 분할하고, 각 청크에 메타데이터를 붙여서 반환

    Args:
        text: 분할할 원본 텍스트 (load_txt, load_pdf, load_image의 결과)
        source_file: 원본 파일명 (출처 표시용)
        file_type: 파일 형식 (.md, .txt, .pdf, image)
        page_number: pdf/이미지의 경우 페이지 번호 (없으면 None)

    Returns:
        [{"text": "청크 내용", "metadata": {...}}, ...]
    """
    if not text:
        return []

    # md 파일은 헤더(#, ##) 기준으로 먼저 구조를 나눔
    if file_type == ".md":
        headers_to_split_on = [("#", "h1"), ("##", "h2"), ("###", "h3")]
        header_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        header_chunks = header_splitter.split_text(text)
        raw_chunks = [chunk.page_content for chunk in header_chunks]
    else:
        raw_chunks = [text]

    # 헤더로 나눈 덩어리를 다시 적정 길이로 세분화
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,      # 한 청크의 최대 글자 수
        chunk_overlap=50,    # 청크끼리 겹치는 글자 수 (문맥 끊김 방지)
        separators=["\n\n", "\n", ". ", " ", ""]  # 우선순위대로 자연스러운 지점에서 나눔
    )

    final_chunks = []
    chunk_index = 0
    for raw_chunk in raw_chunks:
        sub_chunks = splitter.split_text(raw_chunk)
        for sub_chunk in sub_chunks:
            final_chunks.append({
                "text": sub_chunk,
                "metadata": {
                    "source_file": source_file,
                    "file_type": file_type,
                    "chunk_index": chunk_index,
                    "page_number": page_number
                }
            })
            chunk_index += 1

    return final_chunks