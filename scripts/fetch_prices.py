"""Cron job: fetch all stock prices + FX rates, store in DB, take daily snapshot.

Intended to run via cron:
  */15 8-21 * * 1-5  cd ~/Developer/knoxur && .venv/bin/python scripts/fetch_prices.py
"""

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from db import SessionLocal, Base, engine
from models import PortfolioSnapshot
from services.price_fetcher import fetch_and_store_prices
from services.fx_rates import fetch_and_store_fx_rates
from services.portfolio import compute_portfolio_summary

from sqlalchemy.dialects.sqlite import insert as sqlite_upsert


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Fetch stock prices
        print("Fetching stock prices...")
        prices = fetch_and_store_prices(db)
        print(f"  {len(prices)} tickers updated")

        # 2. Fetch FX rates
        print("Fetching FX rates...")
        fx = fetch_and_store_fx_rates(db)
        print(f"  {len(fx)} pairs updated")
        for pair, rate in fx.items():
            print(f"    {pair}: {rate}")

        # 3. Take daily snapshot
        print("Computing portfolio snapshot...")
        summary = compute_portfolio_summary(db)

        stmt = sqlite_upsert(PortfolioSnapshot).values(
            date=date.today(),
            total_gbp=summary["total_gbp"],
            total_usd=summary["total_usd"],
            total_krw=summary["total_krw"],
            breakdown_json=json.dumps(summary["accounts"]),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["date"],
            set_={
                "total_gbp": stmt.excluded.total_gbp,
                "total_usd": stmt.excluded.total_usd,
                "total_krw": stmt.excluded.total_krw,
                "breakdown_json": stmt.excluded.breakdown_json,
            },
        )
        db.execute(stmt)
        db.commit()

        print(f"\nSnapshot saved:")
        print(f"  GBP: £{summary['total_gbp']:,.2f}")
        print(f"  USD: ${summary['total_usd']:,.2f}")
        print(f"  KRW: ₩{summary['total_krw']:,.0f}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
