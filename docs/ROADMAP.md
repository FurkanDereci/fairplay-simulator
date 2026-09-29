# Yol Haritası

Kural: **her dilim ayrı onaylanır** ve DoD'u tamamlanmadan kapanmaz.
DoD = testler yeşil + `ruff`/`mypy` temiz + dokümanlar güncel + `docs-sync` geçer.

| # | Dilim | İçerik | DoD | Durum |
| --- | --- | --- | --- | --- |
| **S0** | Tasarım seti | `docs/` + `AGENTS.md` + ADR-0001/0002 (bu depo) | Set okunabilir bir sözleşme; hiçbir iddia "hedef/gerçek" karışıklığı taşımaz | ✅ |
| **S1** | İskelet | `pyproject` (ruff/mypy/pytest), pre-commit, CI (GitHub Actions), ADR | Yerelde üç kapı yeşil; CI dosyası hazır (uzakta koşması ilk push'a bağlı) | ✅ |
| **S2** | **Çekirdek muhasebe** | `core/`: errors, money, ledger, nav, metrics, odds, settlement, energy, cooldown (+ property & golden) | Spec'teki **13 `[G-x]`** golden test + **6 değişmez** property testi geçer; HTTP yok | ✅ |
| **S3** | Kalıcılık + replay | `repo/` (SQLite), ledger'dan türeyen şema, `cli replay` | Replay NAV'ı bit-birebir üretir (I2 testi) | ✅ |
| **S4** | API kabuğu | auth, wager, portfolio, **sunucu-otoriteli** settlement, refill + OpenAPI + idempotency | Endpoint'te iş mantığı yok; `40-api.md` üretildi; güven sınırı testli | ✅ |
| **S5** | Maç motoru | tohumlu Poisson + Monte Carlo | Aynı seed → aynı sonuç (testli) | ✅ |
| **S6** | Benchmark botları | 3 strateji, maç kayıtlarından **türetilen** | Determinizm + restart'ta sıfırlanmama | ✅ |
| **S7** | Oyunlaştırma + arayüz | enerji/cooldown; enerji **görünür**; kart tabanlı arayüz, lig filtresi, kullanıcı olasılığıyla EV/Kelly | Mock state yok; enerji görünür; bağımsız inceleme bulguları kapatıldı — **ama** istemci OpenAPI'den üretilmiyor, rozetler yok ve **DOM/tarayıcı test koşumu yok** | ⚠️ kısmi |
| **S8** | Yayın | doküman geçişi, README kurulumu, uçtan uca duman | Temiz ortamda kurulum + `docs-sync` yeşil | ⏳ |

## Dilim → sözleşme bağı

- S2 → `20-accounting-spec.md` §1–§3 (muhasebe, metrikler, oran) + §5 (kenar durumlar)
- S4 → `10-domain-model.md` §4 (hata sözleşmesi) + `20` §4 dışı uçlar
- S6 → `20-accounting-spec.md` §3.1–3.3 (vig, Kelly, CLV) + ADR-0004 (kapanış oranı vekili)
- S7 → `20-accounting-spec.md` §4 (enerji/cooldown politika katmanı)

## Deferred (bilinçli olarak sonra)

- **DOM / tarayıcı test koşumu** — ✅ çözüldü: `tests/ui/test_ui_flow.py` (Playwright + Chromium)
  arayüzü **gerçek tarayıcıda** sürüyor; DOM iddiaları, tıklama akışı, konsol/sayfa hatası kontrolü.
  Kurulum root gerektirmez (`playwright install chromium`); tarayıcı yoksa testler atlanır.
- **Tipli istemci üretimi** (OpenAPI → TS) — elle yazılmış ince istemci var.
- **Rozetler ve solvent-gün tier indirimi** — çekirdek fonksiyon hazır ve testli; duvar saatiyle gün
  sınırı işleyen zamanlayıcıya bağlanmadı.
- **Grafikte ortak zaman ekseni** — ✅ çözüldü: portföy NAV'ı **maç sınırlarında** örneklenir
  (`portfolio.nav_at_matches`), böylece botlarla aynı uzunlukta ve aynı eksende çizilir.
- Sosyal kopya fon / lig (Faz 2) — ayrı ADR gerektirir.
- PostgreSQL / TimescaleDB / Redis — `30-architecture.md` tetikleyicileri.
- Rate limiting — kötüye kullanım gözlemlenene kadar.
