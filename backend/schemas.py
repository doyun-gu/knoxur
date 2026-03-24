from typing import Optional

from pydantic import BaseModel
from datetime import date, datetime


# --- Accounts ---

class AccountCreate(BaseModel):
    name: str
    broker: str
    currency: str  # GBP, USD, KRW


class AccountOut(BaseModel):
    id: int
    name: str
    broker: str
    currency: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Holdings ---

class HoldingCreate(BaseModel):
    account_id: int
    ticker: str
    name: str
    quantity: float
    avg_cost: float
    currency: str


class HoldingUpdate(BaseModel):
    quantity: Optional[float] = None
    avg_cost: Optional[float] = None


class HoldingOut(BaseModel):
    id: int
    account_id: int
    ticker: str
    name: str
    quantity: float
    avg_cost: float
    currency: str

    model_config = {"from_attributes": True}


# --- Transactions ---

class TransactionCreate(BaseModel):
    account_id: int
    ticker: str
    type: str  # "buy" or "sell"
    quantity: float
    price_per_share: float
    date: date
    notes: Optional[str] = None


class TransactionOut(BaseModel):
    id: int
    account_id: int
    ticker: str
    type: str
    quantity: float
    price_per_share: float
    date: date
    notes: Optional[str]

    model_config = {"from_attributes": True}
