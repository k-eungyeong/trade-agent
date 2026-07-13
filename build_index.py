"""
data/raw/ 폴더의 모든 문서를 처리해서 Chroma에 저장하는 배치 스크립트
실행: python build_index.py
"""
import os
from app.rag.pipeline import process_file
from app.rag.embeddings import save_chunks_to_chroma

RAW_DIR = "data/raw"
SUPPORTED_EXT = [".txt", ".md", ".pdf", ".png", ".jpg", ".jpeg"]


def build_index():
    files = [
        f for f in os.listdir(RAW_DIR)
        if os.path.splitext(f)[1].lower() in SUPPORTED_EXT
    ]

    print(f"총 {len(files)}개 파일 발견")

    total_chunks = 0
    failed_files = []

    for filename in files:
        file_path = os.path.join(RAW_DIR, filename)
        print(f"\n처리 중: {filename}")

        try:
            chunks = process_file(file_path)
            if not chunks:
                print(f"  → 청크 없음 (사진이거나 처리 실패)")
                continue

            save_chunks_to_chroma(chunks)
            total_chunks += len(chunks)

        except Exception as e:
            print(f"  → 실패: {e}")
            failed_files.append(filename)

    print(f"\n=== 완료 ===")
    print(f"총 저장된 청크: {total_chunks}개")
    if failed_files:
        print(f"실패한 파일: {failed_files}")


if __name__ == "__main__":
    build_index()