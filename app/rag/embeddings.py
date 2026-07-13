"""
임베딩 생성 + Chroma 벡터스토어 저장/검색
"""
import os
import chromadb
from google import genai
from google.genai import types
from dotenv import load_dotenv
import time

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Chroma를 디스크에 영구 저장 (data/chroma_db 폴더에 쌓임)
chroma_client = chromadb.PersistentClient(path="data/chroma_db")
collection = chroma_client.get_or_create_collection(name="trade_documents")


def embed_text(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
    """
    텍스트 하나를 임베딩(숫자 벡터)으로 변환
    속도 제한(429) 에러가 나면 잠깐 대기 후 재시도
    """
    max_retries = 5
    for attempt in range(max_retries):
        try:
            result = client.models.embed_content(
                model="gemini-embedding-001",
                contents=text,
                config=types.EmbedContentConfig(task_type=task_type)
            )
            return result.embeddings[0].values
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait_time = 20 * (attempt + 1)  # 20초, 40초, 60초, 80초, 100초
                print(f"  속도 제한 걸림, {wait_time}초 대기 후 재시도... ({attempt+1}/{max_retries})")
                time.sleep(wait_time)
            else:
                raise
    raise Exception("최대 재시도 횟수 초과")


def save_chunks_to_chroma(chunks: list[dict]):
    """
    청크 리스트(텍스트+메타데이터)를 임베딩해서 Chroma에 저장
    """
    for i, chunk in enumerate(chunks):
        embedding = embed_text(chunk["text"], task_type="RETRIEVAL_DOCUMENT")

        chunk_id = f"{chunk['metadata']['source_file']}_{chunk['metadata']['chunk_index']}"

        clean_metadata = {
            k: v for k, v in chunk["metadata"].items() if v is not None
        }

        collection.add(
            ids=[chunk_id],
            embeddings=[embedding],
            documents=[chunk["text"]],
            metadatas=[clean_metadata]
        )

        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(chunks)}개 처리 중...")

        time.sleep(1.5)  # 요청 사이 1.5초씩 쉬어서 속도 제한 방지

    print(f"{len(chunks)}개 청크 저장 완료")


def search_similar(query: str, top_k: int = 3) -> dict:
    """
    질문과 가장 비슷한 청크를 Chroma에서 검색
    """
    query_embedding = embed_text(query, task_type="RETRIEVAL_QUERY")

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    return results