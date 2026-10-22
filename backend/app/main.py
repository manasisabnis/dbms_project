"""FastAPI application for the Legal Case Citation Evolution Analyzer."""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from backend.app.routers import trends, cases

app = FastAPI(
    title="Legal Case Citation Evolution Analyzer",
    version="0.1.0",
)

fixed_origins = [
    "https://astonishing-pithivier-b3484f.netlify.app",

    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

configured_origins = [
    origin.strip().rstrip("/")
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(fixed_origins + configured_origins)),
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(trends.router, prefix="/api")
app.include_router(cases.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")
