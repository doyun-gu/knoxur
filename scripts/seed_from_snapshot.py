"""Seed knoxur.db from the holdings snapshot JSON.

Reads from ~/.knoxur/holdings-snapshot-2026-03-24.json (never committed).
Creates accounts and holdings — skips entries with null quantity.
"""

import json
import sys
from pathlib import Path

# Add backend to path for model imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from db import engine, Base, SessionLocal
from models import Account, Holding

SNAPSHOT_PATH = Path.home() / ".knoxur" / "holdings-snapshot-2026-03-24.json"


def seed():
    # Create all tables
    Base.metadata.create_all(bind=engine)

    with open(SNAPSHOT_PATH) as f:
        data = json.load(f)

    db = SessionLocal()
    try:
        # Clear existing data for idempotent re-runs
        db.query(Holding).delete()
        db.query(Account).delete()
        db.commit()

        for acct_data in data["accounts"]:
            account = Account(
                name=acct_data["name"],
                broker=acct_data["broker"],
                currency=acct_data["currency"],
            )
            db.add(account)
            db.flush()  # get account.id

            for h in acct_data["holdings"]:
                # Skip entries with null quantity (incomplete data)
                if h.get("quantity") is None:
                    print(f"  SKIP {h['ticker']}: null quantity")
                    continue

                # Skip unknown stocks
                if h["ticker"] == "UNKNOWN":
                    print(f"  SKIP {h['ticker']}: unknown stock")
                    continue

                # ISA and Toss have no avg_cost data — default to 0
                avg_cost = h.get("avg_cost", 0) or 0

                # Holdings are in USD for all accounts except ISA (GBP-denominated account
                # but holdings are US stocks priced in USD)
                currency = "USD"

                holding = Holding(
                    account_id=account.id,
                    ticker=h["ticker"],
                    name=h["name"],
                    quantity=h["quantity"],
                    avg_cost=avg_cost,
                    currency=currency,
                )
                db.add(holding)
                print(f"  + {h['ticker']:6s} x{h['quantity']:.4f} (avg_cost={avg_cost})")

            print(f"Account '{account.name}' ({account.broker}, {account.currency}) — {len(acct_data['holdings'])} holdings")

        db.commit()
        print("\nSeed complete.")

        # Summary
        acct_count = db.query(Account).count()
        hold_count = db.query(Holding).count()
        print(f"  {acct_count} accounts, {hold_count} holdings in database")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
