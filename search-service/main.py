import os
from typing import Optional
import httpx
from fastapi import FastAPI, Query

app = FastAPI(title="Search Optimization Microservice", version="1.0.0")

CORE_BANKING_URL = os.getenv("CORE_BANKING_URL", "http://core-banking-service:8004")


@app.get("/health")
def health():
    return {"status": "healthy", "service": "search-service"}


@app.get("/search")
async def search_catalog(q: Optional[str] = Query(default="")):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{CORE_BANKING_URL}/products", timeout=5.0)
        products = resp.json()

    query = (q or "").strip().lower()
    if not query:
        ranked = sorted(products, key=lambda x: x["popularity_score"], reverse=True)
        return {
            "query": query,
            "count": len(ranked),
            "results": ranked,
            "suggestions": ["High-Yield Savings", "Cashback Card", "Home Mortgage"],
        }

    tokens = query.split()
    scored_results = []

    for item in products:
        score = 0
        name_lower = item["name"].lower()
        cat_lower = item["category"].lower()
        desc_lower = item["description"].lower()
        tags = [t.lower() for t in item["tags"]]

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
    suggestions = [
        item["name"]
        for item in products
        if any(query in tag for tag in item["tags"]) or query in item["name"].lower()
    ][:3]

    return {"query": query, "count": len(results), "results": results, "suggestions": suggestions}