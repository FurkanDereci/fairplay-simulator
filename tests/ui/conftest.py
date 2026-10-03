"""`tests/ui` için paylaşılan kurgular: gerçek HTTP sunucusu + gerçek tarayıcı.

Kurgular burada tutulur çünkü iki test modülü de aynı sunucuyu/tarayıcıyı ister; kopyalamak
depo kuralını çiğnerdi ("aynı sonucu iki yerde gördüysen biri silinir").

Tarayıcı yoksa testler **atlanır**, böylece varsayılan `pytest` koşusu hızlı kalır.
Kurulum: `pip install playwright && playwright install chromium`
"""

from __future__ import annotations

import itertools
import socket
import threading
import time

import pytest

pytest.importorskip("playwright", reason="playwright kurulu değil")

import uvicorn
from playwright.sync_api import Browser, Page, sync_playwright

from fairplay_simulator.app.config import Settings
from fairplay_simulator.app.main import create_app

SECRET = "ui-flow-test-secret-long-enough-for-hs256"
_counter = itertools.count(1)


@pytest.fixture(scope="session")
def live_server(tmp_path_factory: pytest.TempPathFactory) -> str:
    """Uygulamayı gerçek bir HTTP sunucusu olarak ayağa kaldırır (tarayıcı TestClient'i süremez)."""
    db_path = tmp_path_factory.mktemp("ui") / "ui.db"
    app = create_app(db_path=str(db_path), settings=Settings(jwt_secret=SECRET))
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = int(probe.getsockname()[1])
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.1)
    assert server.started, "test sunucusu ayağa kalkmadı"
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=10)


@pytest.fixture(scope="session")
def browser() -> Browser:
    with sync_playwright() as playwright:
        try:
            instance = playwright.chromium.launch()
        except Exception as exc:  # pragma: no cover - ortam bağımlı
            pytest.skip(f"chromium başlatılamadı: {exc}")
        yield instance
        instance.close()


@pytest.fixture
def register(live_server: str):
    """Her çağrıda **benzersiz** kullanıcı adı/e-postası ile kayıt olur.

    Sabit ad kullanmak, oturum boyu paylaşılan tek veritabanında 409 çakışması üretir.
    """

    def _register(page: Page, prefix: str = "ui") -> None:
        name = f"{prefix}{next(_counter)}"
        page.goto(live_server, wait_until="networkidle")
        page.fill("#username", name)
        page.fill("#password", "gizli123")
        page.fill("#email", f"{name}@example.com")
        page.click("#register")
        page.wait_for_selector("details.match", timeout=15000)

    return _register
