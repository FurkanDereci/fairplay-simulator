"""Arayüzü **gerçek tarayıcıda** süren uçtan uca test.

Neden var: `select` öğesinin DOM'a eklenmediği hata, API/statik sayfa testleriyle
yakalanamamıştı; çünkü hiçbiri tarayıcıda JavaScript çalıştırmıyordu. Bu dosya o boşluğu kapatır.

Sunucu ve tarayıcı kurguları `tests/ui/conftest.py`'de paylaşılır; tarayıcı yoksa testler atlanır.
"""

from __future__ import annotations

from playwright.sync_api import Browser


def test_login_screen_hides_the_workspace(browser: Browser, live_server: str) -> None:
    page = browser.new_page()
    page.goto(live_server, wait_until="networkidle")
    assert page.locator("#auth-form").is_visible()
    assert not page.locator("#energy-wrap").is_visible()
    assert page.locator("label[for='username']").count() == 1
    assert page.locator("input#username").input_value() == ""  # gömülü kimlik bilgisi yok
    page.close()


def test_empty_form_shows_a_readable_error_not_a_python_repr(
    browser: Browser, live_server: str
) -> None:
    page = browser.new_page()
    page.goto(live_server, wait_until="networkidle")
    page.click("#register")
    page.wait_for_selector("#auth-error:not([hidden])", timeout=5000)
    message = page.locator("#auth-error").inner_text()
    assert "karakter" in message
    assert "{'type'" not in message, "ham pydantic repr'i ekrana düştü"
    page.close()


def test_selection_control_exists_and_changes_the_odds(
    browser: Browser, live_server: str, register
) -> None:
    """Regresyon: `select` DOM'a eklenmediği için her piyasa ilk sonuca kilitliydi."""
    page = browser.new_page()
    register(page, "sec")
    page.locator("details.match > summary").first.click()
    page.wait_for_selector(".market select", timeout=5000)

    select = page.locator(".market select").first
    values = select.locator("option").evaluate_all("els => els.map(e => e.value)")
    assert len(values) >= 3

    odds_before = page.locator(".market .odds").first.inner_text()
    select.select_option(values[1])
    page.wait_for_timeout(200)
    assert select.input_value() == values[1]
    assert page.locator(".market .odds").first.inner_text() != odds_before
    page.close()


def test_probability_yields_an_assessment_without_betting(
    browser: Browser, live_server: str, register
) -> None:
    page = browser.new_page()
    register(page, "prob")
    page.locator("details.match > summary").first.click()
    page.wait_for_selector(".market input[aria-label*='tahminin']", timeout=5000)

    page.locator(".market input[aria-label*='tahminin']").first.fill("60")
    page.wait_for_selector(".assess:not([hidden])", timeout=10000)
    text = page.locator(".assess").first.inner_text()
    assert "EV" in text and "Kelly" in text and "önerilen stake" in text
    assert page.locator("#wagers-body").inner_text().find("BEKLİYOR") == -1
    page.close()


def test_full_flow_bet_simulate_and_console_is_clean(
    browser: Browser, live_server: str, register, show_view
) -> None:
    page = browser.new_page(viewport={"width": 1600, "height": 1000})
    console_errors: list[str] = []
    page_errors: list[str] = []
    page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: page_errors.append(str(e)))

    register(page, "flow")
    # Portföy "Genel Bakış" görünümünde; NAV orada okunur (menü artık yönlendiriyor).
    show_view(page, "genel")
    assert page.locator("#t-nav").inner_text().startswith("100,00")
    show_view(page, "kupon")
    assert page.locator("#energy-display").inner_text().startswith("100")

    page.locator("details.match > summary").first.click()
    page.wait_for_selector(".market", timeout=5000)
    page.locator("[data-role='bet']").first.click()
    page.wait_for_timeout(1200)

    assert "BEKLİYOR" in page.locator("#wagers-body").inner_text()
    assert page.locator("#energy-display").inner_text().startswith("90")

    page.locator("button:has-text('Simüle et')").first.click()
    page.wait_for_timeout(1800)
    table = page.locator("#wagers-body").inner_text()
    assert ("WON" in table) or ("LOST" in table)
    assert "TL" in table

    arena = page.locator("#sim-panel")
    assert arena.is_visible(), "simülasyon arenası görünmedi"
    score = page.locator("#sim-score").inner_text()
    assert score.replace(" ", "") .count("-") == 1
    assert page.locator("#sim-outcomes .tile").count() == 3
    goals = page.locator("#sim-events li").count()
    totals = [int(part) for part in score.split("-")]
    assert goals == sum(totals) or goals == 1  # golsüz maçta "Gol olmadı." tek satır

    assert page.locator("#chart-legend span").count() == 4
    assert not console_errors, f"konsol hatası: {console_errors}"
    assert not page_errors, f"sayfa hatası: {page_errors}"
    page.close()


def test_unreliable_risk_metrics_carry_no_colour(
    browser: Browser, live_server: str, register, show_view
) -> None:
    """Alan 3'ün arayüz ayağı: `t < 2` iken metrik etiketlenir **ve rengi susar**.

    Ölçüldü (2026-10-03, kullanıcı ekran görüntüsü): "yorumlanmamalı" notu varken MDD ve Alpha
    kırmızı kalıyordu. Renk bir yorumdur; anlamsız örneklemde yorum yasak (DESIGN.md).
    """
    page = browser.new_page()
    register(page, "riskrenk")
    page.locator("details.match > summary").first.click()
    page.wait_for_selector("[data-role='bet']", timeout=5000)
    page.locator("input[aria-label$='stake']").first.fill("10")
    page.locator("[data-role='bet']").first.click()
    page.wait_for_timeout(800)
    page.locator("button:has-text('Simüle et')").first.click()
    page.wait_for_timeout(1500)

    # Metrikler "Genel Bakış" görünümünde; renk kuralı orada okunur.
    show_view(page, "genel")
    assert "Örneklem yetersiz" in page.locator("#risk-note").inner_text()
    for tile in ("t-sharpe", "t-sortino", "t-mdd", "t-beta", "t-alpha", "t-ras"):
        klass = page.locator(f"#{tile}").get_attribute("class")
        assert klass in (None, "", "muted"), f"{tile} anlamsızken renk taşıyor: {klass!r}"
    page.close()


def test_solvent_day_indicator_is_visible(
    browser: Browser, live_server: str, register, show_view
) -> None:
    """F5 — solvent gün göstergesi arayüzde görünür; değer sunucudan gelir (spec §4.2)."""
    page = browser.new_page()
    register(page, "solvent")
    show_view(page, "genel")  # gösterge "Genel Bakış" görünümünde
    assert page.locator("#t-solvent").inner_text() == "0 / 3"
    assert page.locator("#streak-fill").count() == 1
    page.close()


def test_accepted_high_stake_wager_leaves_a_persistent_box(
    browser: Browser, live_server: str, register
) -> None:
    """F6 — onaylanan yüksek riskli bahis **kalıcı** kutuda kalır (toast değil), kapatılabilir."""
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    register(page, "ruinbox")
    page.locator("details.match > summary").first.click()
    page.wait_for_selector("[data-role='bet']", timeout=5000)
    page.locator("input[aria-label$='stake']").first.fill("500")  # %50 > %15 → onay kapısı
    page.locator("[data-role='bet']").first.click()
    page.wait_for_selector("#ruin-dialog[open]", timeout=5000)
    page.click("#ruin-confirm")
    page.wait_for_selector("#ruin-box:not([hidden])", timeout=8000)
    assert "kasadaki pay" in page.locator("#ruin-box-facts").inner_text()

    page.locator("button:has-text('Simüle et')").first.click()  # yenileme kutuyu silmemeli
    page.wait_for_timeout(1500)
    assert page.locator("#ruin-box").is_visible()

    page.click("#ruin-box-close")
    assert not page.locator("#ruin-box").is_visible()
    page.close()


def test_repeated_bets_do_not_flood_the_toast_stack(
    browser: Browser, live_server: str, register
) -> None:
    """Yığın sınırı: tekrar eden mesaj birleşir ve yığın 4'ü geçmez.

    Ölçüldü (2026-09-30): 6 bahis 6 toast üretiyordu; yığın öğrenme panelini ve grafiği
    kapatıyordu. Ekran görüntüsüyle görülmeden fark edilmemişti.
    """
    page = browser.new_page(viewport={"width": 1440, "height": 1100})
    register(page, "toast")

    page.locator("details.match > summary").first.click()
    bet = page.locator("[data-role='bet']").first
    bet.wait_for(state="visible", timeout=5000)
    # Küçük stake: bu test toast yığınını ölçer, ruin kapısını değil (R1 ayrı testte).
    page.locator("input[aria-label$='stake']").first.fill("10")
    for _ in range(6):
        bet.click()
        page.wait_for_timeout(250)

    toasts = page.locator("#toast div")
    assert toasts.count() <= 4, f"toast yığını sınırsız büyüdü: {toasts.count()}"
    texts = toasts.all_inner_texts()
    assert len(texts) == len(set(texts)), f"aynı mesaj tekrar etmiş: {texts}"
    page.close()


def test_energy_gate_closes_the_bet_buttons(
    browser: Browser, live_server: str, register
) -> None:
    """Enerji bitince 'Bahis' butonları kapalı kalmalı (istek sonrası geri açılmamalı)."""
    page = browser.new_page()
    register(page, "energy")
    for index in range(5):
        page.locator("details.match > summary").nth(index).click()
        page.wait_for_timeout(150)
    page.wait_for_selector("[data-role='bet']", timeout=5000)

    # Küçük stake: bu test enerji kapısını ölçer; büyük stake ruin kapısına takılırdı (R1).
    stakes = page.locator("input[aria-label$='stake']")
    for index in range(stakes.count()):
        stakes.nth(index).fill("10")

    for index in range(10):
        page.locator("[data-role='bet']").nth(index).click()
        page.wait_for_timeout(700)

    assert page.locator("#energy-display").inner_text().startswith("0")
    assert page.locator("#energy-wrap").get_attribute("class").find("is-blocked") >= 0
    enabled = page.locator("[data-role='bet']:not([disabled])").count()
    assert enabled == 0, f"enerji 0 iken {enabled} bahis butonu açık kaldı"
    page.close()


def test_high_stake_bet_requires_modal_confirmation(
    browser: Browser, live_server: str, register
) -> None:
    """R1 — kasa eşiğini aşan bahis modal ister; onaylanmadan hiçbir kupon oluşmaz."""
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    register(page, "ruin")
    page.locator("details.match > summary").first.click()
    page.wait_for_selector("[data-role='bet']", timeout=5000)

    page.locator("input[aria-label$='stake']").first.fill("500")  # 500 / 1000 = %50 > %15
    page.locator("[data-role='bet']").first.click()

    dialog = page.locator("#ruin-dialog")
    dialog.wait_for(state="visible", timeout=5000)
    assert "eşiğini" in page.locator("#ruin-body").inner_text()
    assert page.locator("#ruin-facts dt").count() >= 4
    assert page.locator("#wagers-body").inner_text().find("BEKLİYOR") == -1

    page.click("#ruin-confirm")
    page.wait_for_selector("#wagers-body:has-text('BEKLİYOR')", timeout=8000)
    assert not dialog.is_visible()
    page.close()
