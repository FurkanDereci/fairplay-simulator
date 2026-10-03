# FairPlay Simulator

A simulated, non-gambling football prediction/**portfolio** trainer. A bet is treated like a fund
position — unit NAV, vig removal, Kelly, Sharpe/Sortino/MDD, CLV and an escalating cooldown lock
after bankruptcy.

**Principles:** contract-first · single implementation (SSOT) · pure core · event-sourced ledger ·
`Decimal` for money / `float` for statistics · **server-authoritative settlement** · determinism ·
documents never lie.

> **Language note.** The README and commit messages are English; the rest of the repository
> (documents, code comments, UI) is Turkish on purpose — see `AGENTS.md` §11.

## Install

```bash
python3 -m venv .venv          # or: python3 -m virtualenv .venv
.venv/bin/pip install -e ".[dev]"
```

## Run

```bash
.venv/bin/fairplay-simulator serve --db fairplay.db --port 8000
# UI: http://127.0.0.1:8000  (sign up → 1.000 TL virtual balance)
```

The same binary also exposes the `replay`, `export-openapi`, `render-api-docs` and `version`
subcommands.

## How to test

**1. Automated suite** — golden · property · repo · engines · api · ui · docs-sync:

```bash
.venv/bin/pytest                # everything must pass
```

**2. Quality gates:**

```bash
.venv/bin/ruff check .          # lint
.venv/bin/mypy                  # types (strict)
```

**3. Manually, in a browser** — start it with `fairplay-simulator serve`; sign up, place a wager
(energy is visible in the header), settle the match with "Simüle et", watch the NAV and benchmark
curves. A stake above 15% of your cash triggers a **confirmation modal** (the risk gate); after six
or more wagers, **discipline badges** appear from the `learning-report` metrics.

> If you skipped `pip install -e ".[dev]"`, run
> `PYTHONPATH=src .venv/bin/python -m fairplay_simulator.cli <command>` instead.

### If the UI does not open

Open the page **through the server**: `http://127.0.0.1:8000`. Double-clicking the HTML file makes
the address `file://`, and requests cannot resolve as `file:///api/...`. If you still want to open it
as a file: the page connects to the API at `http://127.0.0.1:8000` (CORS allows the `null` origin),
so it works as long as the server is running on port 8000. When it cannot reach the API, a red banner
appears at the top of the page.

## Useful commands

```bash
# Replay one user's ledger and print the projected state (I2: replay reproduces state exactly)
.venv/bin/fairplay-simulator replay aytek --db fairplay.db

# Regenerate the API reference from OpenAPI (never written by hand)
.venv/bin/fairplay-simulator render-api-docs --output docs/40-api.md

# The OpenAPI schema
.venv/bin/fairplay-simulator export-openapi | head -40
```

## Where to look

| What | File |
| --- | --- |
| Why this exists, and what it is not | `docs/00-vision.md` |
| Entities, state machines, invariants (I1–I6) | `docs/10-domain-model.md` |
| **The contract** — formulas plus worked examples (`[G-x]`) | `docs/20-accounting-spec.md` |
| **UI contract** (tokens, nevers, component rules) | `DESIGN.md` |
| Current vs target architecture and migration triggers | `docs/30-architecture.md` |
| API (generated from OpenAPI) | `docs/40-api.md` |
| Risk → test matrix | `docs/50-test-strategy.md` |
| Build order and status | `docs/ROADMAP.md` |
| **Quality areas — decision and gate index** | `docs/80-kalite-alanlari.md` |
| Product value: how "it teaches" is measured | `docs/90-urun-degeri.md` |
| Parity with the original repo and takeover plan | `docs/70-parite-ve-devralma.md` |
| Architecture decisions (ADRs) | `docs/60-decisions/` |

## The one rule of this repo

**No document lies.** Every factual claim is either generated (`40-api.md` ← OpenAPI) or bound to a
test (`tests/test_docs_sync.py`: spec examples ↔ golden tests, documented endpoints ↔ OpenAPI schema,
documented test paths ↔ real files).
