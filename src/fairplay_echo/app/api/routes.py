"""HTTP uçları — yalnız parse → servis → serialize.

Para alanları (`stake`) **string** kabul edilir ve string döner: JSON `float`'ı parasal hassasiyeti
bozar. `float` gönderilirse doğrulama reddeder.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Header, status
from pydantic import BaseModel, Field, field_validator, model_validator

from ...repo import UserRecord
from ..deps import get_current_user, get_service
from ..services import PortfolioService

router = APIRouter(prefix="/api", tags=["fairplay"])


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    username: str
    password: str


class WagerRequest(BaseModel):
    match_id: str
    market_type: str = "1X2"
    selection: str = "HOME"
    stake: Decimal
    probability: Decimal | None = None
    #: Kasa eşiğini aşan bahis, kullanıcı onayı olmadan işlenmez (spec §3.4). İstemci 409'daki
    #: `ruin` uyarısını gösterip onay alırsa **aynı istek** bu bayrak `true` ile tekrar gönderilir.
    confirm_ruin: bool = False

    @field_validator("stake", mode="before")
    @classmethod
    def _reject_float(cls, value: object) -> object:
        if isinstance(value, float):
            raise ValueError("stake'i string gönderin; float parasal hassasiyeti bozar.")
        return value

    @field_validator("stake")
    @classmethod
    def _positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("stake pozitif olmalı.")
        return value

    @field_validator("probability", mode="before")
    @classmethod
    def _reject_float_probability(cls, value: object) -> object:
        if isinstance(value, float):
            raise ValueError("probability'i string gönderin (ör. \"0.55\").")
        return value

    @field_validator("probability")
    @classmethod
    def _probability_in_range(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and not 0 < value < 1:
            raise ValueError("probability 0 ile 1 arasında olmalı (ör. 0.55).")
        return value


class EstimateRequest(BaseModel):
    """Kullanıcının kendi olasılık tahmininden EV/Kelly — bahis oynamadan danışma."""

    match_id: str
    market_type: str = "1X2"
    selection: str = "HOME"
    probability: Decimal

    @field_validator("probability", mode="before")
    @classmethod
    def _reject_float(cls, value: object) -> object:
        if isinstance(value, float):
            raise ValueError("probability'i string gönderin (ör. \"0.55\").")
        return value

    @field_validator("probability")
    @classmethod
    def _probability_in_range(cls, value: Decimal) -> Decimal:
        if not 0 < value < 1:
            raise ValueError("probability 0 ile 1 arasında olmalı (ör. 0.55).")
        return value


class SimulateRequest(BaseModel):
    match_id: str
    seed: int | None = None


class MonteCarloRequest(BaseModel):
    """Monte Carlo analizi — `match_id` (katalog) **veya** ham `odds_1x2` (varsayımsal senaryo).

    İkisi birlikte verilemez: oranın kaynağı belirsizleşir. Hiçbiri verilmezse 400.
    """

    match_id: str | None = None
    odds_1x2: dict[str, Decimal] | None = None
    iterations: int = Field(default=10_000, ge=1, le=200_000)
    seed: int | None = None

    @model_validator(mode="after")
    def _exactly_one_source(self) -> MonteCarloRequest:
        if (self.match_id is None) == (self.odds_1x2 is None):
            raise ValueError("match_id veya odds_1x2'den tam olarak biri verilmeli.")
        return self


def _auth_payload(user: UserRecord, token: str) -> dict[str, object]:
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "email": user.email},
    }


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(
    req: RegisterRequest, service: PortfolioService = Depends(get_service)
) -> dict[str, object]:
    user, token = service.register(username=req.username, email=req.email, password=req.password)
    return _auth_payload(user, token)


@router.post("/auth/login")
def login(req: LoginRequest, service: PortfolioService = Depends(get_service)) -> dict[str, object]:
    user, token = service.login(username=req.username, password=req.password)
    return _auth_payload(user, token)


@router.get("/fixtures")
def fixtures(service: PortfolioService = Depends(get_service)) -> dict[str, object]:
    return {"fixtures": service.fixtures()}


@router.get("/portfolio")
def portfolio(
    user: UserRecord = Depends(get_current_user),
    service: PortfolioService = Depends(get_service),
) -> dict[str, object]:
    return service.portfolio(user_id=user.id)


@router.get("/learning-report")
def learning_report(
    user: UserRecord = Depends(get_current_user),
    service: PortfolioService = Depends(get_service),
) -> dict[str, object]:
    """Öğrenme ölçütleri (docs/90): kullanıcının kendi davranışı — tavsiye değil."""
    return service.learning_report(user_id=user.id)


@router.post("/wager", status_code=status.HTTP_201_CREATED)
def place_wager(
    req: WagerRequest,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    user: UserRecord = Depends(get_current_user),
    service: PortfolioService = Depends(get_service),
) -> dict[str, object]:
    return service.place_wager(
        user_id=user.id,
        match_id=req.match_id,
        market_type=req.market_type,
        selection=req.selection,
        stake=req.stake,
        probability=req.probability,
        confirm_ruin=req.confirm_ruin,
        idempotency_key=idempotency_key,
    )


@router.post("/estimate")
def estimate(
    req: EstimateRequest,
    user: UserRecord = Depends(get_current_user),
    service: PortfolioService = Depends(get_service),
) -> dict[str, object]:
    """Bahis oynamadan danışma: kullanıcının olasılığından EV, Kelly ve önerilen stake."""
    return service.estimate(
        user_id=user.id,
        match_id=req.match_id,
        market_type=req.market_type,
        selection=req.selection,
        probability=req.probability,
    )


@router.post("/refill")
def refill(
    user: UserRecord = Depends(get_current_user),
    service: PortfolioService = Depends(get_service),
) -> dict[str, object]:
    return service.refill(user_id=user.id)


@router.post("/matches/simulate")
def simulate(
    req: SimulateRequest,
    user: UserRecord = Depends(get_current_user),
    service: PortfolioService = Depends(get_service),
) -> dict[str, object]:
    return service.simulate_match(user_id=user.id, match_id=req.match_id, seed=req.seed)


@router.post("/matches/monte_carlo")
def monte_carlo(
    req: MonteCarloRequest,
    user: UserRecord = Depends(get_current_user),
    service: PortfolioService = Depends(get_service),
) -> dict[str, object]:
    """Sonuç dağılımı analizi — bahis oynatmaz, kupon açmaz."""
    return service.monte_carlo(
        user_id=user.id,
        match_id=req.match_id,
        odds_1x2=req.odds_1x2,
        iterations=req.iterations,
        seed=req.seed,
    )
