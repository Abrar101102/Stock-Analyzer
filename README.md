# Stock Analyzer

Full-stack stock analysis platform with an Angular frontend and a FastAPI backend for
fundamentals, technical indicators, valuation, news/sentiment, and screening workflows.

## Features

- Fundamental snapshots, ratios, and trend analysis
- Technical indicators and trading signals
- News and sentiment insights
- Sector comparison and screener endpoints
- Valuation metrics and peer comparisons
- Background ingestion/scheduler jobs

## Tech Stack

- **Frontend:** Angular 21, RxJS, ng-zorro-antd, chart.js
- **Backend:** FastAPI, SQLAlchemy, APScheduler, pandas/numpy/scikit-learn
- **Data sources:** Yahoo Finance, Alpha Vantage, Screener.in
- **Database:** PostgreSQL (Redis optional for caching)

## Repository Structure

```
frontend/   # Angular SPA
backend/    # FastAPI app and services
backend.md  # Backend architecture walkthrough
```

## Prerequisites

- Node.js + npm
- Python 3.12+
- PostgreSQL
- Optional: Redis for caching
- API keys for Alpha Vantage, News API, and FRED (plus Gemini if using LLM features)

## Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configuration:

- Create `backend/.env` and set optional secrets such as `NEWS_API_KEY`, `GEMINI_API_KEY`,
  `FRED_API_KEY`, `LLM_*`, and `REDIS_URL`.
- Update `DATABASE_URL` and `ALPHA_VANTAGE_API_KEY` in `backend/app/core/config.py`
  to match your local database and credentials.

Run the API:

```bash
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm start
```

The frontend expects the API at `http://localhost:8000/api` (see
`frontend/src/environments/environment.ts`).

## Tests

```bash
# frontend
cd frontend
npm test

# backend
cd backend
python -m pytest
```

Backend tests require a running PostgreSQL instance and optional Redis, plus any required API keys.

## Additional Docs

- `backend.md` for backend architecture and module details
- `backend/providers.md` for data provider notes
- `backend/RoadMap.md` for planned features