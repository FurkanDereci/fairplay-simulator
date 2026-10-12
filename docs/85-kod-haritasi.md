# Kod Haritası (ürün haritası)

> **Üretilir, elle yazılmaz.** `graphify` grafiğindeki topluluklar **baskın modülüne**
> göre adlanır (ADR-0020). Grafik commit'e bağlı bir **anlık görüntüdür**; başlıktaki
> commit geçerlidir. Yeniden üretim: `graphify extract . --code-only --no-label` →
> `python3 scripts/kod-haritasi.py`.

**Kaynak commit:** `515fc6da4b87761440d7b2b62db80a0a8239a41f` · **Topluluk:** 50 · **Düğüm:** 900 · **Kenar:** 2021

| Topluluk | Ad (baskın modül) | Düğüm | Uyum | Kilit semboller |
| --- | --- | ---: | ---: | --- |
| C0 | `tests/api/test_api` | 85 | %87 | test_api.py, FixedClock, TestClient, _auth(), _wager() |
| C1 | `app/services + core/odds` | 79 | %39 | PortfolioService, money.py, .portfolio(), ._place_wager(), q() |
| C2 | `engines/match` | 49 | %51 | match.py, pytest, test_match_engine.py, simulate_match(), MatchResult |
| C3 | `app/api/routes` | 35 | %63 | routes.py, UserRecord, place_wager(), post, BaseModel |
| C4 | `cli` | 33 | %55 | cli.py, json, build_parser(), _cmd_scale_report(), Namespace |
| C5 | `core/metrics` | 33 | %76 | metrics.py, sharpe(), SettledWager, sortino(), max_drawdown_pct() |
| C6 | `tests/test_docs_sync` | 31 | %81 | test_docs_sync.py, _read(), re, test_documented_endpoints_cover_every_schema_path(), test_generated_api_docs_are_current() |
| C7 | `tests/test_boundaries` | 31 | %97 | test_boundaries.py, test_money_refuses_float(), test_clv_guards_a_zero_closing_odds(), test_cooldown_tier_zero_is_free_and_tier_one_is_not(), test_kelly_guards_odds_at_or_below_one() |
| C8 | `tests/ui/conftest + tests/ui/test_layout_overflow` | 30 | %37 | conftest.py, live_server(), _open_workspace(), test_layout_overflow.py, Browser |
| C9 | `tests/engines/test_bots + engines/bots` | 29 | %41 | bots.py, benchmark_series(), MatchRecord, test_bots.py, BotStrategy |
| C10 | `tests/property/test_invariants` | 28 | %86 | test_invariants.py, test_i3_settlement_is_idempotent(), _SETTINGS, given, test_i2_nav_times_units_equals_value() |
| C11 | `tests/golden/test_spec_examples` | 28 | %100 | test_spec_examples.py, test_g1_refill_invariance(), _replay(), test_g2_bankruptcy_and_series_compounding(), test_g10_kelly_positive_ev() |
| C12 | `repo/sqlite_repo` | 26 | %92 | Repository, _iso(), LedgerEntry, .entries(), .append_entries() |
| C13 | `core/errors` | 24 | %58 | main.py, core/errors.py, DomainError, core/__init__.py, UnsupportedLedgerVersion |
| C14 | `core/ledger` | 24 | %88 | LedgerEntry, Ledger, decode_ledger(), ._append(), .deposit() |
| C15 | `tests/repo/test_sqlite_repo` | 22 | %64 | test_sqlite_repo.py, Path, test_cli_scale_report_measures_triggers(), test_cli_replay_prints_projection(), _seeded_ledger() |
| C16 | `core/cooldown` | 22 | %86 | CooldownState, cooldown.py, .accrue_solvent_days(), .trigger(), .register_solvent_day() |
| C17 | `tests/ui/test_ui_flow` | 21 | %95 | test_ui_flow.py, Browser, test_accepted_high_stake_wager_leaves_a_persistent_box(), test_energy_gate_closes_the_bet_buttons(), test_high_stake_bet_requires_modal_confirmation() |
| C18 | `app/errors` | 19 | %84 | services.py, app/errors.py, AppError, RuinConfirmationRequired, Unauthorized |
| C19 | `repo/sqlite_repo` | 18 | %78 | sqlite_repo.py, datetime, .cooldown(), _parse_dt(), .energy() |
| C20 | `app/security + app/services` | 18 | %44 | security.py, .register(), decode_token(), ._token(), .login() |
| C21 | `core/nav` | 18 | %72 | Fund, InvalidAmount, InsufficientCash, ._apply_settled(), nav_series() |
| C22 | `app/deps + app/config` | 17 | %41 | deps.py, Settings, config.py, repo/__init__.py, Clock |
| C23 | `package.json` | 15 | %67 | package.json, gen-api-types.mjs, devDependencies, openapi-typescript, scripts |
| C24 | `app/main` | 15 | %67 | create_app(), FastAPI, _error_handler(), _humanize(), app/__init__.py |
| C25 | `core/learning` | 13 | %92 | learning.py, build_learning_report(), observations(), clv_trend(), _mean() |
| C26 | `repo/sqlite_repo` | 12 | %58 | .__init__(), .__init__(), ._migrate(), .backup_to(), .schema_version() |
| C27 | `core/ledger + core/nav` | 12 | %33 | nav.py, ledger.py, EntryType, collections_abc, dataclasses |
| C28 | `tests/repo/test_backup_and_durability` | 12 | %83 | test_backup_and_durability.py, sqlite3, _seed(), test_foreign_keys_are_actually_enforced(), test_backup_passes_integrity_check_and_carries_no_wal_sidecar() |
| C29 | `app/api/routes` | 11 | %82 | Decimal, WagerRequest, EstimateRequest, field_validator, ._positive() |
| C30 | `tests/repo/test_ledger_format` | 10 | %80 | test_ledger_format.py, pathlib, test_a_newer_database_is_refused(), test_unknown_schema_version_is_refused_not_misread(), _fixture_payload() |
| C31 | `core/energy` | 10 | %80 | energy.py, regen(), can_wager(), datetime, spend() |
| C32 | `core/settlement` | 10 | %70 | settlement.py, settle(), payout_for(), Outcome, Enum |
| C33 | `app/services` | 9 | %67 | earned_badges(), ._badges(), .learning_report(), ._bet_inputs(), BetInput |
| C34 | `app/clock` | 9 | %78 | clock.py, datetime, typing, SystemClock, .__init__() |
| C35 | `tests/golden/test_spec_examples` | 8 | %75 | BetInput, test_g16_headline_writes_percentages_in_turkish(), test_g16_learning_metrics(), test_g16_thin_sample_reads_no_trend(), Deptodan gelen, çekirdeğin ihtiyaç duyduğu bahis alanları (DB tipi sızmaz). |
| C36 | `tests/golden/test_spec_examples` | 6 | %67 | test_g18_badges_are_derived_from_measured_metrics(), test_g18_no_badges_from_a_thin_sample(), earns_discipline_discount(), Yeterli rozet toplandı mı → cooldown tavanı düşer mi (spec §4.2)., [G-18] Az örneklemden rozet verilmez (`[G-14]` sınıfının ikizi). |
| C37 | `core/nav + tests/repo/test_backup_and_durability` | 6 | %33 | .replay(), test_restore_drill_recovers_the_committed_ledger(), test_replay_from_db_matches_memory(), I2 — kalıcılık üzerinden replay, bellekteki projeksiyonla birebir aynı., Kayıtları baştan uygulayarak durumu üretir (I2). |
| C38 | `web/api-types.d.ts` | 6 | %100 | api-types.d.ts, $defs, components, operations, paths |
| C39 | `tests/property/test_invariants` | 4 | %50 | generated_funds(), DataObject, Geçerli bir komut dizisinden defter + artımlı projeksiyon üretir., composite |
| C40 | `engines/__init__` | 2 | %100 | Simülasyon motorları — tohumlu, saf; saat/ağ erişimi yok., engines/__init__.py |
| C41 | `tests/golden/test_spec_examples` | 2 | %100 | test_g15_energy_cap_rules(), [G-15] Tavanda geçen süre yanar; artık dakikalar saklanır. |
| C42 | `(modülsüz)` | 1 | %0 | get |
| C43 | `pyproject.toml` | 1 | %100 | fairplay-simulator |
| C44 | `(modülsüz)` | 1 | %0 | datetime |
| C45 | `(modülsüz)` | 1 | %0 | Money |
| C46 | `(modülsüz)` | 1 | %0 | Any |
| C47 | `(modülsüz)` | 1 | %0 | date |
| C48 | `(modülsüz)` | 1 | %0 | datetime |
| C49 | `(modülsüz)` | 1 | %0 | Money |
