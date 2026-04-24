# Prosperity 4 Context Pack Overview (GOAT / Round 3+)

## Purpose

This pack is a compact, high-signal context layer for coding agents working on
the IMC Prosperity 4 repository during the GOAT (Great Orbital Ascension
Trials) phase starting Round 3. It is designed to be consumed by tools such
as Codex and Claude Code without wasting always-loaded context on details
that are only relevant to some tasks.

Use this pack to keep three things separate:

1. **Official competition facts**: rules, interfaces, products, limits, manual
   challenge mechanics (Round 3 onwards).
2. **Soft strategic hints**: narrative prompt cards, uplink summaries, and
   the Round 3 Magritte image hint.
3. **Repo-local tooling reality**: backtesters, visualizer behavior, skills,
   agents, command surfaces, and caveats.

## GOAT phase context

At the start of Round 3 ("Gloves Off", on Salvinar):
- All prior PnL is reset to zero.
- Rounds now last 48 hours instead of 72.
- Three remaining rounds (3, 4, 5) decide the Trading Champion of the Galaxy.
- The final submission wins each round; earlier drafts are ignored.

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
- `10_ALGO_TRADING_CONTEXT.md` — algorithmic challenge facts for Round 3
  (HYDROGEL_PACK, VELVETFRUIT_EXTRACT, 10 VEV vouchers).
- `20_MANUAL_TRADING_CONTEXT.md` — manual challenge facts (Round 3 Bio-Pods).
- `30_REPO_AND_TOOLING_CONTEXT.md` — backtester + visualizer + skills context.
- `New Context/Round 3 Trading round.md` — primary written source for Round 3.
- `New Context/Video Transcript.pdf` — ARIA uplink transcript for Round 3.
- `Unrefined Context/` — original uploaded source material (lower priority).

## Trust model and source hierarchy

When facts conflict, use this order:

1. **Official Prosperity written docs**
   - `New Context/Round 3 Trading round.md` (primary for current round)
   - `Unrefined Context/Official Prosperity Context.md` (general mechanics)
2. **Repo-context documents that describe local code/tooling**
   - `Unrefined Context/RUST_BACKTESTER_CONTEXT_FOR_AI_TOOLS.md`
   - `Unrefined Context/PYTHON_BACKTESTER_AND_VISUALIZER_CONTEXT_FOR_AI_TOOLS.md`
3. **Narrative / transcript material**
   - `New Context/Video Transcript.pdf`
   - `Unrefined Context/ARIA Uplink.md`

Practical rule:
- Treat official written docs as authoritative for rules, interfaces, position
  limits, products, submission behavior, and round mechanics.
- Treat uplinks and narrative transcripts as clue-bearing but lower-authority.
- Repo-context docs are authoritative only for local repo behaviour, not for
  competition rules.

## Round 3 products (live algorithmic)

| Product | Type | Position limit |
|---|---|---|
| `HYDROGEL_PACK` | Delta-1 (anchored ~10000) | 200 |
| `VELVETFRUIT_EXTRACT` (VE) | Delta-1 underlying | 200 |
| `VEV_4000` .. `VEV_6500` | 10 European call vouchers on VE | 300 each |

Voucher strikes: {4000, 4500, 5000, 5100, 5200, 5300, 5400, 5500, 6000, 6500}.
Expiry: shared, 7 rounds from the start of Round 1 ⇒ **5 days at start of
live Round 3**. Historical data days 0/1/2 correspond to TTE = 8/7/6 days.
Settlement: cash at `max(S_T - K, 0)` at expiry; not exercisable before.

## Round 3 manual task

Bio-Pods / Celestial Gardeners:
- Submit two bids. Each gardener has a hidden reserve price.
- First bid wins the gardener if `b1 >= r` (pay `b1`).
- Else, second bid is compared to the **global average of second bids**
  `μ̄`. Wins with probability that collapses cubically below μ̄ (precedent:
  `p = ((V - μ̄) / (V - b2))^3` from P3 Round 3).
- Reserves are "flowering fives apart" — on multiples of 5.
- Resale value V = 920. Won bio-pods auto-sell.

## Cross-round competition facts

- Algorithmic and manual challenges are independent profit sources.
- `bid()` market-access auction only matters in Round 2 (historical).
- Outside Round 2, `bid()` is ignored and can safely be omitted.
- Final submission of the round is the one scored.
- Hosted container is AWS Lambda — stateless between ticks. Use `traderData`.
- `traderData` is truncated at 50,000 characters by the hosted framework.
- `OrderDepth.sell_orders` volumes are negative.

## Naming collisions

Official written docs use: `Intara`, `Intarian`, `XIREN`, `XIRECs`.
Narrative uplink/transcript variants: `Entara`, `Entarian`, `Zyren`, `Zyrex`,
"Salvinar", "Solvenar". The variants refer to the same setting through
lower-authority sources. Prefer the written docs' naming.

## Round 3 hint: "Ceci n'est pas une pipe"

The Round 3 `Data/ROUND_3/La_trahison_des_images.png` is Magritte's
"Treachery of Images". Interpretation guidance:
- Treat it as a structural warning, not a trading tip.
- The voucher chain may *look* like a standard option chain but may include
  structural quirks. Validate with `parity_scan.py` before shipping any
  option-pricing model. Historical days show deep-ITM vouchers priced
  extremely close to (sometimes below) intrinsic, which is unusual for a
  normal option market.

## Routing rules for agents

If the task is about:
- algorithm design, signal mining, execution logic, or voucher pricing:
  read `10_ALGO_TRADING_CONTEXT.md`.
- manual challenge work (Bio-Pods auction):
  read `20_MANUAL_TRADING_CONTEXT.md`.
- backtester, visualizer, command choices, skills, local agents, or
  repo workflow:
  read `30_REPO_AND_TOOLING_CONTEXT.md`.

## What not to do

- Do not mix tutorial products (`EMERALDS`, `TOMATOES`) or the archived Round
  1/2 products (`ASH_COATED_OSMIUM`, `INTARIAN_PEPPER_ROOT`) with live Round 3
  products.
- Do not treat narrative hints as stronger than official docs.
- Do not assume Black-Scholes applies without validating on the Round 3 data
  — use the `round3_options/parity_scan.py` and `vol_surface_fit.py` outputs.
- Do not rely on hosted-only mechanics (conversions, observations) in local
  backtests; the documented Rust/Python tools do not simulate them faithfully.
