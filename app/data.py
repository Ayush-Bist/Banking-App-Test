BANKING_PRODUCTS = [
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

USER_PROFILES = {
    "user_default": {
        "name": "Ayush",
        "account_balance": 14500.00,
        "monthly_spending": {"dining": 620, "travel": 450, "groceries": 510, "utilities": 230},
        "goals": ["wealth", "cashback", "travel"],
        "existing_products": ["prod-101"],
    }
}

FAQ_KNOWLEDGE_BASE = [
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
        "answer": "Your current primary checking & savings combined balance is $14,500.00.",
    },
]