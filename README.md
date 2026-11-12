# ApexBank AI Portal

A demo banking portal split into five containerized services:

- **Core banking** provides the sample product catalog and customer profile.
- **Search** ranks the catalog against a query.
- **Recommendations** personalizes products using a customer profile.
- **Chatbot** answers common banking questions.
- **Frontend** serves the web UI and forwards API requests to the backend services.

## Run locally with Docker Compose

From this directory:

```bash
docker compose up --build
```

Open [http://localhost:8000](http://localhost:8000). To stop the services, press `Ctrl+C` or run `docker compose down`.

## Run tests

Install the test dependencies and run:

```bash
python -m pip install fastapi httpx pytest
python -m pytest
```

## Deploy to Kubernetes

Build and publish each image with a registry name available to your cluster, then update the `image` values in `k8s/*.yaml`. Apply the manifests:

```bash
kubectl apply -f k8s/core-banking.yaml
kubectl apply -f k8s/search.yaml
kubectl apply -f k8s/recommendations.yaml
kubectl apply -f k8s/chatbot.yaml
kubectl apply -f k8s/frontend.yaml
```

The frontend is exposed through a `LoadBalancer` service. The other services are cluster-internal.