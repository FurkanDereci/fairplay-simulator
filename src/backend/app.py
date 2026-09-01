import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.backend.models.database import (
    get_db, init_db, UserModel, UserBalanceModel, CooldownStateModel, WagerModel, NAVHistoryModel
)
from src.backend.auth import hash_password, verify_password, create_access_token, decode_access_token
from src.backend.cooldown_engine import CooldownEngine
from src.backend.match_engine import VirtualMatchEngine
from src.backend.benchmark_engine import BenchmarkManager
from src.data_ingestion.mock_data_generator import MockDataGenerator

init_db()

app = FastAPI(title="FairPlay Football Simulator API", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cached_fixtures = MockDataGenerator.generate_fixtures_and_odds()
benchmark_manager = BenchmarkManager()

@app.get("/")
def serve_root():
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return {"message": "FairPlay Football Simulator API v2.1.0"}

class UserRegisterRequest(BaseModel):
    email: str
    username: str
    password: str

class UserLoginRequest(BaseModel):
    username: str
    password: str

class WagerRequest(BaseModel):
    match_id: str
    market_type: str = "1X2"
    selection: str = "HOME"
    stake: float

class WagerSettleRequest(BaseModel):
    wager_id: str
    won: bool

def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header.")
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return payload["sub"]

@app.post("/api/auth/register")
def register_user(req: UserRegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(UserModel).filter(
        (UserModel.email == req.email) | (UserModel.username == req.username)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists.")
    
    user_id = str(uuid.uuid4())
    pwd_hash = hash_password(req.password)
    
    user = UserModel(id=user_id, email=req.email, username=req.username, password_hash=pwd_hash)
    balance = UserBalanceModel(
        user_id=user_id, cash_balance=1000.0, locked_stakes=0.0, simulation_energy=100, total_units=10.0, series_id=1
    )
    cooldown = CooldownStateModel(user_id=user_id, current_tier=0, status="ACTIVE")
    initial_nav = NAVHistoryModel(
        user_id=user_id, series_id=1, nav=100.0, cash_balance=1000.0, locked_stakes=0.0,
        total_units=10.0, tx_type="INITIAL_DEPOSIT", amount=1000.0
    )
    
    db.add_all([user, balance, cooldown, initial_nav])
    db.commit()

    token = create_access_token({"sub": user_id, "username": req.username})
    return {
        "message": "Registration successful",
        "access_token": token,
        "user": {"id": user_id, "username": req.username, "email": req.email}
    }

@app.post("/api/auth/login")
def login_user(req: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    
    token = create_access_token({"sub": user.id, "username": user.username})
    return {
        "message": "Login successful",
        "access_token": token,
        "user": {"id": user.id, "username": user.username, "email": user.email}
    }

@app.get("/api/fixtures")
def get_fixtures():
    return {"fixtures": cached_fixtures}

@app.get("/api/portfolio")
def get_portfolio_status(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    bal = user.balance
    cd = user.cooldown
    
    # Auto-unlock cooldown if expired
    now = datetime.now(timezone.utc)
    if cd.status == "COOLDOWN_LOCKED" and cd.cooldown_expires_at:
        exp = cd.cooldown_expires_at if cd.cooldown_expires_at.tzinfo else cd.cooldown_expires_at.replace(tzinfo=timezone.utc)
        if now >= exp:
            cd.status = "ACTIVE"
            cd.cooldown_expires_at = None
            db.commit()

    total_value = bal.cash_balance + bal.locked_stakes
    current_nav = round(total_value / bal.total_units, 4) if bal.total_units > 0 else 0.0

    history = [
        {
            "timestamp": h.recorded_at.isoformat() if h.recorded_at else "",
            "nav": round(h.nav, 4),
            "cash": round(h.cash_balance, 2),
            "locked_stakes": round(h.locked_stakes, 2),
            "units": round(h.total_units, 4),
            "tx_type": h.tx_type,
            "amount": round(h.amount, 2)
        }
        for h in user.nav_history[-50:]
    ]

    return {
        "user_id": user.id,
        "username": user.username,
        "nav": current_nav,
        "cash_balance": round(bal.cash_balance, 2),
        "locked_stakes": round(bal.locked_stakes, 2),
        "total_portfolio_value": round(total_value, 2),
        "total_units": round(bal.total_units, 4),
        "series_id": bal.series_id,
        "nav_history": history,
        "benchmarks": benchmark_manager.get_benchmarks_summary(player_nav=current_nav),
        "cooldown_status": cd.status,
        "bankruptcy_tier": cd.current_tier
    }

@app.post("/api/wager")
def place_wager(req: WagerRequest, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    bal = user.balance
    cd = user.cooldown

    # Check cooldown
    now = datetime.now(timezone.utc)
    if cd.status == "COOLDOWN_LOCKED" and cd.cooldown_expires_at:
        exp = cd.cooldown_expires_at if cd.cooldown_expires_at.tzinfo else cd.cooldown_expires_at.replace(tzinfo=timezone.utc)
        if now < exp:
            raise HTTPException(status_code=423, detail=f"Account locked in Bankruptcy Cooldown Tier {cd.current_tier}.")
        else:
            cd.status = "ACTIVE"
            cd.cooldown_expires_at = None

    if req.stake <= 0 or req.stake > bal.cash_balance:
        raise HTTPException(status_code=400, detail="Invalid stake amount or insufficient cash balance.")

    # Find fixture odds (default to 2.0 if not in mock fixture list)
    odds = 2.0
    match_title = "Match Simulation"
    for f in cached_fixtures:
        if f.get("match_id") == req.match_id:
            match_title = f"{f.get('home_team')} vs {f.get('away_team')}"
            market = f.get("markets", {}).get(req.market_type, {})
            odds = market.get("outcomes", {}).get(req.selection, 2.0)
            break

    potential_payout = round(req.stake * odds, 2)
    ruin_risk_warning = req.stake > (0.15 * bal.cash_balance)

    # Balance transaction
    bal.cash_balance -= req.stake
    bal.locked_stakes += req.stake
    if bal.simulation_energy >= 10:
        bal.simulation_energy -= 10

    total_value = bal.cash_balance + bal.locked_stakes
    current_nav = round(total_value / bal.total_units, 4) if bal.total_units > 0 else 0.0

    wager = WagerModel(
        user_id=user.id,
        match_id=req.match_id,
        match_title=match_title,
        market_type=req.market_type,
        selection=req.selection,
        stake=req.stake,
        odds=odds,
        potential_payout=potential_payout,
        status="PENDING"
    )

    nav_record = NAVHistoryModel(
        user_id=user.id,
        series_id=bal.series_id,
        nav=current_nav,
        cash_balance=bal.cash_balance,
        locked_stakes=bal.locked_stakes,
        total_units=bal.total_units,
        tx_type="BET_STAKE",
        amount=-req.stake
    )

    db.add_all([wager, nav_record])
    db.commit()

    return {
        "message": "Wager placed successfully",
        "wager_id": wager.id,
        "stake": req.stake,
        "odds": odds,
        "potential_payout": potential_payout,
        "remaining_cash": round(bal.cash_balance, 2),
        "nav": current_nav,
        "ruin_risk_warning": ruin_risk_warning,
        "warning_message": "⚠️ Stake exceeds 15% of bankroll! High probability of portfolio ruin." if ruin_risk_warning else None
    }

@app.post("/api/wager/settle")
def settle_wager(req: WagerSettleRequest, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    wager = db.query(WagerModel).filter(WagerModel.id == req.wager_id, WagerModel.user_id == user_id).first()
    if not wager:
        raise HTTPException(status_code=404, detail="Wager not found.")
    if wager.status != "PENDING":
        raise HTTPException(status_code=400, detail="Wager already settled.")

    bal = wager.user.balance
    cd = wager.user.cooldown
    now = datetime.now(timezone.utc)

    payout = wager.potential_payout if req.won else 0.0
    wager.status = "WON" if req.won else "LOST"
    wager.payout = payout
    wager.settled_at = now

    bal.locked_stakes = max(0.0, bal.locked_stakes - wager.stake)
    bal.cash_balance += payout

    total_value = bal.cash_balance + bal.locked_stakes
    current_nav = round(total_value / bal.total_units, 4) if bal.total_units > 0 else 0.0

    nav_record = NAVHistoryModel(
        user_id=user_id,
        series_id=bal.series_id,
        nav=current_nav,
        cash_balance=bal.cash_balance,
        locked_stakes=bal.locked_stakes,
        total_units=bal.total_units,
        tx_type="BET_PAYOUT",
        amount=payout - wager.stake
    )

    # Check insolvency / bankruptcy condition
    bankruptcy_triggered = False
    if bal.cash_balance <= 0 and bal.locked_stakes <= 0:
        bankruptcy_triggered = True
        cd.current_tier += 1
        cd.solvent_days_streak = 0
        cd.status = "COOLDOWN_LOCKED"
        lockout_hours = CooldownEngine.calculate_cooldown_hours(cd.current_tier)
        cd.cooldown_expires_at = now + timedelta(hours=lockout_hours)

    db.add(nav_record)
    db.commit()

    return {
        "message": f"Wager settled as {wager.status}",
        "wager_id": wager.id,
        "status": wager.status,
        "payout": payout,
        "cash_balance": round(bal.cash_balance, 2),
        "nav": current_nav,
        "bankruptcy_triggered": bankruptcy_triggered,
        "cooldown_status": cd.status,
        "bankruptcy_tier": cd.current_tier
    }

@app.post("/api/refill")
def request_refill(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    bal = user.balance
    cd = user.cooldown
    now = datetime.now(timezone.utc)

    # Check cooldown lockout
    if cd.status == "COOLDOWN_LOCKED" and cd.cooldown_expires_at:
        exp = cd.cooldown_expires_at if cd.cooldown_expires_at.tzinfo else cd.cooldown_expires_at.replace(tzinfo=timezone.utc)
        if now < exp:
            raise HTTPException(status_code=423, detail="Refill disabled during active cooldown lockout.")
        else:
            cd.status = "ACTIVE"
            cd.cooldown_expires_at = None

    refill_amount = 1000.0
    total_val = bal.cash_balance + bal.locked_stakes
    
    if total_val <= 0 or bal.total_units <= 0:
        # Re-unitization after full bankruptcy
        bal.series_id += 1
        bal.cash_balance = refill_amount
        bal.locked_stakes = 0.0
        bal.total_units = 10.0
        current_nav = 100.0
    else:
        current_nav = total_val / bal.total_units
        new_units = refill_amount / current_nav
        bal.total_units += new_units
        bal.cash_balance += refill_amount

    nav_record = NAVHistoryModel(
        user_id=user.id,
        series_id=bal.series_id,
        nav=round(current_nav, 4),
        cash_balance=bal.cash_balance,
        locked_stakes=bal.locked_stakes,
        total_units=bal.total_units,
        tx_type="REFILL_DEPOSIT",
        amount=refill_amount
    )

    db.add(nav_record)
    db.commit()

    return {
        "message": "1,000 TL virtual balance refill granted.",
        "cash_balance": round(bal.cash_balance, 2),
        "nav": round(current_nav, 4),
        "units": round(bal.total_units, 4)
    }

class MatchSimulateRequest(BaseModel):
    match_id: str
    seed: Optional[int] = None

class MonteCarloRequest(BaseModel):
    odds_1x2: Dict[str, float]
    iterations: Optional[int] = 10000

@app.post("/api/matches/simulate")
def simulate_match_and_settle(req: MatchSimulateRequest, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Find fixture
    fixture = None
    for f in cached_fixtures:
        if f.get("match_id") == req.match_id:
            fixture = f
            break

    home_team = fixture.get("home_team", "Home Team") if fixture else "Home Team"
    away_team = fixture.get("away_team", "Away Team") if fixture else "Away Team"
    market_1x2 = fixture.get("markets", {}).get("1X2", {}).get("outcomes", {"HOME": 2.0, "DRAW": 3.4, "AWAY": 3.8}) if fixture else {"HOME": 2.0, "DRAW": 3.4, "AWAY": 3.8}

    # Simulate match
    match_result = VirtualMatchEngine.simulate_match(
        match_id=req.match_id,
        home_team=home_team,
        away_team=away_team,
        odds_1x2=market_1x2,
        seed=req.seed
    )

    # Auto-settle any pending wagers for this user on this match
    pending_wagers = db.query(WagerModel).filter(
        WagerModel.user_id == user.id,
        WagerModel.match_id == req.match_id,
        WagerModel.status == "PENDING"
    ).all()

    bal = user.balance
    cd = user.cooldown
    now = datetime.now(timezone.utc)
    settled_wagers_summary = []

    for w in pending_wagers:
        won = False
        if w.market_type == "1X2":
            won = (w.selection == match_result.outcome_1x2)
        elif w.market_type == "OVER_UNDER_2.5":
            won = (w.selection == match_result.outcome_ou_25)
        elif w.market_type == "BTTS":
            won = (w.selection == match_result.outcome_btts)

        payout = w.potential_payout if won else 0.0
        w.status = "WON" if won else "LOST"
        w.payout = payout
        w.settled_at = now

        bal.locked_stakes = max(0.0, bal.locked_stakes - w.stake)
        bal.cash_balance += payout

        total_value = bal.cash_balance + bal.locked_stakes
        current_nav = round(total_value / bal.total_units, 4) if bal.total_units > 0 else 0.0

        nav_record = NAVHistoryModel(
            user_id=user.id,
            series_id=bal.series_id,
            nav=current_nav,
            cash_balance=bal.cash_balance,
            locked_stakes=bal.locked_stakes,
            total_units=bal.total_units,
            tx_type="BET_PAYOUT",
            amount=payout - w.stake
        )
        db.add(nav_record)

        settled_wagers_summary.append({
            "wager_id": w.id,
            "selection": w.selection,
            "status": w.status,
            "payout": payout,
            "net_gain": round(payout - w.stake, 2)
        })

    # Check bankruptcy
    bankruptcy_triggered = False
    if bal.cash_balance <= 0 and bal.locked_stakes <= 0:
        bankruptcy_triggered = True
        cd.current_tier += 1
        cd.solvent_days_streak = 0
        cd.status = "COOLDOWN_LOCKED"
        lockout_hours = CooldownEngine.calculate_cooldown_hours(cd.current_tier)
        cd.cooldown_expires_at = now + timedelta(hours=lockout_hours)

    # Process systematic benchmark bots on this match
    benchmark_manager.process_match(
        match_id=req.match_id,
        market_1x2=market_1x2,
        outcome_1x2=match_result.outcome_1x2,
        seed=req.seed
    )

    db.commit()

    total_value = bal.cash_balance + bal.locked_stakes
    final_nav = round(total_value / bal.total_units, 4) if bal.total_units > 0 else 0.0

    return {
        "match_id": req.match_id,
        "home_team": match_result.home_team,
        "away_team": match_result.away_team,
        "score": f"{match_result.home_score} - {match_result.away_score}",
        "home_score": match_result.home_score,
        "away_score": match_result.away_score,
        "outcomes": {
            "1X2": match_result.outcome_1x2,
            "OVER_UNDER_2.5": match_result.outcome_ou_25,
            "BTTS": match_result.outcome_btts
        },
        "events": [
            {"minute": e.minute, "team": e.team, "type": e.event_type, "description": e.description}
            for e in match_result.events
        ],
        "settled_wagers": settled_wagers_summary,
        "portfolio": {
            "cash_balance": round(bal.cash_balance, 2),
            "locked_stakes": round(bal.locked_stakes, 2),
            "nav": final_nav,
            "bankruptcy_triggered": bankruptcy_triggered,
            "cooldown_status": cd.status
        },
        "benchmarks": benchmark_manager.get_benchmarks_summary(player_nav=final_nav)
    }

@app.post("/api/matches/monte_carlo")
def run_monte_carlo_analysis(req: MonteCarloRequest):
    lh, la = VirtualMatchEngine.derive_lambdas(req.odds_1x2)
    mc_result = VirtualMatchEngine.run_monte_carlo(
        lambda_home=lh,
        lambda_away=la,
        iterations=req.iterations or 10000
    )
    return {
        "lambda_home": lh,
        "lambda_away": la,
        "monte_carlo": mc_result.__dict__
    }
