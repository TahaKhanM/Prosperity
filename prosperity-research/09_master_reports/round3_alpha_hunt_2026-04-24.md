# Round 3 alpha hunt — synthesis memo

*2026-04-24 — Round 3 (Salvinar / GOAT). TTE 5 days at live start. PnL reset.*

## TL;DR

Three alphas pass every rejection gate and go into the first submission:
**A1** soft-anchor MM on HYDROGEL (at `fair = 9991`, not 10 000), **B1**
wall-mid MM on VELVETFRUIT_EXTRACT, and **C1** top-2-level imbalance skew
additive to both. A **G1** defensive parity guard rounds out the trader at
negligible cost. Two cards (D1 IV scalp, E1 deep-ITM overlay) look
promising but hit gate 4 (backtester fill model) or gate 1 (single-regime
data) and sit in `research-more`. The chain respects all bounded-payoff
arb identities on the **tradeable** side, so no static parity trade
contributes to v1.

Expected backtest PnL across days 0–2: ≥ 30 k.

## Phase 1 — baseline artefacts

Regenerated with `build_voucher_panel.py`, `parity_scan.py`,
`vol_surface_fit.py`, `counterparty_scan.py`. Shapes match:
- voucher_panel.csv: **30 000 rows** (10 000 per day × 3 days).
- Smile fit: ATM IV median 0.244, skew median −0.077, convexity median 7.70.
- Parity: 11 801 intrinsic-floor flags at 0.5-edge on mids; **0–2 per day**
  once evaluated on `best_ask(K)` vs `best_bid(S)` at edge ≥ 1 (see
  `parity_arbs_true_size.md`).
- Counterparty: 100 % anonymous across 4 049 historical trades.

## Phase 2 — axis-by-axis alpha hunt

| axis | finding | card produced |
|---|---|---|
| A HYDROGEL pin | centred at **9 991**, not 10 000. σ = 32, half-life 300. | A1 ship-now |
| B VE wall-mid | regression slope 0.77 (t = 39) across 3 days. | B1 ship-now |
| C OB imbalance | k=2, h=1: t = 35 HYDROGEL, t = 20 VE. k=3 sign flips. | C1 ship-now |
| D counterparty | 0 named parties. Anonymous buy-side slightly positive. | F1 research-more (live hook) |
| E deep-ITM TV | TV ≈ 0 for K=4000, 4500. 90 % of V_4000 ticks have TV ≤ 0. | E1 research-more + quirk |
| F smile stability | ATM IV drifts +0.005, skew −0.15, convexity +1.6 across 8→6d. | L1 research-more |
| G residual revert | Hurst < 0.03 every strike, half-life 0.4–2.7 ticks. σ tiny. | D1 research-more |
| H tradeable parity | 0–2 floor, 0 mono, 0 cap, 0 butterfly at edge ≥ 1. | G1 ship-now (tiny) |
| I intra-day buckets | 0 buckets with \|z\| > 3. No planted time-of-day signal. | I1 park |
| J lead-lag | Lag 0 wins every pair. No exploitable lead. | J1 park |
| K vol clustering | ρ₁(\|return\|) ≈ 0.087 HYDROGEL & VE. Mild. | H1 fold into A1/B1 later |
| L trade size | Uniform retail-shape. No bot-modal qty. | — |
| M spectral | HYDROGEL 3 330-tick rhythm (real). VE/vouchers peak at 5 000 = half-day drift. No short-cycle planted. | — |
| N EOD drift | VE drifts −2.5 / +19.6 / +39.3 in last 50 ticks (days 0/1/2). Session trend, not squeeze. | K1 park |
| O implied forward | F* = S exactly. Zero basis. | O1 park |

## Phase 3 — "Ceci n'est pas une pipe" findings

The structural quirks report (`structural_quirks.md`) catalogues four real
violations of textbook assumptions:

1. **HYDROGEL is not pinned at 10 000** (mean 9 991, only 13.8 % within
   ±5). *Action:* A1 uses 9 991 as anchor. Ignoring this costs ~40 %
   of HYDROGEL PnL.
2. **Deep-ITM vouchers have zero time value** (K=4000/4500). IV solver
   returns 0; median TV is 0. They are *synthetic delta-1* contracts,
   not options. *Action:* card E1 proposes using them as extra
   delta-1 capacity; card D1 explicitly excludes them from IV scalping.
3. **Smile has a deterministic TTE drift** (skew −0.01 → −0.16 from 8d
   to 6d). *Action:* do not use a frozen smile past the training day.
4. **All historical counterparty strings are empty.** *Action:* live hook
   in F1; no historical staking possible.

Bounded-payoff arb identities (cap, butterfly, monotonicity) are all
satisfied on the tradeable side — the chain is price-consistent.

## Phase 4 — rejection gate application

| card | gate 1 single-day | gate 2 concentration | gate 3 plateau | gate 4 mid-fill | gate 5 structural | verdict |
|---|---|---|---|---|---|---|
| A1 | ✓ | ✓ | ✓ | ✓ | ✓ | ship-now |
| B1 | ✓ | ✓ | ✓ | ✓ | ✓ | ship-now |
| C1 | ✓ | ✓ | ✓ | ✓ | ✓ | ship-now |
| G1 | N/A | N/A | N/A | ✓ | ✓ | ship-now |
| D1 | ✓ | **✗** | ✓ | **✗** | needs K filter | research-more |
| E1 | ✓ | ✓ | ✓ | **✗** | exploits | research-more |
| F1 | **✗** | n/a | n/a | n/a | ✓ | research-more |
| L1 | weak | — | — | ✓ | ✓ | research-more |
| I1/J1/K1/M1/N1/O1 | n/a | no signal | — | — | — | park |

## Phase 5 — deliverables manifest

All required artefacts written and > 0 bytes:

```
prosperity-research/04_signal_notes/round3/alpha_registry.md
prosperity-research/04_signal_notes/round3/counterparty_findings.md
prosperity-research/04_signal_notes/round3/smile_stability_report.md
prosperity-research/04_signal_notes/round3/seasonality_report.md
prosperity-research/04_signal_notes/round3/parity_arbs_true_size.md
prosperity-research/04_signal_notes/round3/structural_quirks.md
prosperity-research/04_signal_notes/round3/ship_now.md
prosperity-research/09_master_reports/round3_alpha_hunt_2026-04-24.md  ← this file
prosperity-research/03_eda/round3/notebooks/alpha_hunt.py              ← full axis scan
prosperity-research/03_eda/round3/notebooks/patch_parity_mono.py       ← corrected parity
prosperity-research/03_eda/round3/notebooks/_cache/axes_results.json   ← 42 kB of raw stats
prosperity-research/03_eda/round3/notebooks/_cache/parity_corrected.json
```

## What to do next (not executed per brief)

1. Build `round3_v1` trader combining A1 + B1 + C1 + G1 behind
   `traderData` feature flags. **Do not** put D1, E1, F1 into v1.
2. Backtest on each of day 0, 1, 2. Gate: ≥ 30 k cumulative PnL, no
   single day < 5 k, no 500-tick drawdown > 2 k.
3. After v1 lands live and the hosted stream is producing named trades,
   begin collecting horizon-PnL per counterparty in `traderData`. When
   a counterparty passes the 20-trade / 2-SE bar, flip F1 to on.
4. Independently, tighten the Rust backtester's voucher fill model and
   reopen D1 (IV residual scalp). Without tighter fills, the backtest
   over-reports D1 PnL by ~2×.
