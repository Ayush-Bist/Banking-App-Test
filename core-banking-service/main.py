import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongodb-service:27017")
DB_NAME = os.getenv("MONGO_DB_NAME", "apex_banking_db")

DEFAULT_PRODUCTS = [
    {
        "id": "prod-101",
        "name": "Apex High-Yield Savings Account",
        "category": "Savings",
        "apy": "4.75% APY",
        "tags": ["savings", "interest", "high yield", "emergency fund", "deposit"],
        "description": "Zero monthly maintenance fees with daily compounding interest and instant transfers.",
        "min_balance": 0,
        "risk_level": "Low",
        "popularity_score": 98,
    },
    {
        "id": "prod-102",
        "name": "Horizon Cashback Platinum Card",
        "category": "Credit Cards",
        "apy": "2% Unlimited Cashback",
        "tags": ["credit card", "cashback", "rewards", "shopping", "dining"],
        "description": "Earn 2% cashback on all purchases and 4% on dining and groceries with zero annual fee.",
        "min_balance": 0,
        "risk_level": "Low",
        "popularity_score": 95,
    },
    {
        "id": "prod-103",
        "name": "SmartWealth Automated Index Portfolio",
        "category": "Investments",
        "apy": "8.4% Avg Historical Return",
        "tags": ["invest", "wealth", "stocks", "etf", "retirement", "portfolio"],
        "description": "Diversified low-cost ETF portfolio automatically rebalanced for long-term wealth growth.",
        "min_balance": 500,
        "risk_level": "Medium",
        "popularity_score": 90,
    },
    {
        "id": "prod-104",
        "name": "Premier Home Mortgage & Refinance",
        "category": "Loans",
        "apy": "5.85% Fixed APR",
        "tags": ["home loan", "mortgage", "house", "property", "refinance"],
        "description": "Fast pre-approval with flexible 15-year and 30-year fixed-rate mortgage options.",
        "min_balance": 0,
        "risk_level": "Low",
        "popularity_score": 85,
    },
    {
        "id": "prod-105",
        "name": "Global Travel Zero-FX Debit Card",
        "category": "Checking",
        "apy": "0% Foreign Transaction Fee",
        "tags": ["travel", "forex", "international", "checking", "atm", "currency"],
        "description": "Spend abroad at interbank exchange rates with free global ATM withdrawals.",
        "min_balance": 100,
        "risk_level": "Low",
        "popularity_score": 88,
    },
]

DEFAULT_USER = {
    "user_id": "user_default",
    "name": "Ayush Bist",
    "account_number": "APEX-9042-8810",
    "account_balance": 14500.00,
    "monthly_spending": {"Dining": 620, "Travel": 450, "Groceries": 510, "Utilities": 230},
    "goals": ["wealth", "cashback", "travel"],
    "existing_products": ["prod-101"],
}

DEFAULT_TRANSACTIONS = [
    {
        "tx_id": "TXN-8841",
        "user_id": "user_default",
        "recipient": "Apex High-Yield Interest Credit",
        "category": "Deposit",
        "amount": 54.80,
        "type": "CREDIT",
        "timestamp": "2026-11-10 09:15 UTC",
    },
    {
        "tx_id": "TXN-8840",
        "user_id": "user_default",
        "recipient": "BlueTokai Roasters",
        "category": "Dining",
        "amount": 18.50,
        "type": "DEBIT",
        "timestamp": "2026-11-09 18:42 UTC",
    },
]

DEFAULT_FAQS = [
    {
        "keywords": ["interest", "rate", "apy", "savings"],
        "answer": "Our Apex High-Yield Savings Account currently offers 4.75% APY with zero monthly fees.",
    },
    {
        "keywords": ["card", "lost", "stolen", "block", "freeze"],
        "answer": "You can instantly freeze or replace a lost card under Card Controls, or I can flag a security hold for you right away.",
    },
    {
        "keywords": ["loan", "mortgage", "emi", "borrow"],
        "answer": "Home mortgage rates start at 5.85% Fixed APR. Pre-approval takes less than 5 minutes online.",
    },
    {
        "keywords": ["transfer", "wire", "neft", "rtgs", "upi", "limit"],
        "answer": "Instant domestic transfers have a daily limit of $25,000 with zero transfer fees.",
    },
    {
        "keywords": ["balance", "account", "statement"],
        "answer": "Your live account balance is synced directly from MongoDB and displayed on your Dashboard.",
    },
]

client = None
db = None
DB_MODE = "unknown"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, db, DB_MODE
    try:
        real_client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=2000)
        await real_client.admin.command("ping")
        client = real_client
        DB_MODE = "MongoDB (Cluster)"
    except Exception:
        from mongomock_motor import AsyncMongoMockClient
        client = AsyncMongoMockClient()
        DB_MODE = "MongoDB (In-Memory Mock)"

    db = client[DB_NAME]

    if await db.products.count_documents({}) == 0:
        await db.products.insert_many(DEFAULT_PRODUCTS)
    if await db.users.count_documents({"user_id": "user_default"}) == 0:
        await db.users.insert_one(DEFAULT_USER)
    if await db.faqs.count_documents({}) == 0:
        await db.faqs.insert_many(DEFAULT_FAQS)
    if await db.transactions.count_documents({}) == 0:
        await db.transactions.insert_many(DEFAULT_TRANSACTIONS)

    yield
    client.close()


app = FastAPI(title="Core Banking Data Microservice (MongoDB)", version="3.0.0", lifespan=lifespan)


class ChatLog(BaseModel):
    user_id: str
    user_message: str
    bot_reply: str


class EnrollRequest(BaseModel):
    user_id: str = "user_default"
    product_id: str


class TransferRequest(BaseModel):
    user_id: str = "user_default"
    recipient: str = Field(..., min_length=2)
    category: str = "Transfer"
    amount: float = Field(..., gt=0)


@app.get("/health")
async def health():
    await db.command("ping")
    return {"status": "healthy", "service": "core-banking-service", "database": DB_MODE}


@app.get("/products")
async def get_products():
    return await db.products.find({}, {"_id": 0}).to_list(length=100)


@app.get("/users/{user_id}")
async def get_user_profile(user_id: str):
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return user or await db.users.find_one({"user_id": "user_default"}, {"_id": 0})


@app.post("/users/enroll")
async def enroll_product(payload: EnrollRequest):
    product = await db.products.find_one({"id": payload.product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    await db.users.update_one(
        {"user_id": payload.user_id},
        {"$addToSet": {"existing_products": payload.product_id}},
    )
    return {"enrolled": True, "product_name": product["name"], "database": DB_MODE}


@app.post("/transfers")
async def create_transfer(payload: TransferRequest):
    user = await db.users.find_one({"user_id": payload.user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["account_balance"] < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    new_balance = round(user["account_balance"] - payload.amount, 2)
    await db.users.update_one(
        {"user_id": payload.user_id},
        {"$set": {"account_balance": new_balance}},
    )

    tx_doc = {
        "tx_id": f"TXN-{int(datetime.now(timezone.utc).timestamp()) % 100000}",
        "user_id": payload.user_id,
        "recipient": payload.recipient,
        "category": payload.category,
        "amount": round(payload.amount, 2),
        "type": "DEBIT",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
    await db.transactions.insert_one(tx_doc)
    tx_doc.pop("_id", None)
    return {"status": "completed", "new_balance": new_balance, "transaction": tx_doc, "database": DB_MODE}


@app.get("/transactions/{user_id}")
async def list_transactions(user_id: str):
    txs = await db.transactions.find({"user_id": user_id}, {"_id": 0}).to_list(length=50)
    return list(reversed(txs))


@app.get("/faqs")
async def get_faqs():
    return await db.faqs.find({}, {"_id": 0}).to_list(length=100)


@app.post("/chat-logs")
async def save_chat_log(log: ChatLog):
    doc = {
        **log.model_dump(),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
    await db.chat_logs.insert_one(doc)
    return {"saved": True}


@app.get("/chat-logs/{user_id}")
async def get_chat_logs(user_id: str):
    logs = await db.chat_logs.find({"user_id": user_id}, {"_id": 0}).to_list(length=50)
    return list(reversed(logs))