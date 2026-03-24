"""Portfolio and FX rate endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db import get_db
from services.portfolio import compute_portfolio_summary, compute_holdings_detail
from services.price_fetcher import fetch_and_store_prices, get_latest_prices
from services.fx_rates import fetch_and_store_fx_rates, get_latest_fx_rates

router = APIRouter(prefix="/api", tags=["portfolio"])


@router.get("/portfolio/summary")
def portfolio_summary(db: Session = Depends(get_db)):
    """Total portfolio value in GBP, USD, KRW with per-account breakdown."""
    return compute_portfolio_summary(db)


@router.get("/portfolio/holdings")
def portfolio_holdings(db: Session = Depends(get_db)):
    """All holdings with current prices and P&L."""
    return compute_holdings_detail(db)


@router.post("/prices/fetch")
def trigger_price_fetch(db: Session = Depends(get_db)):
    """Manually trigger a price fetch for all tickers."""
    prices = fetch_and_store_prices(db)
    return {"fetched": len(prices), "prices": prices}


@router.get("/prices/latest")
def latest_prices(db: Session = Depends(get_db)):
    """Get the most recent stored prices."""
    return get_latest_prices(db)


@router.post("/fx-rates/fetch")
def trigger_fx_fetch(db: Session = Depends(get_db)):
    """Manually trigger FX rate fetch."""
    rates = fetch_and_store_fx_rates(db)
    return {"fetched": len(rates), "rates": rates}


@router.get("/fx-rates/current")
def current_fx_rates(db: Session = Depends(get_db)):
    """Get the most recent stored FX rates."""
    return get_latest_fx_rates(db)
