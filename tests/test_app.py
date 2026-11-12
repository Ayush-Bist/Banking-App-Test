import importlib.util
import os
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))


def load_service(module_name: str, folder_name: str):
    file_path = os.path.join(ROOT_DIR, folder_name, "main.py")
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


core = load_service("core_banking_service", "core-banking-service")

# Replace real Motor client with in-memory MongoDB mock for local pytest
core.AsyncIOMotorClient = lambda *args, **kwargs: AsyncMongoMockClient()


def test_core_banking_mongodb_endpoints():
    with TestClient(core.app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["database"] == "mongodb-connected"

        products = client.get("/products")
        assert products.status_code == 200
        assert len(products.json()) == 5

        user = client.get("/users/user_default")
        assert user.status_code == 200
        assert user.json()["name"] == "Ayush"

        log = client.post(
            "/chat-logs",
            json={"user_id": "user_default", "user_message": "Hi", "bot_reply": "Hello!"},
        )
        assert log.status_code == 200
        assert log.json()["saved"] is True