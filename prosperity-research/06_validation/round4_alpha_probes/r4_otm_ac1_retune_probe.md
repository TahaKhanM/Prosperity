# r4_otm_ac1_retune_probe

## Probe definition

- Based on: r4_baseline_v15 + 3-constant edit only.
- Pre-reg params used (R4-V5300-B07 / V5400-B07 / V5500-B07):
  - `AC1_FADE_K_5300 = 0.21`  (was 0.12)
  - `AC1_FADE_K_5400 = 0.25`  (was 0.15)
  - `AC1_FADE_K_5500 = 0.24`  (was 0.15)
- Reason for retune: R4 measured |AC1| on these strikes is 0.214 / 0.249
  / 0.242 (Phase 1 sub-agent). v15's K was set from R3 fits, where the
  empirical AC1 was smaller. Optimal K under the linear fade model =
  |AC1| (the regression coefficient that maximally explains next-tick
  mid change).
- Equally defensible range: K within +/-15 % of measured |AC1|.

## Backtest result (3-day BT, datasets/round4)

| day | own_trades | pnl | Delta vs v15 |
|---|---|---|---|
| day-1 | 1283 | +67,324.00 | -301 |
| day-2 | 1256 | +107,765.50 | +187.5 |
| day-3 | 1168 | +47,718.50 | +147.5 |
| total | 3,707 | **+222,808.00** | **+33** |

## Per-product attribution (3-day Delta vs v15)

| product | Delta |
|---|---|
| HYDROGEL_PACK | 0 |
| VELVETFRUIT_EXTRACT | +1 |
| VEV_4500 | 0 |
| VEV_4000 | 0 |
| VEV_5100 | 0 |
| VEV_5200 | 0 |
| OTHER(+6) | +33 |
| total | +33 |

The retune K_5300/5400/5500 only touches the smile MM fair on those three
strikes, which roll up under `OTHER(+6)`. So the entire signal sits there.

## Verdict

**REJECT (marginal flat).** The retune produces a +33 net delta, well
inside the noise band of a 3-day BT. Per-strike sliver is +33 on OTHER(+6)
combining VEV_5300/5400/5500/6000/6500.

Why this is essentially a wash:
- Day-1 *loses* 301 shells, day-2 +187, day-3 +147. The day-1 loss says
  the "K = |AC1|" theory is not stable across regimes — it can over-fade
  when the underlying VFE moves are persistent (TTE = 7d on day 1).
- v15's smaller K = 0.5-0.6 * |AC1| (which was the v15 empirical optimum)
  appears to reflect the spread-cost adjustment Cusano-style: optimal K
  in the *linear* model would be |AC1|, but with discrete spreads and
  inventory cost the *trading* optimum is smaller.
- Pre-reg falsifier was "per-strike BT std(mid - fair) does NOT drop >= 3%".
  We can't measure that directly here without re-extracting the smile fair
  from artefacts; the PnL signal alone is too small to declare success.

This probe correctly demonstrates the discipline: the headline-statistic
match (K = |AC1|) does not mechanically transfer to PnL. The conservative
v15 K should remain. Trade-count goes UP (+26 trades) for ~0 PnL — the
larger fade flips a few extra quotes to fills without an edge.

Recommendation: do NOT ship. Re-investigate using a half-day mid-fair
residual sweep before re-tuning K.
