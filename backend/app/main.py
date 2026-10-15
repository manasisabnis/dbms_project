"""FastAPI entry point.   Run from the repo root:

    uvicorn backend.app.main:app --reload

Interactive docs: http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from backend.app.routers import trends, cases
# Person 1: add your routers here, e.g.
#   from backend.app.routers import cases
#   app.include_router(cases.router, prefix="/api")

app = FastAPI(title="Legal Case Citation Evolution Analyzer", version="0.1.0")

# Lets the Next.js dev server call this API from the browser.
app.add_middleware(
    CORSMiddleware,
        allow_origins=[
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:3001", "http://127.0.0.1:3001",
    ],
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