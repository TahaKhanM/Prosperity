# Prosperity 4 Context Pack Overview (GOAT / Round 4)

## Purpose

This pack is a compact, high-signal context layer for coding agents working on
the IMC Prosperity 4 repository during the GOAT (Great Orbital Ascension
Trials) phase. Round 4 is currently live ("The More The Merrier"). The pack is
designed to be consumed by tools such as Codex and Claude Code without wasting
always-loaded context on details that are only relevant to some tasks.

Use this pack to keep three things separate:

1. **Official competition facts**: rules, interfaces, products, limits, manual
   challenge mechanics (Round 4).
2. **Soft strategic hints**: narrative prompt cards, uplink summaries, and
   the Round 4 hint cards from `Data/ROUND 4 Hints.txt`.
3. **Repo-local tooling reality**: backtesters, visualizer behavior, skills,
   agents, command surfaces, and caveats.

## GOAT phase context

At the start of Round 3 ("Gloves Off", on Salvinar):
- All prior PnL is reset to zero.
- Rounds now last 48 hours instead of 72.
- Three remaining rounds (3, 4, 5) decide the Trading Champion of the Galaxy.
- The final submission wins each round; earlier drafts are ignored.

We are now in **Round 4** ("The More The Merrier", same setting). PnL from
Round 3 carries forward; rounds 1–2 do not.

## Design principles

- Keep always-loaded entry files short.
- Put broad persistent rules in `AGENTS.md` / `CLAUDE.md`.
- Put task-specific detail in dedicated markdown files.
- Preserve every materially useful fact, including small caveats that can
  change agent behavior.
- Prefer references and reading order over pasting huge blobs into every
  prompt.

## File map

- `AGENTS.md` — thin Codex-facing entry file with durable repo rules.
- `CLAUDE.md` — thin Claude Code entry file using `@` imports.
- `00_PROSPERITY_CONTEXT_OVERVIEW.md` (this file) — trust model, cross-round
  facts, naming collisions, routing.
- `10_ALGO_TRADING_CONTEXT.md` — algorithmic challenge facts for Round 4
  (HYDROGEL_PACK, VELVETFRUIT_EXTRACT, 10 VEV vouchers + counterparty data).
- `20_MANUAL_TRADING_CONTEXT.md` — manual challenge facts (Round 4 Aether
  Crystal vanilla + exotic options).
- `30_REPO_AND_TOOLING_CONTEXT.md` — backtester + visualizer + skills context.
- `New Context/round_4_trading_round.md` — primary written source for Round 4.
- `New Context/round_4_aria_uplink.md` — Round 4 ARIA uplink transcript.
- `New Context/round_4_hint_cards.md` — verbatim Round 4 hint cards with
  research implications.
- `New Context/round_3_trading_round.md` — primary written source for Round 3
  (kept as reference; same algo products).
- `New Context/video_transcript.pdf` — ARIA uplink transcript for Round 3.
- `Unrefined Context/` — original uploaded source material (lower priority).

## Trust model and source hierarchy

When facts conflict, use this order:

1. **Official Prosperity written docs**
   - `New Context/round_4_trading_round.md` (primary for current round)
   - `New Context/round_3_trading_round.md` (reference; algo products same)
   - `Unrefined Context/official_prosperity_context.md` (general mechanics)
2. **Repo-context documents that describe local code/tooling**
   - `Unrefined Context/RUST_BACKTESTER_CONTEXT_FOR_AI_TOOLS.md`
   - `Unrefined Context/PYTHON_BACKTESTER_AND_VISUALIZER_CONTEXT_FOR_AI_TOOLS.md`
3. **Narrative / transcript material**
   - `New Context/round_4_aria_uplink.md`
   - `New Context/round_4_hint_cards.md`
   - `New Context/video_transcript.pdf` (R3)
   - `Unrefined Context/aria_uplink.md`

Practical rule:
- Treat official written docs as authoritative for rules, interfaces, position
  limits, products, submission behavior, and round mechanics.
- Treat uplinks and narrative transcripts as clue-bearing but lower-authority.
- Repo-context docs are authoritative only for local repo behaviour, not for
  competition rules.

## Round 4 products (live algorithmic, unchanged from R3)

| Product | Type | Position limit |
|---|---|---|
| `HYDROGEL_PACK` | Delta-1 (oscillates ~9990–10005) | 200 |
| `VELVETFRUIT_EXTRACT` (VE) | Delta-1 underlying | 200 |
| `VEV_4000` .. `VEV_6500` | 10 European call vouchers on VE | 300 each |

Voucher strikes: {4000, 4500, 5000, 5100, 5200, 5300, 5400, 5500, 6000, 6500}.
Expiry: shared, set in Round 1; **TTE = 4 days at start of live Round 4**.
Historical files `prices_round_4_day_{1,2,3}.csv` correspond to TTE = 7, 6, 5.
Settlement: cash at `max(S_T - K, 0)` at expiry; not exercisable before.

## Round 4 manual task (Aether Crystal options)

Independent of the algorithmic trader. Manual is a one-shot submission; last
submission before round timer counts.

- Underlying: **Aether Crystal** (manual-only; not in `order_depths`).
- Available contracts: vanilla calls, vanilla puts, plus three exotics:
  - **Chooser**: K=50, expiry 21 Solvenarian days. After 14 days the contract
    auto-converts to whichever of call/put is in the money; behaves vanilla
    afterward.
  - **Binary put**: K=40, expiry 21 days. Pays 10 if `S_T < 40`, else 0.
  - **Knockout (down-and-out) put**: K=45, barrier 35, expiry 21 days.
    Settles as a regular put with K=45 *iff* the underlying never touches the
    barrier; worthless if the barrier is breached even momentarily.
- Submission window: any time during Round 4; final submission wins.

## Round 4 counterparty disclosure (THE central new alpha)

Trade `buyer` / `seller` fields are now populated with `Mark <NN>` strings.
Distinct counterparties observed in 3-day historical data:
`Mark 01, Mark 14, Mark 22, Mark 38, Mark 49, Mark 55, Mark 67`. Initial
classification (see `prosperity-research/03_eda/round4/headline_findings.md`):

- **Mark 14** — smart bot, +5.71/unit horizon-500 PnL, 8,718 gross qty. Copy.
- **Mark 38** — bag-holder, −8.34/unit, 5,000 gross qty. Fade.
- **Mark 01** — high-volume buyer of OTM vouchers; Mark 22's natural
  counterparty. Treat as MM noise.
- **Mark 22** — high-volume seller of OTM vouchers; Mark 01's pair. Noise.
- **Mark 67** — buy-only on VE (1,510 buys, 0 sells). Lean long when seen.
- **Mark 49** — modest informed seller of VE. Fade their buys.
- **Mark 55** — high-volume both sides; net unfavourable. Treat as noise.

Temporal patterns are weak (no Mark concentrates >14 % of trades in any
hour-bucket). Do not gate on time of day.

## Cross-round competition facts

- Algorithmic and manual challenges are independent profit sources.
- `bid()` market-access auction only matters in Round 2 (historical).
- Outside Round 2, `bid()` is ignored and can safely be omitted.
- Final submission of the round is the one scored.
- Hosted container is AWS Lambda — stateless between ticks. Use `traderData`.
- `traderData` is truncated at 50,000 characters by the hosted framework.
- `OrderDepth.sell_orders` volumes are negative.

## Naming collisions

Official written docs use: `Salvinar`, `XIRECS`, `Aether Crystal`, `Mark <NN>`.
Narrative uplink/transcript variants: `Solvenar`, `Zyren`/`Zyrex`/`ZYREX`/`XYX`,
`Ether Crystal`. The variants refer to the same setting through lower-authority
sources. Prefer the written docs' naming.

## Round 3 hint: "Ceci n'est pas une pipe" (now historical)

The Round 3 `Data/ROUND_3/La_trahison_des_images.png` was Magritte's
"Treachery of Images". The R3 alpha hunt confirmed four real structural
quirks; see `prosperity-research/04_signal_notes/round3/structural_quirks.md`.
These quirks (HYDROGEL not actually pinned at 10000; deep-ITM vouchers have
zero time value; deterministic TTE drift in the smile; clean tradeable parity)
**continue to apply in Round 4** since the underlying products and dynamics
are unchanged.

## Routing rules for agents

If the task is about:
- algorithm design, signal mining, execution logic, or voucher pricing:
  read `10_ALGO_TRADING_CONTEXT.md`.
- manual challenge work (Aether Crystal options):
  read `20_MANUAL_TRADING_CONTEXT.md`.
- backtester, visualizer, command choices, skills, local agents, or
  repo workflow:
  read `30_REPO_AND_TOOLING_CONTEXT.md`.

## What not to do

- Do not mix tutorial products (`EMERALDS`, `TOMATOES`) or the archived Round
  1/2 products (`ASH_COATED_OSMIUM`, `INTARIAN_PEPPER_ROOT`) with live Round 4
  products.
- Do not treat narrative hints as stronger than official docs.
- Do not assume Black-Scholes applies without validating on the Round 4 data
  — use the `round4_options/parity_scan.py` and `vol_surface_fit.py` outputs.
- Do not rely on hosted-only mechanics (conversions, observations) in local
  backtests; the documented Rust/Python tools do not simulate them faithfully.
- Do not gate strategies on counterparty time-of-day — the Round 4 EDA shows
  temporal patterns are weak (peak hour-bucket share ≤14 %).
- Do not run the Round 3 Bio-Pods manual playbook — that auction has closed.
