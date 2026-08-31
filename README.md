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

`
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
├── run_demo.py                 # Backend Server Entrypoint
└── .env.example                # Sample Environment Configuration
`

---

## 🚀 Quick Start (Local Development)

### 1. Requirements
- Python 3.10+
- FastAPI, Uvicorn, Requests

### 2. Run the Backend
`ash
python run_demo.py
`
The API server will start at http://localhost:8000.

### 3. Open the Frontend
Open src/frontend/index.html in your favorite web browser.

### 4. Run Test Suite
`ash
python -m unittest discover tests
`

---

## 🗺️ Roadmap & Development Plan

See [docs/ROADMAP.md](docs/ROADMAP.md) for the active development backlog and architectural specifications.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
