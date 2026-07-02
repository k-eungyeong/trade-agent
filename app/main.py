from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="TradeAgent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 배포 시 프론트 도메인으로 제한 권장
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "ok", "message": "TradeAgent API is running"}


# TODO (Day 8~9): /ask 엔드포인트 구현
# @app.post("/ask")
# def ask(question: str):
#     ...
