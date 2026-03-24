"""Portfolio valuation logic — compute totals across accounts and currencies."""

from sqlalchemy.orm import Session

from models import Account, Holding
from services.price_fetcher import get_latest_prices
from services.fx_rates import get_latest_fx_rates


def compute_portfolio_summary(db: Session) -> dict:
    """Compute total portfolio value in GBP, USD, KRW with per-account breakdown.

    Returns:
        {
            "total_gbp": float,
            "total_usd": float,
            "total_krw": float,
            "accounts": [
                {
                    "id": int,
                    "name": str,
                    "broker": str,
                    "native_currency": str,
                    "total_native": float,
                    "total_gbp": float,
                    "total_usd": float,
                    "total_krw": float,
                    "holdings_count": int,
                }
            ]
        }
    """
    prices = get_latest_prices(db)
    fx = get_latest_fx_rates(db)

    # FX conversion helpers — all holdings are priced in USD
    usd_to_gbp = fx.get("USDGBP", 1.0)
    usd_to_krw = fx.get("USDKRW", 1.0)
    gbp_to_krw = fx.get("GBPKRW", 1.0)

    accounts = db.query(Account).all()
    account_summaries = []
    grand_total_usd = 0.0

    for acct in accounts:
        holdings = db.query(Holding).filter(Holding.account_id == acct.id).all()
        acct_total_usd = 0.0

        for h in holdings:
            price = prices.get(h.ticker)
            if price is None:
                continue
            acct_total_usd += h.quantity * price

        # Convert to all currencies
        acct_total_gbp = acct_total_usd * usd_to_gbp
        acct_total_krw = acct_total_usd * usd_to_krw

        # Native currency total
        if acct.currency == "GBP":
            total_native = acct_total_gbp
        elif acct.currency == "KRW":
            total_native = acct_total_krw
        else:
            total_native = acct_total_usd

        account_summaries.append({
            "id": acct.id,
            "name": acct.name,
            "broker": acct.broker,
            "native_currency": acct.currency,
            "total_native": round(total_native, 2),
            "total_gbp": round(acct_total_gbp, 2),
            "total_usd": round(acct_total_usd, 2),
            "total_krw": round(acct_total_krw, 2),
            "holdings_count": len(holdings),
        })

        grand_total_usd += acct_total_usd

    return {
        "total_gbp": round(grand_total_usd * usd_to_gbp, 2),
        "total_usd": round(grand_total_usd, 2),
        "total_krw": round(grand_total_usd * usd_to_krw, 2),
        "accounts": account_summaries,
    }


def compute_holdings_detail(db: Session) -> list[dict]:
    """Get all holdings with current prices and P&L.

    Returns list of holdings with:
        ticker, name, account, quantity, avg_cost, current_price,
        market_value, gain_loss, gain_loss_pct
    """
    prices = get_latest_prices(db)
    holdings = (
        db.query(Holding, Account)
        .join(Account, Holding.account_id == Account.id)
        .all()
    )

    result = []
    for holding, account in holdings:
        price = prices.get(holding.ticker)
        if price is None:
            current_price = None
            market_value = None
            gain_loss = None
            gain_loss_pct = None
        else:
            current_price = round(price, 2)
            market_value = round(holding.quantity * price, 2)

            if holding.avg_cost > 0:
                cost_basis = holding.quantity * holding.avg_cost
                gain_loss = round(market_value - cost_basis, 2)
                gain_loss_pct = round((gain_loss / cost_basis) * 100, 2) if cost_basis else None
            else:
                gain_loss = None
                gain_loss_pct = None

        result.append({
            "ticker": holding.ticker,
            "name": holding.name,
            "account_id": account.id,
            "account_name": account.name,
            "broker": account.broker,
            "account_currency": account.currency,
            "quantity": holding.quantity,
            "avg_cost": holding.avg_cost,
            "current_price": current_price,
            "market_value": market_value,
            "gain_loss": gain_loss,
            "gain_loss_pct": gain_loss_pct,
        })

    # Sort by market value descending (None values at end)
    result.sort(key=lambda x: x["market_value"] or 0, reverse=True)
    return result
