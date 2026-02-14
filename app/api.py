"""Minimal FastAPI app for health check."""
from fastapi import FastAPI

app = FastAPI(title="Avito Monitor", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}
