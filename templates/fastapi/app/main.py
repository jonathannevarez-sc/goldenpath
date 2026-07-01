import os

from fastapi import FastAPI

app = FastAPI(title="{{SERVICE_NAME}}")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": os.getenv("SERVICE_NAME", "{{SERVICE_NAME}}"),
        "environment": os.getenv("ENVIRONMENT", "unknown"),
    }


@app.get("/")
def root():
    return {"message": "Hello from Golden Path FastAPI"}