# r4_combined_v01_probe

## Probe definition

- Based on: r4_baseline_v15 + Probe 1 (mark lean) + Probe 2 (OTM K retune)
  + Probe 3 (xprod lean) + R4-CHAIN-01 (0.7 sticky-strike portfolio-delta
  hedge).
- Pre-reg params used:
  - All Probe 1, 2, 3 parameters as locked.
  - `HEDGE_DELTA_MULT = 0.70` (sticky-strike adjustment).
  - `HEDGE_THRESHOLD = 40` portfolio delta units.
  - `HEDGE_TARGET = 20` (bring |D| down to this).
  - Hedge instrument: VFE only. Never HYD.
- Hedge logic: each tick, compute
  `D = sum_K Delta_BS(S, K, T, sigma_K) * pos[K] * 0.70` across all 10
  vouchers. If `|D| > 40`, post a TAKE order on VFE to neutralise
  `|D| - 20`. Sigma_K from the live smile fit.

## Backtest result (3-day BT, datasets/round4)

| day | own_trades | pnl | Delta vs v15 |
|---|---|---|---|
| day-1 | 1400 | +39,039.50 | -28,585.5 |
| day-2 | 1327 | +84,159.00 | -23,419.5 |
| day-3 | 1403 | +38,637.50 | -8,933.5 |
| total | 4,130 | **+161,836.00** | **-60,939** |

## Per-product attribution (3-day Delta vs v15)

| product | Delta |
|---|---|
| HYDROGEL_PACK | +519 |
| VELVETFRUIT_EXTRACT | -61,531 |
| VEV_4500 | 0 |
| VEV_4000 | 0 |
| VEV_5100 | 0 |
| VEV_5200 | 0 |
| OTHER(+6) | +75 |
| total | -60,937 |

The HYD/OTHER deltas mirror Probe 1 + Probe 2/3 individually. The disaster
is VFE: -61,531 vs v15.

## Verdict

**REJECT (catastrophic VFE hedge cost).** The 0.7 portfolio-delta hedge,
implemented as TAKE-only on VFE, is the entire problem. Net trade count
jumps from 3,681 to 4,130 (+449) with the increment going to VFE, and
each forced VFE take crosses the spread (~2 shells / RT) without an
informational edge.

Diagnostic:
- The 4-product mark-lean / xprod / OTM K logic delivers ~+1,100 in
  isolation (Probe 1 +1,054 plus Probe 2 +33 plus Probe 3 +42, minus
  expected interactions).
- VFE goes from +20,418 (baseline) -> -41,113 (combined). That is
  roughly -6 shells x 10,000 hedges. The hedge fires every tick the
  inventory crosses the threshold, and for a 200-cap, 4-shell-spread VFE
  market, the cumulative cost dominates any information from the hedge.
- The hedge sign is correct (long-vega -> sell VFE) but the implementation
  is naive: pure TAKE crosses the spread; the v15 smile MM and accumulation
  blocks already provide implicit inventory management, so adding an
  explicit take-hedge double-pays the spread.
- Pre-reg ranged HEDGE_THRESHOLD only via the parameter list (40-unit
  threshold), but did not pre-register a falsifier. In hindsight the
  falsifier should have been "no more than 0.5 shells / hedge of slippage
  cost" — easy to compute from a sample BT.

Recommendation: do NOT ship the hedge as TAKE-only. Re-implement as a
fair-value bias on VFE (subtract delta * hedge_cost_per_unit from VFE
fair) so the existing MM absorbs the rebalancing without crossing.
The mark-lean component (Probe 1) is unaffected and still ships +1k on
its own.
