# Test Stratejisi — Risk → Test

Her satır bir **riski** alır ve onu kapatan **test türünü** gösterir. Bir risk kapandı sayılmaz
sürece `tests/` altında onu tutan yeşil bir test yoksa.

## 1. Değişmezler → property testleri (Hypothesis)

| # | Değişmez | Testin yapacağı |
| --- | --- | --- |
| I1 | Refill invariance | Rastgele geçmiş + rastgele `D` → refill öncesi/sonrası `NAV` eşit |
| I2 | Defter tutarlılığı | Rastgele geçerli entry dizisi → `replay` son durumu birebir üretir |
| I3 | Settlement idempotentliği | Aynı settlement iki kez → ikinci kez durum değişmez |
| I4 | Seri bileşikliği | İflas + refill dizisi → `TWR` ürün formülüne eşit, iflas kayıtta kalır |
| I5 | Enerji monotonluğu | Pozitif geçen süre enerjiyi azaltmaz; tavanı aşmaz; eşik altı reddeder |
| I6 | Cooldown | `T(n)` formülü ve tavan; 3 solvent gün tier'ı bir düşürür |

## 2. Sözleşme → golden testler

`docs/20-accounting-spec.md` içindeki **her `[G-x]`** bir golden testtir. Spec'teki sayı birebir
tutmazsa build kırılır. Bu, "formül değişti ama doküman kaldı" durumunu yapısal olarak engeller.

| Golden | Ne kanıtlar |
| --- | --- |
| G-1 | Refill invariance (sayısal) |
| G-2 | İflas kalıcılığı + seri bileşikliği (`−100%`) |
| G-3 | MDD |
| G-4 · G-5 | Sharpe · Sortino |
| G-6 | ProfitFactor · Expectancy |
| G-7 | RAS |
| G-8 | Vig · fair odds |
| G-9 · G-10 | Kelly negatif/pozitif EV |
| G-11 | CLV |
| G-12 · G-13 | Enerji · Cooldown |

## 3. Doküman ↔ kod senkronu (`tests/test_docs_sync.py`)

| İddia | Doğrulama |
| --- | --- |
| `40-api.md` uç listesi | `app.routes` ile birebir (S3+) |
| Metrik tanımları (`20` §2) | `core/metrics` fonksiyonları mevcut ve imzaları uyumlu |
| `50-test-strategy.md` test dosyaları | `tests/` altında gerçekten var |
| Her `[G-x]` | `tests/golden/` altında karşılık bulan bir test var |

## 4. Uçtan uca (duman)

Kayıt → enerji `100` → N bahis → enerji tükenir → `429` → maç simüle → settle →
NAV/benchmark grafiği güncel ve tutarlı.

## 5. Sınır / güvenlik testleri

| Risk | Test |
| --- | --- |
| İstemci sonucu bildiriyor | `settle` ucu sonucu **istemciden almaz**; sonuç kaynağı maç motoru |
| Bilinmeyen maç/market | `400` döner, sessiz varsayılana düşmez |
| Başkasının kuponu | `403` |
| Çift harcama / tekrar gönderim | idempotency: ikinci istek para hareketi yaratmaz |
| Yetkisiz erişim | token yok/expired → `401` |

## 6. Kapılar (CI)

```
ruff check .            # lint
mypy --strict core app  # tip
pytest -q               # unit + property + golden + contract + docs-sync
```

Hepsi yeşil değilse dilim kapanmaz (DoD).

## 7. Test yerleşimi

`tests/golden` · `tests/property` · `tests/repo` · `tests/engines` · `tests/api` · `tests/ui` · `tests/test_docs_sync.py`

`tests/ui` **gerçek tarayıcıda** (Playwright/Chromium) sürer: DOM iddiaları, tıklama akışı,
konsol/sayfa hatası kontrolü. Kurulum: `pip install playwright && playwright install chromium`.
Tarayıcı yoksa testler **atlanır** (varsayılan koşu hızlı kalır).

Her dilim kendi dosyasını buraya ekler; `tests/test_docs_sync.py` bu yolların **gerçekten
var olduğunu** doğrular.

## 8. Devralınan doğrulama paketleri (kabul ölçütü)

Orijinalin `docs/architecture/03_verification_layer_and_test_strategy.md` belgesi **dört değişmez
paketi** tanımlar; bunlar yeni depo için de **kabul ölçütüdür**. Kapsam durumu `docs/70` §7.2'de
satır satır yazılı (R3–R6). Özet:

| Paket | Gereksinim | echo'daki durum |
| --- | --- | --- |
| Suite 1 | Kilit süresi dolunca bahis yeniden serbest | Kilit test edildi, **açılma edilmedi** |
| Suite 2 | `NAV × U = Cash + Exposure` | Model gereği sağlanıyor, **kimlik testi yok** |
| Suite 3 | Bozuk/negatif vig'li oran **reddedilmeli** | **Kırpılıyor, reddedilmiyor** |
| Suite 4 | Aynı finalizasyon tekrar işlenirse tek ödeme | Çekirdekte testli, **uç düzeyinde değil** |
