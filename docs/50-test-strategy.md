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
| G-17 | Risk of Ruin (formül + kenar yoksa %100) |
| G-18 | Disiplin rozetleri · cooldown indirimi |
| G-19 | Oran temizliği: bozuk/negatif vig reddi |
| G-20 | Solvent gün ve tier indirimi (iflasta geçen günler yanar) |

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

`tests/golden` · `tests/property` · `tests/repo` · `tests/engines` · `tests/api` · `tests/ui` · `tests/data` · `tests/test_docs_sync.py`

`tests/data` **donmuş kayıtlar**dır (ör. `ledger_v1.json`): eski biçimli verinin hâlâ aynı durumu
ürettiğini kanıtlar (ADR-0009). Elle değiştirilmez; yeni sürüm **yeni dosya** olarak eklenir.

`tests/ui` **gerçek tarayıcıda** (Playwright/Chromium) sürer: DOM iddiaları, tıklama akışı,
konsol/sayfa hatası kontrolü. Kurulum: `pip install playwright && playwright install chromium`.
Tarayıcı yoksa testler **atlanır** (varsayılan koşu hızlı kalır).

Her dilim kendi dosyasını buraya ekler; `tests/test_docs_sync.py` bu yolların **gerçekten
var olduğunu** doğrular.

## 8. Devralınan doğrulama paketleri (kabul ölçütü)

Orijinalin `docs/architecture/03_verification_layer_and_test_strategy.md` belgesi **dört değişmez
paketi** tanımlar; bunlar yeni depo için de **kabul ölçütüdür**. Kapsam durumu `docs/70` §7.2'de
satır satır yazılı (R3–R6). Özet:

| Paket | Gereksinim | bu depodaki durum |
| --- | --- | --- |
| Suite 1 | Kilit süresi dolunca bahis yeniden serbest | ✅ `test_cooldown_unlocks_after_expiry` (uç düzeyi, enjekte saat) |
| Suite 2 | `NAV × U = Cash + Exposure` | ✅ `test_i2_nav_times_units_equals_value` (property) + `test_nav_identity_holds_at_the_endpoint` |
| Suite 3 | Bozuk/negatif vig'li oran **reddedilmeli** | ✅ `test_g19_odds_sanitation_rejects_corrupt_feeds` + `test_monte_carlo_rejects_corrupt_or_negative_vig_odds` |
| Suite 4 | Aynı finalizasyon tekrar işlenirse tek ödeme | ✅ `test_repeated_simulation_returns_the_same_score_and_pays_once` + `I3` |

## 9. Sınır kararları (mutation denetimi yerine)

Araç denemesi (2026-09-30): `mutmut 3.8` bu ortamda **çalışmadı** — kopyalama adımı
`/run/udev/watch` symlink döngüsüne giriyor (`OSError: Too many levels of symbolic links`);
ayrıca maliyeti ~28 sn × mutant olurdu. Çita araca değil **kararın sınırına** bağlandı:
aşağıdaki her satır, karşılaştırma veya sabit değiştiğinde **kırmızıya düşen** testi adıyla
gösterir (ADR-0010). Testler: `tests/test_boundaries.py` (+ `[G-15]` golden).

| Sınır kararı | Onu öldüren test |
| --- | --- |
| `money.q` `ROUND_HALF_UP` (`0.125 → 0.13`) | `test_money_rounds_half_up_never_half_even` |
| `money.dec` `float` reddi | `test_money_refuses_float` |
| Oranı `≤ 0` olan sonuç atılır (`v > ZERO`) | `test_normalize_market_drops_non_positive_odds` |
| Overround tabanı 0 (`max(ZERO, total − 1)`) | `test_overround_never_goes_negative` |
| Tümü geçersiz pazar (`total > ZERO` guard) | `test_normalize_market_survives_an_all_invalid_market` |
| Kelly: kenar yoksa **tam 0** (orijinalde 0.05'e düşüyordu) | `test_kelly_returns_exactly_zero_when_there_is_no_edge` |
| Kelly: `O ≤ 1` guard | `test_kelly_guards_odds_at_or_below_one` |
| CLV: kapanış oranı 0 guard | `test_clv_guards_a_zero_closing_odds` |
| Enerji: tavanda geçen süre yanar | `test_g15_energy_cap_rules` |
| Enerji: bahis **tam** maliyette kabul | `test_wager_is_allowed_at_exactly_the_cost` |
| Enerji: harcama tabanı 0 | `test_spend_never_goes_below_zero` |
| Cooldown: `tier < 1` ücretsiz, `tier = 1` değil | `test_cooldown_tier_zero_is_free_and_tier_one_is_not` |
| Cooldown: kilit **tam** bitiş anında açılır | `test_unlock_happens_at_the_exact_expiry_instant` |
| Cooldown: 3. solvent günü tier'ı düşürür | `test_solvent_day_streak_drops_the_tier_at_exactly_three` |
| Sharpe t: `periods ≤ 0` guard | `test_sharpe_t_statistic_guards_a_zero_period_count` |
| Ruin: kasa eşiğinin altı/üstü (%15) | `test_ruin_gate_requires_confirmation_above_the_threshold` |
| Ruin: reddedilen istek yan etki bırakmaz | `test_ruin_gate_does_not_consume_energy_when_it_rejects` |
| Cooldown indirimi: 3 rozet tavanı 72'ye çeker | `test_i6_discipline_discount_caps_the_cooldown` |
| Oran: `Σ(1/O) ≤ 1` (negatif vig) ve `O ≤ 1` reddedilir | `test_g19_odds_sanitation_rejects_corrupt_feeds` |
| Finalizasyon: tekrar çağrı aynı skoru döndürür, ikinci ödeme yok | `test_repeated_simulation_returns_the_same_score_and_pays_once` |
| Solvent gün: imleç kurulmamışken gün uydurulmaz | `test_g20_first_tick_only_sets_the_cursor` |
| Solvent gün: iflasta geçen günler **yanar** (imleç yine ilerler) | `test_days_spent_bankrupt_do_not_count_as_solvent_days` |
| Göç: eski şemalı dosyaya kolon eklenir | `test_existing_db_gets_the_solvent_day_column` |
| Yerleşim: taşma **yetmez**, örtüşme de ölçülür (`elementFromPoint`) | `test_no_overflow_or_clipping_at_any_viewport` |

Tablodaki adlar **uydurulamaz**: `tests/test_docs_sync.py` her adın gerçekten var olduğunu doğrular.
