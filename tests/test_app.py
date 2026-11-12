from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_search_optimization():
    response = client.get("/api/search?q=cashback")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert "Cashback" in data["results"][0]["name"]


def test_recommendations():
    response = client.get("/api/recommendations")
    assert response.status_code == 200
    assert len(response.json()["recommendations"]) > 0


def test_chatbot():
    response = client.post("/api/chat", json={"message": "What is your savings interest rate?"})
    assert response.status_code == 200
    assert "4.75% APY" in response.json()["reply"]