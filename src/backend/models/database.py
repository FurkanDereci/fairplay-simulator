import os
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class UserModel(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    balance = relationship("UserBalanceModel", back_populates="user", uselist=False, cascade="all, delete-orphan")
    cooldown = relationship("CooldownStateModel", back_populates="user", uselist=False, cascade="all, delete-orphan")
    wagers = relationship("WagerModel", back_populates="user", cascade="all, delete-orphan")
    nav_history = relationship("NAVHistoryModel", back_populates="user", cascade="all, delete-orphan")

class UserBalanceModel(Base):
    __tablename__ = "user_balances"
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    cash_balance = Column(Float, default=1000.0, nullable=False)
    locked_stakes = Column(Float, default=0.0, nullable=False)
    simulation_energy = Column(Integer, default=100, nullable=False)
    total_units = Column(Float, default=10.0, nullable=False)
    series_id = Column(Integer, default=1, nullable=False)
    last_energy_update = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("UserModel", back_populates="balance")

class CooldownStateModel(Base):
    __tablename__ = "cooldown_states"
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    current_tier = Column(Integer, default=0, nullable=False)
    solvent_days_streak = Column(Integer, default=0, nullable=False)
    status = Column(String(20), default="ACTIVE", nullable=False)
    cooldown_expires_at = Column(DateTime, nullable=True)

    user = relationship("UserModel", back_populates="cooldown")

class WagerModel(Base):
    __tablename__ = "wagers"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    match_id = Column(String(100), nullable=False)
    league = Column(String(100), nullable=True)
    match_title = Column(String(200), nullable=True)
    market_type = Column(String(50), nullable=False)  # '1X2', 'OVER_UNDER_2.5'
    selection = Column(String(50), nullable=False)    # 'HOME', 'DRAW', 'AWAY'
    stake = Column(Float, nullable=False)
    odds = Column(Float, nullable=False)
    potential_payout = Column(Float, nullable=False)
    status = Column(String(20), default="PENDING", nullable=False)  # 'PENDING', 'WON', 'LOST', 'VOID'
    payout = Column(Float, default=0.0, nullable=False)
    placed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    settled_at = Column(DateTime, nullable=True)

    user = relationship("UserModel", back_populates="wagers")

class NAVHistoryModel(Base):
    __tablename__ = "nav_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    series_id = Column(Integer, default=1, nullable=False)
    nav = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    locked_stakes = Column(Float, nullable=False)
    total_units = Column(Float, nullable=False)
    tx_type = Column(String(50), nullable=False)  # 'INITIAL_DEPOSIT', 'REFILL_DEPOSIT', 'BET_STAKE', 'BET_PAYOUT'
    amount = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("UserModel", back_populates="nav_history")

# Cross-platform Database Engine (Environment configurable, SQLite default for local development)
class BenchmarkNAVHistoryModel(Base):
    __tablename__ = "benchmark_nav_history"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(String(64), nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    random_walk_nav = Column(Float, default=100.0)
    favorite_heavy_nav = Column(Float, default=100.0)
    home_advantage_nav = Column(Float, default=100.0)
    step_index = Column(Integer, default=0)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fairplay.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db(target_engine=None):
    e = target_engine or engine
    Base.metadata.create_all(bind=e)
