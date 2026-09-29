"""Yerleşim regresyonu: yatay taşma ve metin kırpılması — "arayüz işi görmeden bitmez".

Neden var: 375px'de **96px yatay taşma** ve kırpılan metinler vardı; 80 yeşil test bunların
hiçbirini görmedi. Kusur ancak sayfa render edilip `scrollWidth` ölçülünce çıktı. Bu dosya o
sınıfı kapıya çevirir: taşma ve kırpılma artık sessizce geri gelemez.

Tarayıcı yoksa atlanır (bkz. `conftest.py`).
"""

from __future__ import annotations

from playwright.sync_api import Browser, Page

VIEWPORTS = ((375, "mobil"), (900, "tablet"), (1440, "masaustu"))

# Taşma = gövde içeriğinin pencereyi aşması. Kırpılma = içeriğin kabından taşması
# (`scrollWidth > clientWidth`). İkisi de görsel kusurun sayısal imzasıdır.
MEASURE = """() => {
  const clip = (sel) => [...document.querySelectorAll(sel)]
      .filter(el => el.scrollWidth > el.clientWidth + 1)
      .map(el => el.textContent.trim().slice(0, 40));
  const wrap = document.querySelector('.table-wrap');
  return {
    tasma: document.body.scrollWidth - document.documentElement.clientWidth,
    kirpilan: [...clip('th'), ...clip('.market-name'), ...clip('.market-meta'), ...clip('.tile')],
    tileKolon: getComputedStyle(document.querySelector('.tiles'))
        .gridTemplateColumns.split(' ').length,
    tabloKaydirilabilir: wrap ? wrap.scrollWidth > wrap.clientWidth + 1 : null,
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
