import os
from typing import Optional
import httpx
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Frontend Portal & API Gateway", version="3.0.0")

CORE_BANKING_URL = os.getenv("CORE_BANKING_URL", "http://core-banking-service:8004")
CHATBOT_URL = os.getenv("CHATBOT_URL", "http://chatbot-service:8001")
SEARCH_URL = os.getenv("SEARCH_URL", "http://search-service:8002")
RECOMMENDATIONS_URL = os.getenv("RECOMMENDATIONS_URL", "http://recommendations-service:8003")


class ChatRequest(BaseModel):
    message: str
    user_id: str = "user_default"


class EnrollRequest(BaseModel):
    user_id: str = "user_default"
    product_id: str


class TransferRequest(BaseModel):
    user_id: str = "user_default"
    recipient: str
    category: str = "Transfer"
    amount: float


async def forward_request(method: str, url: str, **kwargs):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.request(method, url, timeout=5.0, **kwargs)
            if resp.status_code >= 400:
                detail = resp.json().get("detail", "Upstream microservice error")
                raise HTTPException(status_code=resp.status_code, detail=detail)
            return resp.json()
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail=f"Microservice unreachable: {url}")


@app.get("/health")
def health():
    return {"status": "healthy", "service": "frontend-service"}


@app.get("/api/system-status")
async def system_status():
    services = {
        "core_banking_mongodb": f"{CORE_BANKING_URL}/health",
        "search_service": f"{SEARCH_URL}/health",
        "recommendations_mysql": f"{RECOMMENDATIONS_URL}/health",
        "chatbot_service": f"{CHATBOT_URL}/health",
    }
    statuses = {}
    async with httpx.AsyncClient() as client:
        for name, url in services.items():
            try:
                r = await client.get(url, timeout=2.0)
                statuses[name] = r.json() if r.status_code == 200 else {"status": "degraded"}
            except Exception:
                statuses[name] = {"status": "offline"}
    return statuses


@app.get("/api/profile")
async def get_profile(user_id: str = "user_default"):
    return await forward_request("GET", f"{CORE_BANKING_URL}/users/{user_id}")


@app.get("/api/search")
async def proxy_search(q: Optional[str] = Query(default="")):
    return await forward_request("GET", f"{SEARCH_URL}/search", params={"q": q})


@app.post("/api/enroll")
async def proxy_enroll(payload: EnrollRequest):
    return await forward_request("POST", f"{CORE_BANKING_URL}/users/enroll", json=payload.model_dump())


@app.get("/api/recommendations")
async def proxy_recommendations(user_id: str = "user_default"):
    return await forward_request("GET", f"{RECOMMENDATIONS_URL}/recommendations", params={"user_id": user_id})


@app.post("/api/recommendations/accept")
async def proxy_accept_recommendation(payload: EnrollRequest):
    return await forward_request("POST", f"{RECOMMENDATIONS_URL}/recommendations/accept", json=payload.model_dump())


@app.get("/api/recommendations/history")
async def proxy_recommendation_history():
    return await forward_request("GET", f"{RECOMMENDATIONS_URL}/recommendations/history")


@app.get("/api/transactions")
async def proxy_transactions(user_id: str = "user_default"):
    return await forward_request("GET", f"{CORE_BANKING_URL}/transactions/{user_id}")


@app.post("/api/transfers")
async def proxy_transfers(payload: TransferRequest):
    return await forward_request("POST", f"{CORE_BANKING_URL}/transfers", json=payload.model_dump())


@app.get("/api/chat-logs")
async def proxy_chat_logs(user_id: str = "user_default"):
    return await forward_request("GET", f"{CORE_BANKING_URL}/chat-logs/{user_id}")


@app.post("/api/chat")
async def proxy_chat(payload: ChatRequest):
    return await forward_request("POST", f"{CHATBOT_URL}/chat", json=payload.model_dump())


static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def serve_portal():
    return FileResponse(os.path.join(static_dir, "index.html"))