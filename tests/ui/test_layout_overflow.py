"""Yerleşim regresyonu: taşma, kırpılma ve **üst üste binme** — "arayüz işi görmeden bitmez".

Neden var: 375px'de **96px yatay taşma** ve kırpılan metinler vardı; 80 yeşil test bunların
hiçbirini görmedi. Kusur ancak sayfa render edilip `scrollWidth` ölçülünce çıktı. Bu dosya o
sınıfı kapıya çevirir: taşma ve kırpılma artık sessizce geri gelemez.

**2026-10-03 eki — taşma ölçümü yetmiyor.** 7 kolonlu `.market` ızgarası ~1181–1330px arasında
kendi kolonuna sığmayıp **komşu kolonun üzerine** biniyordu: `body.scrollWidth` değişmediği için
"taşma yok" sanılıyordu, ama "Bahis" düğmesi portföy kutularının **altında** kalıyor, yani
**tıklanamıyordu**. İkinci ölçüm bu yüzden eklendi: düğmenin merkezinde `elementFromPoint` ile
**kendisi** bulunmalı.

Tarayıcı yoksa atlanır (bkz. `conftest.py`).
"""

from __future__ import annotations

from playwright.sync_api import Browser, Page

#: 1200: ızgara taşmasının görüldüğü bant (1181–1330) — taşma ölçümünün kör noktası.
VIEWPORTS = ((375, "mobil"), (900, "tablet"), (1200, "dizustu-esik"), (1440, "masaustu"))

# Taşma = gövde içeriğinin pencereyi aşması. Kırpılma = içeriğin kabından taşması
# (`scrollWidth > clientWidth`). Üst üste binme = düğmenin merkezinde başka bir öğe olması.
MEASURE = """() => {
  const clip = (sel) => [...document.querySelectorAll(sel)]
      .filter(el => el.scrollWidth > el.clientWidth + 1)
      .map(el => el.textContent.trim().slice(0, 40));
  const wrap = document.querySelector('.table-wrap');
  const fund = document.getElementById('fund-tiles');
  const btn = document.querySelector("[data-role='bet']");
  let engel = null;
  if (btn) {
    btn.scrollIntoView({block: 'center'});
    const r = btn.getBoundingClientRect();
    const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    if (!(hit === btn || btn.contains(hit))) {
      engel = hit ? String(hit.className || hit.tagName).slice(0, 40) : 'yok';
    }
  }
  return {
    tasma: document.body.scrollWidth - document.documentElement.clientWidth,
    kirpilan: [...clip('th'), ...clip('.market-name'), ...clip('.market-meta'),
               ...clip('.tile'), ...clip('.timeline li')],
    tileKolon: getComputedStyle(fund).gridTemplateColumns.split(' ').length,
    tabloKaydirilabilir: wrap ? wrap.scrollWidth > wrap.clientWidth + 1 : null,
    engel,
  };
}"""


def _open_workspace(browser: Browser, base: str, register, prefix: str) -> Page:
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    register(page, prefix)
    page.locator("details.match > summary").first.click()
    page.wait_for_selector(".market", timeout=5000)
    return page


def test_no_overflow_or_clipping_at_any_viewport(
    browser: Browser, live_server: str, register
) -> None:
    """375 / 900 / 1440: yatay taşma yok, kırpılan metin yok."""
    page = _open_workspace(browser, live_server, register, "layout")
    try:
        for width, label in VIEWPORTS:
            page.set_viewport_size({"width": width, "height": 800})
            page.wait_for_timeout(350)
            data = page.evaluate(MEASURE)
            assert data["tasma"] <= 1, f"{label} ({width}px): {data['tasma']}px yatay taşma"
            assert data["kirpilan"] == [], f"{label} ({width}px) kırpılan metin: {data['kirpilan']}"
            assert data["engel"] is None, f"{label} ({width}px) düğme örtülü: {data['engel']}"
    finally:
        page.close()


def test_no_overflow_with_the_simulation_arena_visible(
    browser: Browser, live_server: str, register
) -> None:
    """Arena açıldıktan sonra da taşma/kırpılma olmamalı — yeni yüzey kapı dışında kalmasın."""
    page = _open_workspace(browser, live_server, register, "arena")
    try:
        page.locator("button:has-text('Simüle et')").first.click()
        page.wait_for_selector("#sim-panel", state="visible", timeout=15000)
        for width, label in VIEWPORTS:
            page.set_viewport_size({"width": width, "height": 800})
            page.wait_for_timeout(300)
            data = page.evaluate(MEASURE)
            assert data["tasma"] <= 1, f"arena açıkken {label}: {data['tasma']}px yatay taşma"
            assert data["kirpilan"] == [], f"arena açıkken {label} kırpılan: {data['kirpilan']}"
            assert data["engel"] is None, f"arena açıkken {label}: düğme örtülü ({data['engel']})"
    finally:
        page.close()


def test_mobile_stacks_tiles_and_lets_the_table_scroll(
    browser: Browser, live_server: str, register
) -> None:
    """Mobil: metrik kutuları 2 kolona iner; 7 kolonlu tablo sıkışmak yerine kaydırılır."""
    page = _open_workspace(browser, live_server, register, "stack")
    try:
        page.set_viewport_size({"width": 375, "height": 800})
        page.wait_for_timeout(350)
        data = page.evaluate(MEASURE)
        assert data["tileKolon"] == 2, f"mobilde kutu kolonu {data['tileKolon']} (beklenen 2)"
        assert data["tabloKaydirilabilir"] is True, "mobilde tablo kaydırılamıyor (sıkışmış)"
    finally:
        page.close()
