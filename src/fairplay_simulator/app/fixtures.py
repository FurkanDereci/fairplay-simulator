"""Fikstür kataloğu.

Kimlikler **deterministik** (`md-01`…), rastgele üretilmez: aynı maç her çalıştırmada aynı kimliğe
sahip olur, böylece kuponlar ve maç kayıtları tutarlı kalır.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from ..core.money import ONE, Money, dec, q
from ..core.odds import ODDS_Q, NormalizedMarket, normalize_market

MARKET_1X2 = "1X2"
MARKET_OU_25 = "OVER_UNDER_2.5"
MARKET_BTTS = "BTTS"


@dataclass(frozen=True)
class Fixture:
    match_id: str
    league: str
    home_team: str
    away_team: str
    markets: dict[str, NormalizedMarket]

    @property
    def title(self) -> str:
        return f"{self.home_team} vs {self.away_team}"

    def odds_1x2(self) -> dict[str, Money]:
        return dict(self.markets[MARKET_1X2].outcomes)


_RAW: tuple[tuple[str, str, str, str, dict[str, dict[str, str]]], ...] = (
    (
        "md-01",
        "Premier League",
        "Arsenal",
        "Chelsea",
        {
            MARKET_1X2: {"HOME": "1.95", "DRAW": "3.50", "AWAY": "4.10"},
            MARKET_OU_25: {"OVER_2.5": "1.85", "UNDER_2.5": "2.02"},
            MARKET_BTTS: {"BTTS_YES": "1.78", "BTTS_NO": "2.12"},
        },
    ),
    (
        "md-02",
        "La Liga",
        "Real Madrid",
        "Barcelona",
        {
            MARKET_1X2: {"HOME": "2.20", "DRAW": "3.60", "AWAY": "3.10"},
            MARKET_OU_25: {"OVER_2.5": "1.70", "UNDER_2.5": "2.25"},
            MARKET_BTTS: {"BTTS_YES": "1.65", "BTTS_NO": "2.30"},
        },
    ),
    (
        "md-03",
        "Serie A",
        "Inter Milan",
        "AC Milan",
        {
            MARKET_1X2: {"HOME": "2.05", "DRAW": "3.40", "AWAY": "3.80"},
            MARKET_OU_25: {"OVER_2.5": "1.95", "UNDER_2.5": "1.90"},
            MARKET_BTTS: {"BTTS_YES": "1.90", "BTTS_NO": "1.95"},
        },
    ),
    (
        "md-04",
        "Süper Lig",
        "Galatasaray",
        "Fenerbahçe",
        {
            MARKET_1X2: {"HOME": "2.35", "DRAW": "3.30", "AWAY": "3.05"},
            MARKET_OU_25: {"OVER_2.5": "1.80", "UNDER_2.5": "2.08"},
            MARKET_BTTS: {"BTTS_YES": "1.72", "BTTS_NO": "2.20"},
        },
    ),
    (
        "md-05",
        "Bundesliga",
        "Bayern Munich",
        "Borussia Dortmund",
        {
            MARKET_1X2: {"HOME": "1.55", "DRAW": "4.60", "AWAY": "5.40"},
            MARKET_OU_25: {"OVER_2.5": "1.45", "UNDER_2.5": "2.85"},
            MARKET_BTTS: {"BTTS_YES": "1.60", "BTTS_NO": "2.40"},
        },
    ),
)


def _build() -> dict[str, Fixture]:
    catalog: dict[str, Fixture] = {}
    for match_id, league, home, away, markets in _RAW:
        normalized = {
            market: normalize_market(market, {k: dec(v) for k, v in outcomes.items()})
            for market, outcomes in markets.items()
        }
        catalog[match_id] = Fixture(match_id, league, home, away, normalized)
    return catalog


CATALOG: dict[str, Fixture] = _build()


def get(match_id: str) -> Fixture | None:
    return CATALOG.get(match_id)


def kickoff(match_id: str, *, now: datetime) -> datetime:
    order = list(CATALOG).index(match_id) if match_id in CATALOG else 0
    return now + timedelta(days=order + 1, hours=19)


def all_fixtures() -> list[Fixture]:
    return list(CATALOG.values())


_DRIFT_BASIS_POINTS = 600  # ±%6


def closing_odds(match_id: str, selection: str, opening: Money) -> Money:
    """Sentetik kapanış çizgisi: açılış çizgisinin **deterministik piyasa hareketi**.

    Gerçek bir kapanış akışı yok; kapanış açılıştan türetilir. Aynı (maç, seçim) her zaman aynı
    hareketi verir ve hareket ±%6 aralığında **iki yöne de** olabilir (bkz. ADR-0005).

    Neden fair oran değil: fair oran her zaman bookmaker oranından uzundur, dolayısıyla
    `CLV = O/O_fair − 1` yapı gereği hep negatif çıkar ve hiçbir bilgi taşımaz.
    """
    digest = hashlib.sha256(f"{match_id}:{selection}".encode()).digest()
    span = 2 * _DRIFT_BASIS_POINTS + 1
    basis_points = int.from_bytes(digest[:4], "big") % span - _DRIFT_BASIS_POINTS
    factor = ONE + Decimal(basis_points) / Decimal(10000)
    return q(opening * factor, ODDS_Q)
