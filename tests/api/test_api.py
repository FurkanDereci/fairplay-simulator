"""S4 — API kabuğu: güven sınırı, enerji kapısı, idempotency, iflas cooldown'ı."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal as D
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fairplay_echo.app.clock import FixedClock
from fairplay_echo.app.config import Settings
from fairplay_echo.app.fixtures import CATALOG, closing_odds
from fairplay_echo.app.main import create_app
from fairplay_echo.core.odds import clv_pct
from fairplay_echo.engines.match import MARKET_1X2, simulate_match

EPOCH = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
SECRET = "test-secret-that-is-long-enough-for-hs256"
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def world(tmp_path: Path) -> tuple[TestClient, FixedClock]:
    clock = FixedClock(EPOCH)
    app = create_app(
        db_path=str(tmp_path / "api.db"),
        settings=Settings(jwt_secret=SECRET),
        clock=clock,
    )
    return TestClient(app), clock


def _auth(client: TestClient, username: str = "aytek") -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={"username": username, "email": f"{username}@example.com", "password": "gizli123"},
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _wager(
    client: TestClient,
    headers: dict[str, str],
    *,
    stake: str = "100",
    match_id: str = "md-01",
    selection: str = "HOME",
    probability: str | None = None,
    key: str | None = None,
) -> object:
    extra = {"Idempotency-Key": key} if key else {}
    body: dict[str, object] = {
        "match_id": match_id,
        "market_type": MARKET_1X2,
        "selection": selection,
        "stake": stake,
    }
    if probability is not None:
        body["probability"] = probability
    return client.post("/api/wager", headers={**headers, **extra}, json=body)


def test_register_login_and_token(world: tuple[TestClient, FixedClock]) -> None:
    client, _ = world
    headers = _auth(client)
    assert client.get("/api/portfolio", headers=headers).status_code == 200

    ok = client.post("/api/auth/login", json={"username": "aytek", "password": "gizli123"})
    assert ok.status_code == 200

    bad = client.post("/api/auth/login", json={"username": "aytek", "password": "yanlis"})
    assert bad.status_code == 401

    duplicate = client.post(
        "/api/auth/register",
        json={"username": "aytek", "email": "baska@example.com", "password": "gizli123"},
    )
    assert duplicate.status_code == 409


def test_portfolio_requires_token(world: tuple[TestClient, FixedClock]) -> None:
    client, _ = world
    assert client.get("/api/portfolio").status_code == 401
    bogus = {"Authorization": "Bearer sahte-token"}
    assert client.get("/api/portfolio", headers=bogus).status_code == 401


def test_fixtures_are_deterministic_catalogue(world: tuple[TestClient, FixedClock]) -> None:
    client, _ = world
    payload = client.get("/api/fixtures").json()
    ids = [fixture["match_id"] for fixture in payload["fixtures"]]
    assert ids == ["md-01", "md-02", "md-03", "md-04", "md-05"]
    first = payload["fixtures"][0]["markets"][MARKET_1X2]
    assert first["outcomes"]["HOME"] == "1.95"
    assert first["fair_odds"]["HOME"] == "2.03"


def test_unknown_fixture_and_market_are_rejected(world: tuple[TestClient, FixedClock]) -> None:
    client, _ = world
    headers = _auth(client)
    assert _wager(client, headers, match_id="yok").status_code == 400
    assert _wager(client, headers, selection="YOK").status_code == 400


def test_float_stake_is_rejected(world: tuple[TestClient, FixedClock]) -> None:
    """Para string olmalı; float gönderimi doğrulamada reddedilir."""
    client, _ = world
    headers = _auth(client)
    response = client.post(
        "/api/wager",
        headers=headers,
        json={"match_id": "md-01", "market_type": MARKET_1X2, "selection": "HOME", "stake": 100.5},
    )
    assert response.status_code == 400


def test_energy_depletes_after_ten_wagers(world: tuple[TestClient, FixedClock]) -> None:
    client, _ = world
    headers = _auth(client)
    for index in range(10):
        response = _wager(client, headers, stake="10", match_id=f"md-0{index % 5 + 1}")
        assert response.status_code == 201, response.text

    blocked = _wager(client, headers, stake="10")
    assert blocked.status_code == 429

    portfolio = client.get("/api/portfolio", headers=headers).json()
    assert portfolio["simulation_energy"] == 0
    assert portfolio["can_wager"] is False


def test_energy_recharges_with_time(world: tuple[TestClient, FixedClock]) -> None:
    client, clock = world
    headers = _auth(client)
    for _ in range(10):
        _wager(client, headers, stake="10")
    assert client.get("/api/portfolio", headers=headers).json()["simulation_energy"] == 0

    clock.advance(hours=2)
    assert client.get("/api/portfolio", headers=headers).json()["simulation_energy"] == 20


def test_client_cannot_declare_a_result(world: tuple[TestClient, FixedClock]) -> None:
    """Güven sınırı: sonucu istemci bildirmez — böyle bir uç yoktur."""
    client, _ = world
    headers = _auth(client)
    response = client.post(
        "/api/wager/settle", headers=headers, json={"wager_id": "x", "won": True}
    )
    assert response.status_code == 404


def test_simulation_settles_server_side(world: tuple[TestClient, FixedClock]) -> None:
    client, _ = world
    headers = _auth(client)
    placed = _wager(client, headers, stake="100", match_id="md-01", selection="HOME")
    assert placed.status_code == 201
    wager_id = placed.json()["wager_id"]

    outcome = client.post(
        "/api/matches/simulate", headers=headers, json={"match_id": "md-01", "seed": 5}
    )
    assert outcome.status_code == 200
    settled_ids = [w["wager_id"] for w in outcome.json()["settled_wagers"]]
    assert settled_ids == [wager_id]
    assert outcome.json()["settled_wagers"][0]["status"] in {"WON", "LOST"}

    portfolio = client.get("/api/portfolio", headers=headers).json()
    assert portfolio["pending_wagers"] == []
    assert len(portfolio["settled_wagers"]) == 1
    assert portfolio["risk"]["trade_stats"]["total_trades"] == 1


def test_refill_does_not_change_nav(world: tuple[TestClient, FixedClock]) -> None:
    """I1 — HTTP üzerinden: refill NAV'ı değiştirmez."""
    client, _ = world
    headers = _auth(client)
    before = client.get("/api/portfolio", headers=headers).json()
    refilled = client.post("/api/refill", headers=headers)
    assert refilled.status_code == 200
    after = client.get("/api/portfolio", headers=headers).json()

    assert before["fund"]["nav"] == after["fund"]["nav"] == "100.0000"
    assert D(after["fund"]["units"]) > D(before["fund"]["units"])


def test_idempotency_key_prevents_double_spend(world: tuple[TestClient, FixedClock]) -> None:
    client, _ = world
    headers = _auth(client)
    first = _wager(client, headers, stake="100", key="abc")
    second = _wager(client, headers, stake="100", key="abc")

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["wager_id"] == second.json()["wager_id"]

    portfolio = client.get("/api/portfolio", headers=headers).json()
    assert len(portfolio["pending_wagers"]) == 1
    assert portfolio["fund"]["cash"] == "900.00"
    assert portfolio["simulation_energy"] == 90


def test_bankruptcy_locks_the_account(world: tuple[TestClient, FixedClock]) -> None:
    """Tam kasayla kaybedince iflas: kilit (423) ve kayıt (tier 1)."""
    client, _ = world
    headers = _auth(client)

    odds = {"HOME": D("1.95"), "DRAW": D("3.50"), "AWAY": D("4.10")}
    preview = simulate_match("md-01", "Arsenal", "Chelsea", odds, seed=7)
    losing_selection = "AWAY" if preview.outcome_1x2 == "HOME" else "HOME"

    placed = _wager(client, headers, stake="1000", selection=losing_selection)
    assert placed.status_code == 201
    assert placed.json()["ruin_risk_warning"] is True

    client.post("/api/matches/simulate", headers=headers, json={"match_id": "md-01", "seed": 7})

    portfolio = client.get("/api/portfolio", headers=headers).json()
    assert portfolio["fund"]["bankrupt"] is True
    assert portfolio["cooldown"]["locked"] is True
    assert portfolio["cooldown"]["tier"] == 1

    assert _wager(client, headers, stake="10").status_code == 423
    assert client.post("/api/refill", headers=headers).status_code == 423


def test_insufficient_cash_is_rejected(world: tuple[TestClient, FixedClock]) -> None:
    client, _ = world
    headers = _auth(client)
    assert _wager(client, headers, stake="5000").status_code == 400


def test_healthz(world: tuple[TestClient, FixedClock]) -> None:
    client, _ = world
    assert client.get("/healthz").json()["status"] == "ok"


def test_estimate_uses_the_users_own_probability(world: tuple[TestClient, FixedClock]) -> None:
    """EV/Kelly kullanıcının tahmininden gelir (fair olasılık kullanılsa f* hep 0 olurdu)."""
    client, _ = world
    headers = _auth(client)

    optimistic = client.post(
        "/api/estimate",
        headers=headers,
        json={
            "match_id": "md-01",
            "market_type": MARKET_1X2,
            "selection": "HOME",
            "probability": "0.60",
        },
    )
    assert optimistic.status_code == 200, optimistic.text
    body = optimistic.json()
    assert body["verdict"] == "POZITIF"
    assert float(body["ev"]) == pytest.approx(0.17, abs=0.001)
    assert float(body["kelly_fraction"]) == pytest.approx(0.1789, abs=0.001)
    assert float(body["suggested_stake"]) > 0

    pessimistic = client.post(
        "/api/estimate",
        headers=headers,
        json={
            "match_id": "md-01",
            "market_type": MARKET_1X2,
            "selection": "HOME",
            "probability": "0.40",
        },
    )
    rejected = pessimistic.json()
    assert rejected["verdict"] == "NEGATIF"
    assert rejected["suggested_stake"] == "0.00"


def test_estimate_rejects_bad_probability(world: tuple[TestClient, FixedClock]) -> None:
    client, _ = world
    headers = _auth(client)
    base = {"match_id": "md-01", "market_type": MARKET_1X2, "selection": "HOME"}

    out_of_range = client.post(
        "/api/estimate", headers=headers, json={**base, "probability": "1.4"}
    )
    assert out_of_range.status_code == 400

    as_float = client.post("/api/estimate", headers=headers, json={**base, "probability": 0.6})
    assert as_float.status_code == 400

    unknown = client.post(
        "/api/estimate", headers=headers, json={**base, "probability": "0.6", "match_id": "yok"}
    )
    assert unknown.status_code == 400


def test_wager_carries_the_assessment_when_probability_given(
    world: tuple[TestClient, FixedClock],
) -> None:
    client, _ = world
    headers = _auth(client)

    with_probability = _wager(client, headers, probability="0.60")
    assert with_probability.status_code == 201, with_probability.text
    assessment = with_probability.json()["assessment"]
    assert assessment["verdict"] == "POZITIF"
    assert float(assessment["kelly_fraction"]) > 0

    without = _wager(client, headers)
    assert without.json()["assessment"] is None


def test_validation_error_is_readable_not_a_python_repr(
    world: tuple[TestClient, FixedClock],
) -> None:
    """Boş alanla deneme ham Python repr döndürmemeli — ekranda tam olarak öyle görünüyordu."""
    client, _ = world
    response = client.post(
        "/api/auth/register", json={"username": "", "email": "", "password": ""}
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail.startswith("Doğrulama hatası →")
    assert "username" in detail
    assert "{'type'" not in detail, "ham pydantic repr'i sızdı"


def test_nav_at_matches_aligns_with_benchmarks(world: tuple[TestClient, FixedClock]) -> None:
    """Grafikte ortak zaman ekseni: portföy serisi botlarla **aynı uzunlukta** olmalı."""
    client, _ = world
    headers = _auth(client)
    _wager(client, headers, stake="100", match_id="md-01")
    client.post("/api/matches/simulate", headers=headers, json={"match_id": "md-01", "seed": 5})

    portfolio = client.get("/api/portfolio", headers=headers).json()
    at_matches = portfolio["nav_at_matches"]
    benchmarks = portfolio["benchmarks"]["series"]
    assert len(at_matches) == len(benchmarks["RANDOM_WALK"])
    assert len(at_matches) == 2  # başlangıç + 1 maç
    assert at_matches[0] == "100.0000"
    assert float(at_matches[-1]) != 100.0


def test_monte_carlo_from_the_catalogue(world: tuple[TestClient, FixedClock]) -> None:
    client, _ = world
    headers = _auth(client)
    response = client.post(
        "/api/matches/monte_carlo",
        headers=headers,
        json={"match_id": "md-01", "iterations": 2000, "seed": 7},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["source"] == "CATALOG"
    assert body["match_title"].startswith("Arsenal")
    assert body["odds_1x2"]["HOME"] == "1.95"

    distribution = body["monte_carlo"]
    assert distribution["iterations"] == 2000
    total = (
        distribution["home_win_pct"] + distribution["draw_pct"] + distribution["away_win_pct"]
    )
    assert total == pytest.approx(100.0, abs=0.05)


def test_monte_carlo_accepts_hypothetical_odds_and_is_deterministic(
    world: tuple[TestClient, FixedClock],
) -> None:
    client, _ = world
    headers = _auth(client)
    payload = {
        "odds_1x2": {"HOME": "1.50", "DRAW": "4.00", "AWAY": "6.00"},
        "iterations": 2000,
        "seed": 11,
    }
    first = client.post("/api/matches/monte_carlo", headers=headers, json=payload)
    second = client.post("/api/matches/monte_carlo", headers=headers, json=payload)

    assert first.status_code == 200, first.text
    assert first.json() == second.json(), "aynı seed aynı dağılımı vermeli"
    assert first.json()["source"] == "CUSTOM"
    assert first.json()["lambda_home"] > first.json()["lambda_away"]


def test_monte_carlo_requires_exactly_one_odds_source(
    world: tuple[TestClient, FixedClock],
) -> None:
    client, _ = world
    headers = _auth(client)

    neither = client.post("/api/matches/monte_carlo", headers=headers, json={"iterations": 100})
    assert neither.status_code == 400

    both = client.post(
        "/api/matches/monte_carlo",
        headers=headers,
        json={"match_id": "md-01", "odds_1x2": {"HOME": "2.0", "DRAW": "3.0", "AWAY": "4.0"}},
    )
    assert both.status_code == 400

    unknown = client.post(
        "/api/matches/monte_carlo", headers=headers, json={"match_id": "yok"}
    )
    assert unknown.status_code == 400

    bad_iterations = client.post(
        "/api/matches/monte_carlo",
        headers=headers,
        json={"match_id": "md-01", "iterations": 0},
    )
    assert bad_iterations.status_code == 400


def test_monte_carlo_does_not_touch_the_ledger(world: tuple[TestClient, FixedClock]) -> None:
    """Analiz ucu: bahis açmaz, enerji harcamaz, deftere yazmaz."""
    client, _ = world
    headers = _auth(client)
    before = client.get("/api/portfolio", headers=headers).json()

    client.post(
        "/api/matches/monte_carlo",
        headers=headers,
        json={"match_id": "md-01", "iterations": 500, "seed": 3},
    )

    after = client.get("/api/portfolio", headers=headers).json()
    assert after["fund"] == before["fund"]
    assert after["simulation_energy"] == before["simulation_energy"]
    assert after["pending_wagers"] == []


def test_learning_report_refuses_to_read_a_trend_from_an_empty_log(
    world: tuple[TestClient, FixedClock],
) -> None:
    """Alan 9'un kapısı: öğrenme ölçütleri ucu, örneklem kuralını kendisi de uygular."""
    client, _ = world
    headers = _auth(client)

    payload = client.get("/api/learning-report", headers=headers).json()
    assert payload["bets"] == 0
    assert payload["reliable"] is False
    assert payload["min_sample"] == 6
    assert payload["clv"]["trend"] == "örneklem yetersiz"
    assert "Örneklem yetersiz (0/6)" in payload["headline"]


def test_learning_report_measures_behavior_not_advice(
    world: tuple[TestClient, FixedClock],
) -> None:
    """Ölçütler davranışı sayar; tavsiye/tahmin alanı **yoktur** (ADR-0006, docs/90)."""
    client, _ = world
    headers = _auth(client)
    for _ in range(6):
        _wager(client, headers, stake="50", match_id="md-01")

    payload = client.get("/api/learning-report", headers=headers).json()
    assert payload["bets"] == 6
    assert payload["reliable"] is True
    assert payload["market_breadth"] == 1
    assert payload["stake"]["verdict"] in {"ölçülü", "aşırı"}
    assert payload["stake"]["limit_pct"] == "15.00"
    assert payload["favourite"]["line"] == "2.00"
    # Kapanış oranı olmadığı için CLV serisi boş: genel örneklem yeter, CLV'in kendi kapısı var.
    assert payload["clv"]["trend"] == "örneklem yetersiz"
    assert set(payload) == {
        "bets",
        "min_sample",
        "reliable",
        "market_breadth",
        "clv",
        "stake",
        "favourite",
        "headline",
    }


def test_risk_reliability_flags_a_thin_sample(world: tuple[TestClient, FixedClock]) -> None:
    """Anlamlılık kapısı (docs/20 §2.8): az işlemli portföyde risk metrikleri etiketlenir."""
    client, _ = world
    headers = _auth(client)
    _wager(client, headers, stake="100", match_id="md-01")
    client.post("/api/matches/simulate", headers=headers, json={"match_id": "md-01", "seed": 5})

    risk = client.get("/api/portfolio", headers=headers).json()["risk"]
    reliability = risk["reliability"]

    assert reliability["sharpe_reliable"] is False, "tek işlemli portföy 'anlamlı' olamaz"
    assert reliability["sharpe_t_statistic"] < reliability["min_t_statistic"]
    assert "Örneklem yetersiz" in reliability["note"]
    assert isinstance(reliability["profit_factor_defined"], bool)
    assert reliability["periods"] >= 1


def test_root_serves_the_ui_without_mock_state(world: tuple[TestClient, FixedClock]) -> None:
    """Arayüz API'den beslenir; enerji görünür (görünmeyen kural yok sayılır dersi)."""
    client, _ = world
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    page = response.text
    assert 'id="energy-display"' in page
    assert "/api/portfolio" in page
    assert "/api/fixtures" in page
    assert "/api/wager" in page
    assert "mock" not in page.lower()
    assert "Math.random" not in page


def test_hidden_attribute_beats_layout_css(world: tuple[TestClient, FixedClock]) -> None:
    """Regresyon: `hidden`, `display` kuralı olan elementte EZİLİYORDU.

    Enerji çubuğu (`.row`) giriş yapılmadan görünüyordu, çünkü `hidden` özniteliği UA
    stilinden gelir ve `.row { display: flex }` onu geçersiz kılar.
    """
    page = world[0].get("/").text
    assert re.search(r"\[hidden\]\s*\{[^}]*display:\s*none", page), (
        "`[hidden] { display: none }` kuralı yok: gizli paneller yine görünür olur."
    )


def test_ui_market_row_appends_the_selection_control() -> None:
    """Regresyon: `select` oluşturulup DOM'a **eklenmemişti**.

    O hâlde her piyasa satırı sessizce ilk sonucu gösteriyor ve ilk sonuca bahis yapıyordu;
    seçim yapmak imkânsızdı ve ekran hiçbir şey belli etmiyordu.

    Not: elimizde DOM koşturacak bir tarayıcı yok, bu yüzden koruma **statik**: bir piyasa
    satırının `row.append(...)` çağrısı seçim kontrolünü içermek zorunda. Gerçek DOM testi
    (tarayıcı/headless harness) S7'nin kalan işi olarak `docs/ROADMAP.md`'de duruyor.
    """
    page = (ROOT / "src" / "fairplay_echo" / "web" / "index.html").read_text(encoding="utf-8")
    assert re.search(r"row\.append\([^)]*\bselect\b[^)]*\)", page), (
        "market satırı `select` öğesini DOM'a eklemiyor — seçim yapılamaz."
    )


def test_ui_opened_from_a_file_can_reach_the_api(world: tuple[TestClient, FixedClock]) -> None:
    """`file://` ile açılan sayfa mutlak API tabanı kullanır; hatayı görünür bantla bildirir."""
    page = world[0].get("/").text
    assert 'id="banner"' in page
    assert "location.protocol" in page
    assert "http://127.0.0.1:8000" in page


def test_clv_is_not_always_negative() -> None:
    """Regresyon: fair oranı kapanış vekili yapmak CLV'yi yapı gereği hep negatife kilitliyordu.

    ADR-0005: kapanış, açılışın deterministik piyasa hareketidir (±%6) ve iki yöne de açıktır.
    """
    signs = set()
    for fixture in CATALOG.values():
        for selection, opening in fixture.markets[MARKET_1X2].outcomes.items():
            closing = closing_odds(fixture.match_id, selection, opening)
            assert closing > 0
            signs.add(clv_pct(opening, closing) >= 0)
    assert signs == {True, False}, "CLV tek işarete kilitli: metrik bilgi taşımıyor."


def test_closing_odds_are_deterministic_and_match_specific() -> None:
    opening = D("1.95")
    assert closing_odds("md-01", "HOME", opening) == closing_odds("md-01", "HOME", opening)
    assert closing_odds("md-01", "HOME", opening) != closing_odds("md-02", "HOME", opening)
    assert closing_odds("md-01", "HOME", opening) != closing_odds("md-01", "AWAY", opening)
