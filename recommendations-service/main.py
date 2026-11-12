import os
from datetime import datetime, timezone
import httpx
from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

CORE_BANKING_URL = os.getenv("CORE_BANKING_URL", "http://core-banking-service:8004")
MYSQL_URL = os.getenv(
    "MYSQL_URL",
    "mysql+pymysql://bankuser:bankpass@mysql-service:3306/recommendations_db",
)

Base = declarative_base()


class RecommendationAudit(Base):
    __tablename__ = "recommendation_audits"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(64), index=True)
    product_id = Column(String(64))
    product_name = Column(String(128))
    match_score = Column(Float)
    reason = Column(String(255))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# Connect to MySQL in Kubernetes/Docker, or fall back to local SQLite on Windows
try:
    engine = create_engine(MYSQL_URL, pool_pre_ping=True, connect_args={"connect_timeout": 2})
    Base.metadata.create_all(bind=engine)
    DB_BACKEND = "mysql-connected"
    print(f"Connected to MySQL at {MYSQL_URL}")
except Exception:
    engine = create_engine("sqlite:///./local_recommendations.db", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    DB_BACKEND = "sqlite-local-fallback"
    print("MySQL not found locally — using local SQLite fallback")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Recommendations Microservice (MySQL)", version="2.0.0")


@app.get("/health")
def health():
    return {"status": "healthy", "service": "recommendations-service", "database": DB_BACKEND}


@app.get("/recommendations")
async def get_recommendations(user_id: str = "user_default"):
    async with httpx.AsyncClient() as client:
        prod_resp = await client.get(f"{CORE_BANKING_URL}/products", timeout=5.0)
        user_resp = await client.get(f"{CORE_BANKING_URL}/users/{user_id}", timeout=5.0)
        products = prod_resp.json()
        profile = user_resp.json()

    balance = profile["account_balance"]
    goals = set(profile["goals"])
    owned = set(profile["existing_products"])

    recommendations = []
    for product in products:
        if product["id"] in owned:
            continue

        match_score = 0
        reasons = []

        overlap = goals.intersection(set(product["tags"]))
        if overlap:
            match_score += len(overlap) * 30
            reasons.append(f"Matches your interest in {', '.join(overlap)}")

        if balance >= 5000 and product["category"] == "Investments":
            match_score += 35
            reasons.append("Ideal for growing surplus cash above $5,000")

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

    # Persist recommendation scores in MySQL
    db = SessionLocal()
    try:
        for rec in recommendations:
            db.add(
                RecommendationAudit(
                    user_id=user_id,
                    product_id=rec["id"],
                    product_name=rec["name"],
                    match_score=rec["match_score"],
                    reason=rec["reason"],
                )
            )
        db.commit()
    finally:
        db.close()

    return {"user": profile["name"], "balance": balance, "recommendations": recommendations}


@app.get("/recommendations/history")
def get_recommendation_history():
    db = SessionLocal()
    try:
        rows = db.query(RecommendationAudit).order_by(RecommendationAudit.id.desc()).limit(20).all()
        return [
            {
                "id": r.id,
                "user_id": r.user_id,
                "product_name": r.product_name,
                "match_score": r.match_score,
                "reason": r.reason,
                "created_at": r.created_at,
            }
            for r in rows
        ]
    finally:
        db.close()