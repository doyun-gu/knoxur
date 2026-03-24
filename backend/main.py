import sys
from pathlib import Path

# Ensure backend dir is on sys.path for local imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import init_db
from routers import accounts, holdings, transactions, portfolio

app = FastAPI(title="Knoxur", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3004"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts.router)
app.include_router(holdings.router)
app.include_router(transactions.router)
app.include_router(portfolio.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}
