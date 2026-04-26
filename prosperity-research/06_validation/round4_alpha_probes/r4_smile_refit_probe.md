# r4_smile_refit_probe (Probe 5)

## Probe definition

- Based on: r4_baseline_v15. Pure constants change in the smile prior:
  - `SMILE_A2_BASE`: 7.21 -> 7.62
  - `SMILE_A2_DRIFT_PER_DAY`: 0.815 -> 1.62
- Pre-registered as R4-CHAIN-02 (day-3 convexity refit). All other v15 logic
  byte-for-byte identical, including the per-strike bias dict and the AC1
  fades. traderData "smile" shape preserved.

## Backtest result (3-day BT, datasets/round4)

| day | own_trades | pnl | Delta vs v15 |
|---|---|---|---|
| day-1 | 1273 | +64,511.50 | -3,113.5 |
| day-2 | 1290 | +106,569.50 | -1,008.5 |
| day-3 | 1210 | +49,004.50 | +1,433.0 |
| total | 3,773 | **+220,085.50** | **-2,690** |

## Per-product attribution (3-day Delta vs v15)

| product | baseline | probe | Delta |
|---|---:|---:|---:|
| HYDROGEL_PACK | 134,062 | 134,062 | 0 |
| VELVETFRUIT_EXTRACT | 20,419 | 20,419 | 0 |
| VEV_4500 | 17,506 | 17,506 | 0 |
| VEV_4000 | 18,684 | 18,684 | 0 |
| VEV_5100 | 12,078.5 | 11,603.5 | -475 |
| VEV_5200 | 2,850.5 | 4,878.5 | +2,028 |
| OTHER(+6) | 17,175 | 12,932.5 | -4,243 |
| total | 222,775 | 220,086 | -2,690 |

## Verdict

**REJECT.** The convexity refit shifts voucher PnL but is net-negative at
locked params. Day-3 alone gains +1,433 (matching the pre-reg story that
v15's smile is most stale at TTE=5d) but day-1 (TTE=7d) loses -3,114 and
day-2 (TTE=6d) loses -1,009.

The drift per day was nearly doubled (0.815 -> 1.62), so the smile is
substantially flatter at TTE=8d (drift=0) than v15 -- but R4 day-1 sits at
TTE=7d, so the new prior has already drifted +1.62 in `a2`, which over-
prices the wings of the smile relative to where R4 day-1 actually trades.

V_5200 picks up +2,028 (the wing that benefits from a flatter convexity),
but OTHER (= V_5300/5400/5500/4500/4000/etc. excl V_5100 minus tagged
buckets) drops -4,243 because the deeper OTM strikes get over-priced and
the smile-MM rebalances against itself. Net -2,690.

The pre-reg theory is directionally correct (day-3 wins) but the magnitude
of the convexity change overshoots day-1. **Do not ship in isolation.**
A weighted blend (e.g. blend the new and old `A2_BASE/DRIFT` per TTE
bucket) might recover day-3's lift without the day-1 cost, but that is
a TUNING exercise outside Phase 8b's scope.
