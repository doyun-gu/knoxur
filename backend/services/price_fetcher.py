"""Fetch current stock prices via yfinance and store in price_history."""

from __future__ import annotations

from datetime import date

import yfinance as yf
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert

from models import Holding, PriceHistory


def get_unique_tickers(db: Session) -> list[str]:
    """Get all unique tickers from holdings."""
    rows = db.query(Holding.ticker).distinct().all()
    return [r[0] for r in rows]


def fetch_and_store_prices(db: Session) -> dict[str, float]:
    """Fetch current prices for all holdings tickers, store in price_history.

    Returns dict of {ticker: close_price}.
    """
    tickers = get_unique_tickers(db)
    if not tickers:
        return {}

    # Batch download — 1d period gives latest trading day
    data = yf.download(tickers, period="1d", group_by="ticker", progress=False)
    today = date.today()
    results = {}

    for ticker in tickers:
        try:
            if len(tickers) == 1:
                row = data
            else:
                row = data[ticker]

            # yfinance returns DataFrame — get the last row
            if row.empty:
                continue

            last = row.iloc[-1]
            close_price = float(last["Close"])
            results[ticker] = close_price

            # Upsert into price_history
            stmt = sqlite_upsert(PriceHistory).values(
                ticker=ticker,
                date=today,
                open=float(last["Open"]) if "Open" in last else None,
                close=close_price,
                high=float(last["High"]) if "High" in last else None,
                low=float(last["Low"]) if "Low" in last else None,
                volume=int(last["Volume"]) if "Volume" in last else None,
                currency="USD",
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["ticker", "date"],
                set_={
                    "open": stmt.excluded.open,
                    "close": stmt.excluded.close,
                    "high": stmt.excluded.high,
                    "low": stmt.excluded.low,
                    "volume": stmt.excluded.volume,
                },
            )
            db.execute(stmt)

        except (KeyError, IndexError) as e:
            print(f"  Warning: could not fetch {ticker}: {e}")
            continue

    db.commit()
    return results


def get_latest_prices(db: Session) -> dict[str, float]:
    """Get the most recent close price for each ticker from price_history."""
    from sqlalchemy import func

    subq = (
        db.query(
            PriceHistory.ticker,
            func.max(PriceHistory.date).label("max_date"),
        )
        .group_by(PriceHistory.ticker)
        .subquery()
    )

    rows = (
        db.query(PriceHistory.ticker, PriceHistory.close)
        .join(
            subq,
            (PriceHistory.ticker == subq.c.ticker)
            & (PriceHistory.date == subq.c.max_date),
        )
        .all()
    )

    return {r.ticker: r.close for r in rows if r.close is not None}
