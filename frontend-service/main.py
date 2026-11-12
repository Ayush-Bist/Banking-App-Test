import os
from typing import Optional
import httpx
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Frontend Portal & Gateway Microservice", version="1.0.0")

CHATBOT_URL = os.getenv("CHATBOT_URL", "http://chatbot-service:8001")
SEARCH_URL = os.getenv("SEARCH_URL", "http://search-service:8002")
RECOMMENDATIONS_URL = os.getenv("RECOMMENDATIONS_URL", "http://recommendations-service:8003")


class ChatRequest(BaseModel):
    message: str
    user_id: str = "user_default"


@app.get("/health")
def health():
    return {"status": "healthy", "service": "frontend-service"}


@app.get("/api/search")
async def proxy_search(q: Optional[str] = Query(default="")):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{SEARCH_URL}/search", params={"q": q}, timeout=5.0)
        return resp.json()


@app.get("/api/recommendations")
async def proxy_recommendations(user_id: str = "user_default"):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{RECOMMENDATIONS_URL}/recommendations", params={"user_id": user_id}, timeout=5.0)
        return resp.json()


@app.post("/api/chat")
async def proxy_chat(payload: ChatRequest):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{CHATBOT_URL}/chat", json=payload.model_dump(), timeout=5.0)
        return resp.json()


static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def serve_portal():
    return FileResponse(os.path.join(static_dir, "index.html"))