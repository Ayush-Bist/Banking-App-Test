import os
from typing import List
import httpx
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="AI Banking Chatbot Microservice", version="1.0.0")

CORE_BANKING_URL = os.getenv("CORE_BANKING_URL", "http://core-banking-service:8004")


class ChatRequest(BaseModel):
    message: str
    user_id: str = "user_default"


class ChatResponse(BaseModel):
    reply: str
    suggested_actions: List[str]


@app.get("/health")
def health():
    return {"status": "healthy", "service": "chatbot-service"}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    async with httpx.AsyncClient() as client:
        faq_resp = await client.get(f"{CORE_BANKING_URL}/faqs", timeout=5.0)
        user_resp = await client.get(f"{CORE_BANKING_URL}/users/{payload.user_id}", timeout=5.0)
        faqs = faq_resp.json()
        profile = user_resp.json()

    msg = payload.message.strip().lower()

    for entry in faqs:
        if any(kw in msg for kw in entry["keywords"]):
            return ChatResponse(
                reply=entry["answer"],
                suggested_actions=["Compare Savings Rates", "View My Recommendations", "Check Transfer Limits"],
            )

    if "recommend" in msg or "best" in msg or "invest" in msg:
        return ChatResponse(
            reply=(
                f"Hi {profile['name']}, based on your ${profile['account_balance']:,.2f} balance and dining/travel activity, "
                "I recommend the Horizon Cashback Platinum Card and SmartWealth Index Portfolio."
            ),
            suggested_actions=["Explore SmartWealth", "Apply for Cashback Card"],
        )

    return ChatResponse(
        reply=(
            f"Hello {profile['name']}! I'm your ApexBank AI Assistant. I can help you check account balances, "
            "compare loan/savings rates, freeze a card, or recommend tailored financial products."
        ),
        suggested_actions=["Check Savings APY", "Recommend a Card", "Mortgage Rates"],
    )