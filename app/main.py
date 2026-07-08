from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="TradeAgent")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/health")
def health_check():
    return {"status": "ok"}