# ApexBank AI Portal

Cloud-native Banking Domain Web Application featuring an AI Banking Chatbot, Search Optimization, and Personalized Product Recommendations, containerized with Docker and deployed on Kubernetes via a LoadBalancer Service.

## Local Testing
1. Install dependencies: `pip install -r requirements.txt`
2. Run tests: `pytest`
3. Start server: `uvicorn app.main:app --reload`
4. Open `http://localhost:8000`

## Docker Build & Run
```bash
docker compose up --build -d