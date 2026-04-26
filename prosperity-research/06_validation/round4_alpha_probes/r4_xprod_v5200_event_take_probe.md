# r4_xprod_v5200_event_take_probe (Phase 6 follow-up)

## Probe definition

- Based on: r4_baseline_v15.
- New event-triggered TAKE module: when any V_5200 trade has qty ≥ 5,
  classify aggressor side via trade.price vs V_5200 best bid/ask, and take
  V_4000 in the same direction with qty=10. Daily cap=30.
- No auto-flatten; v15's accumulation block on V_4000 unwinds via EXIT_SLACK=6.

## Backtest result (3-day BT, datasets/round4)

| day | own_trades | pnl | Δ vs v15 |
|---|---|---|---|
| day-1 | 1283 | +67,512.00 | −113.0 |
| day-2 | 1241 | +106,990.50 | −587.5 |
| day-3 | 1190 | +46,458.50 | −1,112.5 |
| total | 3,714 | **+220,961.00** | **−1,814** |

Per-product:
| product | baseline | probe | Δ |
|---|---:|---:|---:|
| HYDROGEL_PACK | 134,062 | 134,062 | 0 |
| VELVETFRUIT_EXTRACT | 20,419 | 20,419 | 0 |
| VEV_4000 | 18,684 | 16,870 | **−1,814** |
| (other) | 51,610 | 51,610 | 0 |
| total | 222,775 | 220,961 | −1,814 |

## Verdict — REJECT

**Ship gate**: Δ ≥ +200 AND ≥ 10 events fire AND day-3 dominates.

**Actual**:
- Δ = −1,814 (FAIL, sign wrong)
- Trade count went up 33 (3,681 → 3,714) — events did fire
- Day-3 has the LARGEST loss (−1,113) — opposite of pre-reg expectation

## Root cause

V_4000 spread is **21 ticks** (median). Each event-take crosses the spread
to enter (~10 ticks half-spread cost) and v15's accumulation MM later
unwinds at `intr + EXIT_SLACK = 6` below entry (~16 ticks total slippage).
The Phase 3 spillover signal is +5 ticks of mid move — REAL but the
implementation pays 16 ticks of round-trip spread cost.

V_4000 is NOT the right target for a TAKE-style implementation of the
spillover. The +5 tick lift on V_4000 mid only beats spread cost if you
are PASSIVE (post a buy at the bid, wait for the lift to bring offer down
to your level), not aggressive.

## Lessons for next session

1. **Take V_5200 itself** instead of V_4000. V_5200 spread is 3 ticks,
   not 21 — the spillover IS on V_5200's own mid (the source-product
   shuffle null PASSED z=+12-19 directly on V_5200's continuation).
   The spec asked for V_4000 to leverage the empirical lift, but spread
   cost dominates.

2. **Passive event quote** — when the event fires, post a buy at the
   current V_4000 bid + 1 (improving the queue but staying inside spread).
   If the +5 mid-lift materializes, the bid-side gets lifted toward ask
   and our bid fills; if it doesn't, the order just sits.

3. **Wait-and-take** — after event fires, hold the take order for 5 ticks
   only and unwind at the new ask, not via accumulation. Cuts the
   round-trip cost from 16 to ~10.

The alpha is statistically real (Phase 6 nulls confirmed source-shuffle
PASS z=+12.3/+19.5). It cannot be shipped as TAKE-on-V_4000. Re-test as
take-on-V_5200 or passive quote in next session.
