"""
검색된 청크 + LLM을 연결해서 실제 답변을 생성하는 RAG 체인
"""
from app.rag.embeddings import search_similar, client
import time


def rewrite_query_with_context(query: str, history: list[dict]) -> str:
    """
    이전 대화를 참고해서, 대명사가 포함된 질문을 검색하기 좋은 완전한 질문으로 재구성
    """
    if not history:
        return query

    history_lines = [f"{'사용자' if h['role'] == 'user' else 'AI'}: {h['content']}" for h in history]
    history_text = "\n".join(history_lines)

    prompt = f"""아래는 이전 대화입니다. 이를 참고해서, 마지막 사용자 질문을 대명사(그거, 그건, 방금 등) 없이
완전하고 명확한 질문으로 다시 써주세요. 다른 설명 없이 재구성된 질문만 출력하세요.

[이전 대화]
{history_text}

[마지막 질문]
{query}

[재구성된 질문]
"""

    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=prompt
    )
    return response.text.strip()


def answer_question(query: str, top_k: int = 3, history: list[dict] = None) -> dict:
    """
    질문을 받아서 관련 문서를 검색하고, 이전 대화 맥락도 참고해서 답변을 생성
    """
    # 1) 대명사가 있으면 검색하기 좋은 완전한 질문으로 먼저 재구성
    search_query = rewrite_query_with_context(query, history) if history else query

    # 2) 재구성된 질문으로 벡터 검색 (원래 query가 아니라 search_query 사용!)
    results = search_similar(search_query, top_k=top_k)

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    if not documents:
        return {"answer": "관련된 문서를 찾을 수 없습니다.", "sources": []}

    context = "\n\n---\n\n".join(documents)

    history_text = ""
    if history:
        history_lines = [f"{'사용자' if h['role'] == 'user' else 'AI'}: {h['content']}" for h in history]
        history_text = "\n".join(history_lines)

    prompt = f"""아래는 무역서류에서 검색된 참고자료입니다. 이 내용을 바탕으로만 질문에 답변해주세요.
참고자료에 없는 내용은 추측하지 말고, 모르면 모른다고 답해주세요.
사용자의 질문에 "그거", "아까 그건" 같은 대명사가 있으면, 아래 이전 대화 내용을 참고해서 무엇을 가리키는지 파악해주세요.

[이전 대화]
{history_text if history_text else "(이전 대화 없음)"}

[참고자료]
{context}

[현재 질문]
{query}

[답변]
"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-flash-lite-latest",
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