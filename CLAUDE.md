# Knoxur

Personal multi-account portfolio tracker with multi-currency support. Private, local-only deployment.

## Tech Stack

- **Backend:** Python 3.12+, FastAPI, SQLite, yfinance
- **Frontend:** React (Vite), Recharts, TanStack Table
- **Scheduling:** cron on Mac Mini (price fetcher every 15 min during market hours)
- **Deploy:** Mac Mini :3004 (single process — FastAPI serves API + built React static files)

## File Structure

```
knoxur/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── models.py            # SQLAlchemy/SQLite models
│   ├── routers/
│   │   ├── accounts.py      # CRUD for accounts
│   │   ├── holdings.py      # CRUD for holdings/transactions
│   │   ├── prices.py        # Price fetch + history endpoints
│   │   └── portfolio.py     # Aggregated portfolio views
│   ├── services/
│   │   ├── price_fetcher.py # yfinance integration
│   │   ├── fx_rates.py      # Exchange rate fetcher
│   │   └── portfolio.py     # Portfolio valuation logic
│   ├── db.py                # Database connection + migrations
│   └── config.py            # App configuration
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Dashboard, Account detail, Settings
│   │   ├── hooks/           # Custom hooks (usePortfolio, usePrices)
│   │   └── utils/           # Currency formatting, date helpers
│   ├── index.html
│   └── vite.config.ts
├── scripts/
│   ├── fetch_prices.py      # Cron job: fetch latest prices
│   └── seed_data.py         # Initial data setup helper
├── data/
│   └── knoxur.db            # SQLite database (gitignored)
├── CLAUDE.md
├── PLAN.md
└── README.md
```

## Dev Commands

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --port 3004

# Frontend (dev)
cd frontend && npm install && npm run dev

# Frontend (production build — served by FastAPI)
cd frontend && npm run build

# Fetch prices manually
python scripts/fetch_prices.py

# Run both (dev)
# Terminal 1: uvicorn main:app --reload --port 3004
# Terminal 2: cd frontend && npm run dev
```

## Current State / Priorities

- **Phase 1:** Backend + data model + price fetching (in progress)
- **Phase 2:** React dashboard with portfolio charts
- **Phase 3:** Cron automation on Mac Mini
