"""Fetch FX rates via yfinance and store in fx_rates table."""

from __future__ import annotations

from datetime import date

import yfinance as yf
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert

from models import FxRate

# Pairs we track: Yahoo Finance format
FX_PAIRS = {
    "USDGBP": "USDGBP=X",
    "USDKRW": "USDKRW=X",
    "GBPKRW": "GBPKRW=X",
}


def fetch_and_store_fx_rates(db: Session) -> dict[str, float]:
    """Fetch current FX rates and store in fx_rates table.

    Returns dict of {pair: rate}, e.g. {"USDGBP": 0.79, "USDKRW": 1350.5}.
    """
    yahoo_tickers = list(FX_PAIRS.values())
    data = yf.download(yahoo_tickers, period="1d", group_by="ticker", progress=False)
    today = date.today()
    results = {}

    for pair_name, yahoo_ticker in FX_PAIRS.items():
        try:
            if len(yahoo_tickers) == 1:
                row = data
            else:
                row = data[yahoo_ticker]

            if row.empty:
                continue

            rate = float(row.iloc[-1]["Close"])
            results[pair_name] = rate

            stmt = sqlite_upsert(FxRate).values(
                pair=pair_name,
                date=today,
                rate=rate,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["pair", "date"],
                set_={"rate": stmt.excluded.rate},
            )
            db.execute(stmt)

        except (KeyError, IndexError) as e:
            print(f"  Warning: could not fetch {pair_name}: {e}")
            continue

    db.commit()
    return results


def get_latest_fx_rates(db: Session) -> dict[str, float]:
    """Get the most recent rate for each FX pair."""
    from sqlalchemy import func

    subq = (
        db.query(
            FxRate.pair,
            func.max(FxRate.date).label("max_date"),
        )
        .group_by(FxRate.pair)
        .subquery()
    )

    rows = (
        db.query(FxRate.pair, FxRate.rate)
        .join(
            subq,
            (FxRate.pair == subq.c.pair)
            & (FxRate.date == subq.c.max_date),
        )
        .all()
    )

    return {r.pair: r.rate for r in rows}
