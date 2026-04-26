# r4_mark_lean_v01_probe

## Probe definition

- Based on: r4_baseline_v15 + per-product Mark-conditional lean stack.
- Pre-reg params used:
  - `LEAN_DECAY = 0.985` (HL ~46 ticks).
  - `LEAN_CLAMP_PROD = 3.0` ticks.
  - HYD: Mark 14 +/-0.20, Mark 38 +/-0.20 (mirrored), Mark 22 buyer -0.20
    (R4-HYD-M01).
  - VFE: Mark 14 +/-0.10, Mark 38 +/-0.10 (mirrored), Mark 67 buyer +0.10
    (R4-VFE-M01), Mark 49 seller +0.10 (R4-VFE-M02), Mark 22 seller +0.05
    (R4-VFE-M03).
  - Per-trade contribution = sign * weight * qty * 0.05.
- Lean is added to the `fair` value in the HYD MM (after `H_IMB*himb_k1 +
  hyd_fade`) and the VFE MM (after `skew + vfe_fade`). All other v15 logic
  is byte-for-byte identical.
- `mark_lean` and `last_ts` persisted in `traderData`.

## Backtest result (3-day BT, datasets/round4)

| day | own_trades | pnl | Delta vs v15 |
|---|---|---|---|
| day-1 | 1269 | +67,936.50 | +311.5 |
| day-2 | 1219 | +107,658.50 | +80.5 |
| day-3 | 1160 | +48,233.50 | +662.5 |
| total | 3,648 | **+223,828.50** | **+1,053.5** |

## Per-product attribution (3-day Delta vs v15)

| product | Delta |
|---|---|
| HYDROGEL_PACK | +519 |
| VELVETFRUIT_EXTRACT | +536 |
| VEV_4500 | 0 |
| VEV_4000 | 0 |
| VEV_5100 | 0 |
| VEV_5200 | 0 |
| OTHER(+6) | +1 |
| total | +1,054 |

The lean only mutates HYD/VFE fair. Vouchers see no direct change beyond
positions cascading through smile MM, hence near-zero attribution there.

## Verdict

**RESEARCH (marginal).** PnL improves +1,054 / +0.47 % vs the v15 baseline.
The improvement is roughly evenly split between HYD (+519) and VFE (+536),
matching the asymmetric per-Mark capacity in the playbook.

Per-day diagnostic:
- Day-3 alone delivers +662 (most of the alpha). Day-1 +312, day-2 +80.
- The day-3 HYD edge (+628) and VFE flat-day suggest the lean activates
  in the regime where v15 was weakest.

The signal sign is correct but magnitude is small relative to the full
+222k baseline. Pre-reg said LEAN_PER_QTY_M67 = 0.10 conservatively halves
the empirical bias; the BT confirms there is a small live edge but not
the "headline alpha" size from the headline_findings.md table.

Trade-count drops 33 (3,681 -> 3,648), consistent with the lean tightening
some MM quotes such that the trader trades less but slightly better.

**Ship-ready when**: combined with other small-delta alphas (Probes 2/3),
provided the combined probe doesn't introduce confounds. Standalone +1k
is below the typical ship threshold but the sign-confirmation is valuable.
