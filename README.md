# FairPlay Simulator ⚽📊

> **⚠️ IMPORTANT DISCLAIMER:**
> **FairPlay is a non-gambling, educational sports analytics and portfolio simulation platform.**
> **No real money is deposited, wagered, won, or lost.** All balances, odds, and returns are strictly virtual and designed for mathematical risk analysis and educational purposes.

---

## 🎯 Overview & Philosophy

Most sports betting applications encourage reckless gambling behavior through dopamine-driven loops. **FairPlay** flips the script: it treats sports predictions as **financial portfolio investments** using **mutual fund accounting (GIPS-compliant Unit NAV)**, the **Kelly Criterion**, and mathematical risk management.

### Key Highlights
- **Unit NAV Accounting:** Eliminates the distortion of virtual balance refills. Your NAV measures pure predictive skill over time.
- **Bookmaker Vig & Fair Odds Normalizer:** Automatically strips out bookmaker margins (overround) to show true market implied probabilities.
- **Responsible Gaming & Anti-Ruin Protection:** Built-in Kelly Criterion stake suggestions and exponential cooldown lockout upon insolvency to discourage reckless all-in bets.
- **Dual Gameplay Modes:**
  1. *Matchday Fund Manager (Live Weekends):* Allocate weekly risk units on real-world upcoming fixtures.
  2. *Historical Sandbox (Time Machine):* Backtest strategies against historical seasons in fast-forward simulation.

---

## 📁 Repository Structure

```text
fairplay_simulator_src/
├── docs/                       # Architecture, GDD, Research & Roadmap
│   ├── ROADMAP.md              # Master Blueprint & Phased Development Backlog
│   ├── architecture/           # System Topology, DB Schema, Verification Strategy
│   ├── research/               # NAV Accounting & Odds Ingestion Research
│   └── agents/                 # Multi-Agent Guideline Specifications
├── src/
│   ├── backend/                # FastAPI Application & Database Models
│   │   ├── nav_engine.py       # GIPS Unit NAV Accounting Engine
│   │   ├── cooldown_engine.py  # Exponential Backoff & Tier Decay Engine
│   │   └── models/             # Database & Persistence Schemas
│   ├── data_ingestion/         # Fixture & Odds Ingestion (The Odds API, Football-Data.org)
│   └── frontend/               # Interactive Simulation Dashboard (Tailwind + Chart.js)
├── tests/                      # Mathematical & API Unit Test Suite
├── requirements.txt            # Pinned Python dependencies
├── run_demo.py                 # Backend Server Entrypoint
└── .env.example                # Sample Environment Configuration
```

---

## 🚀 Quick Start (Local Development)

### 1. Requirements
- Python 3.10+
- Tüm bağımlılıklar `requirements.txt` içinde sabitlenmiştir.

```bash
pip install -r requirements.txt
```

### 2. Run the Backend
```bash
python run_demo.py
```
The API server will start at http://localhost:8000.

### 3. Open the Frontend
Open http://localhost:8000 in your browser (the backend serves `src/frontend/index.html`),
or open `src/frontend/index.html` directly as a local file.

### 4. Run Test Suite
```bash
python -m unittest discover tests
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and fill in the values you need:

| Variable | Purpose |
| -------- | ------- |
| `JWT_SECRET_KEY` | Signs auth tokens. If unset, a random key is generated per start — fast to try, but tokens become invalid on restart. |
| `FOOTBALL_DATA_API_KEY` | Fixtures/scores feed (not used yet; mock data is served by default). |
| `ODDS_API_KEY` | Odds feed (not used yet; mock data is served by default). |
| `DATABASE_URL` | SQLAlchemy URL. Defaults to `sqlite:///./fairplay.db`. |
| `CORS_ORIGINS` | Comma-separated allowed browser origins. Defaults to localhost plus `null` (needed when the frontend is opened as a `file://` page). |

---

## 🗺️ Roadmap & Development Plan

See [docs/ROADMAP.md](docs/ROADMAP.md) for the active development backlog and architectural specifications.

> **Not:** `docs/architecture/` ve `docs/ROADMAP.md` **hedef (target) mimariyi** anlatır
> (PostgreSQL + TimescaleDB + Redis, mikroservis topolojisi). Çalışan kod ise tek bir FastAPI
> süreci + SQLAlchemy/SQLite üzerinde durur; aradaki fark planlı bir yol haritasıdır, uygulanmış
> bir mimari değildir.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
