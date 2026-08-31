import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class UserModel(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    balance = relationship("UserBalanceModel", back_populates="user", uselist=False)
    cooldown = relationship("CooldownStateModel", back_populates="user", uselist=False)

class UserBalanceModel(Base):
    __tablename__ = "user_balances"
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    cash_balance = Column(Float, default=1000.0)
    locked_stakes = Column(Float, default=0.0)
    simulation_energy = Column(Integer, default=100)
    last_energy_update = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("UserModel", back_populates="balance")

class CooldownStateModel(Base):
    __tablename__ = "cooldown_states"
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    current_tier = Column(Integer, default=0)
    solvent_days_streak = Column(Integer, default=0)
    status = Column(String(20), default="ACTIVE")  # 'ACTIVE', 'COOLDOWN_LOCKED'
    cooldown_expires_at = Column(DateTime, nullable=True)

    user = relationship("UserModel", back_populates="cooldown")

# SQLite Database Engine for Local Dev / Testing
DATABASE_URL = "sqlite:////working_dir/c_a88f28dd458ad1b3/fairplay.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
