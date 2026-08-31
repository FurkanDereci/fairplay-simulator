from datetime import datetime, timedelta, timezone
from typing import Dict, Any

class CooldownEngine:
    """Manages Exponential Backoff Cooldown Lockouts & Tier Decay for Bankruptcy Recovery."""
    
    @staticmethod
    def calculate_cooldown_hours(tier: int) -> float:
        """T(n) = min(168, 1.0 * 4^(n-1)) hours."""
        if tier < 1:
            return 0.0
        return min(168.0, 1.0 * (4.0 ** (tier - 1)))

    def __init__(self):
        self.bankruptcy_tier: int = 0
        self.solvent_days_streak: int = 0
        self.status: str = "ACTIVE"  # 'ACTIVE', 'COOLDOWN_LOCKED'
        self.cooldown_expires_at: datetime | None = None

    def trigger_bankruptcy(self, now: datetime | None = None) -> Dict[str, Any]:
        """Triggers exponential cooldown lockout upon bankroll depletion."""
        now = now or datetime.now(timezone.utc)
        self.bankruptcy_tier += 1
        self.solvent_days_streak = 0
        self.status = "COOLDOWN_LOCKED"
        
        lockout_hours = self.calculate_cooldown_hours(self.bankruptcy_tier)
        self.cooldown_expires_at = now + timedelta(hours=lockout_hours)
        
        return {
            "status": self.status,
            "tier": self.bankruptcy_tier,
            "lockout_hours": lockout_hours,
            "expires_at": self.cooldown_expires_at.isoformat()
        }

    def check_and_unlock(self, now: datetime | None = None) -> bool:
        """Checks if current cooldown lockout period has elapsed."""
        now = now or datetime.now(timezone.utc)
        if self.status == "COOLDOWN_LOCKED" and self.cooldown_expires_at:
            if now >= self.cooldown_expires_at:
                self.status = "ACTIVE"
                self.cooldown_expires_at = None
                return True
        return self.status == "ACTIVE"

    def record_solvent_day(self):
        """Records an active solvent day and decays bankruptcy tier every 3 consecutive days."""
        self.solvent_days_streak += 1
        if self.solvent_days_streak >= 3:
            self.solvent_days_streak = 0
            if self.bankruptcy_tier > 0:
                self.bankruptcy_tier -= 1
