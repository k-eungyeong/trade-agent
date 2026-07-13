"""
검색된 청크 + LLM을 연결해서 실제 답변을 생성하는 RAG 체인
"""
from app.rag.embeddings import search_similar, client
import time


def answer_question(query: str, top_k: int = 3) -> dict:
    """
    질문을 받아서 관련 문서를 검색하고, 그 내용을 바탕으로 답변을 생성
    """
    results = search_similar(query, top_k=top_k)

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    if not documents:
        return {"answer": "관련된 문서를 찾을 수 없습니다.", "sources": []}

    context = "\n\n---\n\n".join(documents)

    prompt = f"""아래는 무역서류에서 검색된 참고자료입니다. 이 내용을 바탕으로만 질문에 답변해주세요.
참고자료에 없는 내용은 추측하지 말고, 모르면 모른다고 답해주세요.

[참고자료]
{context}

[질문]
{query}

[답변]
"""

    # Gemini 서버가 일시적으로 혼잡할 수 있어 재시도 로직 추가
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt
            )
            answer_text = response.text
            break
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                else:
                    return {
                        "answer": "죄송합니다, 현재 AI 서버가 혼잡하여 답변을 생성하지 못했습니다. 잠시 후 다시 시도해주세요.",
                        "sources": []
                    }
            else:
                raise

    sources = []
    seen = set()
    for meta in metadatas:
        source_key = f"{meta.get('source_file')}_{meta.get('page_number', '')}"
        if source_key not in seen:
            sources.append({
                "file": meta.get("source_file"),
                "page": meta.get("page_number")
            })
            seen.add(source_key)

    return {
        "answer": answer_text,
        "sources": sources
    }