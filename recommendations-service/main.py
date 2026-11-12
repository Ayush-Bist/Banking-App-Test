import os
from datetime import datetime, timezone
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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
    status = Column(String(32), default="RECOMMENDED")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


try:
    engine = create_engine(MYSQL_URL, pool_pre_ping=True, connect_args={"connect_timeout": 2})
    Base.metadata.create_all(bind=engine)
    DB_BACKEND = "MySQL 8.0 (Cluster)"
except Exception:
    engine = create_engine("sqlite:///./local_recommendations.db", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    DB_BACKEND = "SQLite (Local Fallback)"

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Recommendations Microservice (MySQL)", version="3.0.0")


class AcceptOfferRequest(BaseModel):
    user_id: str = "user_default"
    product_id: str


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
            reasons.append(f"Aligns with your {', '.join(overlap)} goals")

        if balance >= 5000 and product["category"] == "Investments":
            match_score += 35
            reasons.append("High surplus balance eligible for index growth")

        if profile["monthly_spending"].get("Dining", 0) > 400 and product["category"] == "Credit Cards":
            match_score += 30
            reasons.append("Earn 4% cashback on your $620/mo dining spend")

        if profile["monthly_spending"].get("Travel", 0) > 300 and "travel" in product["tags"]:
            match_score += 25
            reasons.append("Zero FX fees on your $450/mo travel spend")

        if match_score > 0:
            recommendations.append({
                **product,
                "match_score": min(match_score, 99),
                "reason": reasons[0] if reasons else "Recommended for your profile",
            })

    recommendations.sort(key=lambda x: x["match_score"], reverse=True)

    db = SessionLocal()
    try:
        for rec in recommendations:
            existing = (
                db.query(RecommendationAudit)
                .filter_by(user_id=user_id, product_id=rec["id"], status="RECOMMENDED")
                .first()
            )
            if not existing:
                db.add(
                    RecommendationAudit(
                        user_id=user_id,
                        product_id=rec["id"],
                        product_name=rec["name"],
                        match_score=rec["match_score"],
                        reason=rec["reason"],
                        status="RECOMMENDED",
                    )
                )
        db.commit()
    finally:
        db.close()

    return {
        "user": profile["name"],
        "balance": balance,
        "database": DB_BACKEND,
        "recommendations": recommendations,
    }


@app.post("/recommendations/accept")
async def accept_recommendation(payload: AcceptOfferRequest):
    # 1. Enroll user in MongoDB via core-banking-service
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{CORE_BANKING_URL}/users/enroll",
            json=payload.model_dump(),
            timeout=5.0,
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Enrollment failed")

    # 2. Update relational audit record status in MySQL
    db = SessionLocal()
    try:
        row = (
            db.query(RecommendationAudit)
            .filter_by(user_id=payload.user_id, product_id=payload.product_id)
            .order_by(RecommendationAudit.id.desc())
            .first()
        )
        if row:
            row.status = "ACCEPTED"
            db.commit()
    finally:
        db.close()

    return {"accepted": True, "product_id": payload.product_id, "mysql_status": "ACCEPTED"}


@app.get("/recommendations/history")
def get_recommendation_history():
    db = SessionLocal()
    try:
        rows = db.query(RecommendationAudit).order_by(RecommendationAudit.id.desc()).limit(15).all()
        return {
            "database": DB_BACKEND,
            "records": [
                {
                    "id": r.id,
                    "user_id": r.user_id,
                    "product_name": r.product_name,
                    "match_score": r.match_score,
                    "reason": r.reason,
                    "status": r.status,
                    "created_at": r.created_at.strftime("%Y-%m-%d %H:%M UTC") if r.created_at else "",
                }
                for r in rows
            ],
        }
    finally:
        db.close()