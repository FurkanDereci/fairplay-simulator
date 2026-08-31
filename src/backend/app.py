import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from src.backend.models.sqlite_db import get_db_connection, init_sqlite_db
from src.backend.auth_jwt import hash_password, verify_password, create_jwt, decode_jwt
from src.data_ingestion.mock_data_generator import MockDataGenerator
from src.backend.nav_engine import NAVPortfolioEngine
from src.backend.cooldown_engine import CooldownEngine

init_sqlite_db()

app = FastAPI(title="FairPlay Football Simulator API", version="2.0.0")

user_portfolios: Dict[str, NAVPortfolioEngine] = {}
user_cooldowns: Dict[str, CooldownEngine] = {}
cached_fixtures = MockDataGenerator.generate_fixtures_and_odds()

class UserRegisterRequest(BaseModel):
    email: str
    username: str
    password: str

class UserLoginRequest(BaseModel):
    username: str
    password: str

class WagerRequest(BaseModel):
    match_id: str
    market_type: str
    selection: str
    stake: float

def get_current_user_payload(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header.")
    token = authorization.split(" ")[1]
    payload = decode_jwt(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return payload

@app.post("/api/auth/register")
def register_user(req: UserRegisterRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE email = ? OR username = ?", (req.email, req.username))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username or email already exists.")
    
    user_id = str(uuid.uuid4())
    now_str = datetime.now(timezone.utc).isoformat()
    pwd_hash = hash_password(req.password)
    
    cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (user_id, req.email, req.username, pwd_hash, now_str))
    cursor.execute("INSERT INTO user_balances VALUES (?, 1000.0, 0.0, 100)", (user_id,))
    cursor.execute("INSERT INTO cooldown_states VALUES (?, 0, 'ACTIVE', NULL)", (user_id,))
    conn.commit()
    conn.close()

    token = create_jwt({"sub": user_id, "username": req.username})
    user_portfolios[user_id] = NAVPortfolioEngine(initial_balance=1000.0, base_nav=100.0)
    user_cooldowns[user_id] = CooldownEngine()

    return {
        "message": "Registration successful",
        "access_token": token,
        "user": {"id": user_id, "username": req.username, "email": req.email}
    }

@app.post("/api/auth/login")
def login_user(req: UserLoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, username, password_hash FROM users WHERE username = ?", (req.username,))
    row = cursor.fetchone()
    conn.close()

    if not row or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    
    user_id = row["id"]
    token = create_jwt({"sub": user_id, "username": row["username"]})
    if user_id not in user_portfolios:
        user_portfolios[user_id] = NAVPortfolioEngine(initial_balance=1000.0, base_nav=100.0)
        user_cooldowns[user_id] = CooldownEngine()

    return {
        "message": "Login successful",
        "access_token": token,
        "user": {"id": user_id, "username": row["username"], "email": row["email"]}
    }

@app.get("/api/fixtures")
def get_fixtures():
    return {"fixtures": cached_fixtures}

@app.get("/api/portfolio")
def get_portfolio_status(authorization: Optional[str] = Header(None)):
    auth = get_current_user_payload(authorization)
    user_id = auth["sub"]
    p = user_portfolios.setdefault(user_id, NAVPortfolioEngine(1000.0, 100.0))
    c = user_cooldowns.setdefault(user_id, CooldownEngine())
    
    current_nav = p.nav
    return {
        "user_id": user_id,
        "username": auth.get("username", "User"),
        "nav": round(p.nav, 4),
        "cash_balance": round(p.cash_balance, 2),
        "locked_stakes": round(p.locked_stakes, 2),
        "total_portfolio_value": round(p.total_portfolio_value, 2),
        "total_units": round(p.total_units, 4),
        "series_id": p.series_id,
        "nav_history": p.nav_history,
        "benchmarks": {
            "player_nav": round(current_nav, 2),
            "random_walk_index": round(100.0 * (current_nav / 100.0) ** 0.8, 2),
            "favorite_heavy_index": round(100.0 * (current_nav / 100.0) ** 1.1, 2),
            "home_advantage_index": round(100.0 * (current_nav / 100.0) ** 0.95, 2)
        },
        "cooldown_status": c.status,
        "bankruptcy_tier": c.bankruptcy_tier
    }

@app.post("/api/wager")
def place_wager(req: WagerRequest, authorization: Optional[str] = Header(None)):
    auth = get_current_user_payload(authorization)
    user_id = auth["sub"]
    p = user_portfolios.setdefault(user_id, NAVPortfolioEngine(1000.0, 100.0))
    c = user_cooldowns.setdefault(user_id, CooldownEngine())

    if not c.check_and_unlock():
        raise HTTPException(status_code=423, detail=f"Account locked in Bankruptcy Cooldown Tier {c.bankruptcy_tier}.")

    if req.stake > p.cash_balance:
        raise HTTPException(status_code=400, detail="Insufficient available cash balance.")

    ruin_risk_warning = req.stake > (0.15 * p.cash_balance)
    success = p.place_wager(req.stake)
    if not success:
        raise HTTPException(status_code=400, detail="Wager placement failed.")

    return {
        "message": "Wager placed successfully",
        "stake": req.stake,
        "remaining_cash": round(p.cash_balance, 2),
        "nav": round(p.nav, 4),
        "ruin_risk_warning": ruin_risk_warning,
        "warning_message": "⚠️ Stake exceeds 15% of bankroll! High probability of portfolio ruin." if ruin_risk_warning else None
    }

@app.post("/api/refill")
def request_refill(authorization: Optional[str] = Header(None)):
    auth = get_current_user_payload(authorization)
    user_id = auth["sub"]
    p = user_portfolios.setdefault(user_id, NAVPortfolioEngine(1000.0, 100.0))
    c = user_cooldowns.setdefault(user_id, CooldownEngine())

    if c.status == "COOLDOWN_LOCKED" and not c.check_and_unlock():
        raise HTTPException(status_code=423, detail="Refill disabled during active cooldown lockout.")

    p.deposit_refill(1000.0)
    return {
        "message": "1,000 TL virtual balance refill granted.",
        "cash_balance": round(p.cash_balance, 2),
        "nav": round(p.nav, 4),
        "units": round(p.total_units, 4)
    }
