# {{SERVICE_NAME}}

FastAPI service on the Shop Golden Path.

## Local

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Deploy

Push to `main` → deploys to `dev`. Health: `/api/health`.