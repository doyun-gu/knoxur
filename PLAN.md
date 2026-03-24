# Knoxur — Project Plan

## What Is This

A personal portfolio tracker that consolidates holdings across 3 brokerage accounts (different countries/currencies), fetches live stock prices and exchange rates, and visualises total portfolio value over time.

**Deployment:** Local only — Mac Mini (:3004), accessible from MacBook over LAN. No cloud, no external access. Financial data never leaves your machines.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   Browser                        │
│         React + Recharts + TanStack Table        │
└──────────────────────┬──────────────────────────┘
                       │ HTTP (localhost:3004)
┌──────────────────────┴──────────────────────────┐
│                 FastAPI Backend                   │
│  ┌────────────┐ ┌───────────┐ ┌──────────────┐  │
│  │ Accounts   │ │ Holdings  │ │ Portfolio    │  │
│  │ Router     │ │ Router    │ │ Router       │  │
│  └─────┬──────┘ └─────┬─────┘ └──────┬───────┘  │
│        │              │              │           │
│  ┌─────┴──────────────┴──────────────┴───────┐   │
│  │           Service Layer                    │   │
│  │  price_fetcher.py  │  fx_rates.py         │   │
│  │  portfolio.py      │  valuations.py       │   │
│  └────────────────────┬──────────────────────┘   │
│                       │                          │
│  ┌────────────────────┴──────────────────────┐   │
│  │              SQLite (knoxur.db)            │   │
│  │  accounts │ holdings │ transactions       │   │
│  │  price_history │ fx_rates │ snapshots     │   │
│  └───────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
         ▲
         │ cron (every 15 min)
┌────────┴─────────┐
│  yfinance API    │
│  (Yahoo Finance) │
└──────────────────┘
```

---

## Data Model

### accounts
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| name | TEXT | Display name (e.g. "ISA", "Korean Brokerage") |
| broker | TEXT | Broker name (e.g. "Trading 212", "Samsung Securities") |
| currency | TEXT | Base currency of account (GBP, USD, KRW) |
| created_at | DATETIME | |

### holdings
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| account_id | INTEGER FK | References accounts.id |
| ticker | TEXT | Yahoo Finance ticker (e.g. "TSLA", "005930.KS") |
| name | TEXT | Human-readable name (e.g. "Samsung Electronics") |
| quantity | REAL | Number of shares held |
| avg_cost | REAL | Average cost per share (in native currency) |
| currency | TEXT | Native currency of this stock |

### transactions
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| account_id | INTEGER FK | |
| ticker | TEXT | |
| type | TEXT | "buy" or "sell" |
| quantity | REAL | |
| price_per_share | REAL | In native currency |
| date | DATE | Transaction date |
| notes | TEXT | Optional |

### price_history
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| ticker | TEXT | Yahoo Finance ticker |
| date | DATE | |
| open | REAL | |
| close | REAL | |
| high | REAL | |
| low | REAL | |
| volume | INTEGER | |
| currency | TEXT | |
| UNIQUE(ticker, date) | | Prevents duplicates |

### fx_rates
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| pair | TEXT | e.g. "USDGBP", "USDKRW", "GBPKRW" |
| date | DATE | |
| rate | REAL | |
| UNIQUE(pair, date) | | |

### portfolio_snapshots
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| date | DATE | |
| total_gbp | REAL | Total portfolio value in GBP |
| total_usd | REAL | Total portfolio value in USD |
| total_krw | REAL | Total portfolio value in KRW |
| breakdown_json | TEXT | Per-account values as JSON |

---

## APIs Required

### 1. Stock Prices — yfinance (Python library)

**What:** Unofficial Yahoo Finance API wrapper. Free, no API key.

**Install:** `pip install yfinance`

**Usage:**
```python
import yfinance as yf

# Single ticker — current price
ticker = yf.Ticker("TSLA")
price = ticker.info["regularMarketPrice"]  # 185.20

# Multiple tickers — batch download
data = yf.download(["TSLA", "VOO", "005930.KS"], period="1d")

# Historical data for charts
history = yf.download("TSLA", period="1y", interval="1d")
# Returns: Date, Open, High, Low, Close, Volume
```

**Ticker format by exchange:**
| Exchange | Suffix | Example |
|----------|--------|---------|
| NYSE / NASDAQ | (none) | TSLA, AAPL, VOO |
| London Stock Exchange | .L | HSBA.L, VOD.L |
| Korea Exchange (KRX) | .KS | 005930.KS (Samsung) |
| KOSDAQ | .KQ | 035720.KQ (Kakao) |

**Rate limits:** Unofficial, but ~2000 requests/day works reliably. Batch downloads count as 1 request regardless of ticker count.

**Data delay:** ~15 minutes for US/UK markets. Korean market is closer to real-time.

### 2. Exchange Rates — yfinance (same library)

**What:** Yahoo Finance also provides FX rate data using currency pair tickers.

**Usage:**
```python
import yfinance as yf

# Current rate
usdgbp = yf.Ticker("USDGBP=X").info["regularMarketPrice"]

# Historical rates
fx_history = yf.download("USDGBP=X", period="1y", interval="1d")
```

**Currency pairs we need:**
| Pair | Ticker | Purpose |
|------|--------|---------|
| USD to GBP | USDGBP=X | Convert US stocks to GBP |
| USD to KRW | USDKRW=X | Convert US stocks to KRW |
| GBP to KRW | GBPKRW=X | Convert UK stocks to KRW |
| GBP to USD | GBPUSD=X | Convert UK stocks to USD |
| KRW to GBP | KRWGBP=X | Convert Korean stocks to GBP |
| KRW to USD | KRWUSD=X | Convert Korean stocks to USD |

In practice, we only need 2 independent rates (e.g. USDGBP and USDKRW) and derive the rest.

### 3. No Other External APIs Needed

yfinance covers everything:
- Stock prices (all exchanges)
- ETF prices
- Exchange rates
- Historical data
- Basic company info (name, sector, market cap)

**Zero API keys. Zero cost. Zero rate limit concerns at our scale.**

---

## Cron Jobs (Mac Mini)

### Price Fetcher — every 15 minutes during market hours

```cron
# KRX: Mon-Fri 09:00-15:30 KST (00:00-06:30 UTC)
# NYSE/NASDAQ: Mon-Fri 09:30-16:00 EST (14:30-21:00 UTC)
# LSE: Mon-Fri 08:00-16:30 GMT (08:00-16:30 UTC)
# Combined: cover 00:00-21:00 UTC on weekdays

*/15 8-21 * * 1-5 cd ~/Developer/knoxur && python scripts/fetch_prices.py
```

### Daily Snapshot — end of day

```cron
# After all markets close (22:00 UTC)
0 22 * * 1-5 cd ~/Developer/knoxur && python scripts/daily_snapshot.py
```

---

## Build Phases

### Phase 1: Foundation (Backend + Data)
- [ ] SQLite database setup with all tables
- [ ] FastAPI app with account/holdings CRUD
- [ ] yfinance price fetcher service
- [ ] FX rate fetcher service
- [ ] Portfolio valuation logic (multi-currency)
- [ ] Seed script to add initial accounts and holdings
- [ ] API endpoints: GET portfolio summary, GET historical values

### Phase 2: Dashboard (Frontend)
- [ ] Vite + React + TypeScript setup
- [ ] Dashboard page: total portfolio value + daily change
- [ ] Portfolio value over time (line chart, Recharts)
- [ ] Per-account breakdown (stacked area chart)
- [ ] Holdings table with current prices and P&L
- [ ] Currency toggle (GBP / USD / KRW)
- [ ] Last updated timestamp + manual refresh button

### Phase 3: Automation + Polish
- [ ] Cron setup on Mac Mini (price fetch + daily snapshot)
- [ ] Production build (FastAPI serves React static files)
- [ ] Transaction logging (buy/sell history)
- [ ] Individual stock detail view
- [ ] Date range selector on charts
- [ ] Dark theme (match your terminal aesthetic)

### Phase 4: Nice-to-Have
- [ ] CLI tool for quick terminal checks (`knoxur summary`)
- [ ] Dividend tracking
- [ ] Tax report helper (capital gains per account)
- [ ] Alerts (price drops > X%, portfolio milestone reached)
- [ ] Mobile-responsive layout
