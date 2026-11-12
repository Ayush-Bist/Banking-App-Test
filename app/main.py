import os
from typing import List, Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.data import BANKING_PRODUCTS, USER_PROFILES, FAQ_KNOWLEDGE_BASE

app = FastAPI(title="ApexBank AI Portal", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    user_id: str = "user_default"


class ChatResponse(BaseModel):
    reply: str
    suggested_actions: List[str]


# --- Health Check Endpoint (Used by Kubernetes Liveness/Readiness Probes) ---
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "banking-portal"}


# --- 1. Search Optimization Engine ---
@app.get("/api/search")
def search_banking_catalog(q: Optional[str] = Query(default="", description="Search query")):
    query = (q or "").strip().lower()
    if not query:
        # Return top popular items when search bar is empty
        ranked = sorted(BANKING_PRODUCTS, key=lambda x: x["popularity_score"], reverse=True)
        return {"query": query, "count": len(ranked), "results": ranked, "suggestions": ["High-Yield Savings", "Cashback Card", "Home Mortgage"]}

    tokens = query.split()
    scored_results = []

    for item in BANKING_PRODUCTS:
        score = 0
        name_lower = item["name"].lower()
        cat_lower = item["category"].lower()
        desc_lower = item["description"].lower()
        tags = [t.lower() for t in item["tags"]]

        # Weighted relevance scoring (Title > Tags > Category > Description + Popularity boost)
        for token in tokens:
            if token in name_lower:
                score += 50
            if any(token in tag for tag in tags):
                score += 35
            if token in cat_lower:
                score += 25
            if token in desc_lower:
                score += 10

        if score > 0:
            score += item["popularity_score"] * 0.1
            scored_results.append((score, item))

    scored_results.sort(key=lambda pair: pair[0], reverse=True)
    results = [item for _, item in scored_results]

    # Generate autocomplete search suggestions
    suggestions = [
        item["name"]
        for item in BANKING_PRODUCTS
        if any(query in tag for tag in item["tags"]) or query in item["name"].lower()
    ][:3]

    return {
        "query": query,
        "count": len(results),
        "results": results,
        "suggestions": suggestions,
    }


# --- 2. Personalized Recommendations Engine ---
@app.get("/api/recommendations")
def get_recommendations(user_id: str = "user_default"):
    profile = USER_PROFILES.get(user_id, USER_PROFILES["user_default"])
    balance = profile["account_balance"]
    goals = set(profile["goals"])
    owned = set(profile["existing_products"])

    recommendations = []
    for product in BANKING_PRODUCTS:
        if product["id"] in owned:
            continue

        match_score = 0
        reasons = []

        # Goal alignment
        overlap = goals.intersection(set(product["tags"]))
        if overlap:
            match_score += len(overlap) * 30
            reasons.append(f"Matches your interest in {', '.join(overlap)}")

        # Balance-based eligibility & wealth optimization
        if balance >= 5000 and product["category"] == "Investments":
            match_score += 35
            reasons.append("Ideal for growing surplus cash above $5,000")

        # Spending-habit triggers
        if profile["monthly_spending"].get("dining", 0) > 400 and product["category"] == "Credit Cards":
            match_score += 30
            reasons.append("Earn ~4% back on your $620/mo dining spend")

        if profile["monthly_spending"].get("travel", 0) > 300 and "travel" in product["tags"]:
            match_score += 25
            reasons.append("Saves FX fees on your frequent travel spend")

        if match_score > 0:
            recommendations.append({
                **product,
                "match_score": min(match_score, 99),
                "reason": reasons[0] if reasons else "Popular among similar customers",
            })

    recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    return {"user": profile["name"], "balance": balance, "recommendations": recommendations}


# --- 3. AI Banking Chatbot ---
@app.post("/api/chat", response_model=ChatResponse)
def ai_banking_chatbot(payload: ChatRequest):
    msg = payload.message.strip().lower()
    profile = USER_PROFILES.get(payload.user_id, USER_PROFILES["user_default"])

    # Check knowledge base for domain-specific banking intents
    for entry in FAQ_KNOWLEDGE_BASE:
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
            "compare loan/savings rates, freeze a card, or recommend tailored financial products. What would you like to do?"
        ),
        suggested_actions=["Check Savings APY", "Recommend a Card", "Mortgage Rates"],
    )


# Serve Frontend Static Assets
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def serve_portal():
    return FileResponse(os.path.join(static_dir, "index.html"))