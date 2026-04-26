# r4_xprod_vev5200_probe

## Probe definition

- Based on: r4_baseline_v15 + per-strike `xprod_lean[K]` accumulator
  triggered by Mark 14 buyer or Mark 22 seller of VEV_5200.
- Pre-reg params used:
  - `XPROD_LEAN_DECAY = 0.95` (per-tick HL ~14 ticks; ~5-tick effective lift).
  - `XPROD_LEAN_CLAMP = 5.0` ticks per strike.
  - Triggers: buyer in {Mark 14} or seller in {Mark 22} on VEV_5200.
  - Per-strike weights on `qty * 0.10`:
    - K=4000 -> 1.0
    - K=4500 -> 0.7
    - K=5000 -> 0.3
    - K=5100 -> 0.2
- Apply: in `_smile_voucher_orders`, add `xprod_lean[k]` to `fair`. In the
  deep-ITM accumulation block (K in {4000, 4500}), add `xprod_lean[k]` to
  the `intr` reference.
- `xprod_lean` and `last_ts` persisted in `traderData`.

## Backtest result (3-day BT, datasets/round4)

| day | own_trades | pnl | Delta vs v15 |
|---|---|---|---|
| day-1 | 1281 | +67,625.00 | 0 |
| day-2 | 1238 | +107,578.50 | +0.5 |
| day-3 | 1162 | +47,612.50 | +41.5 |
| total | 3,681 | **+222,816.00** | **+42** |

## Per-product attribution (3-day Delta vs v15)

| product | Delta |
|---|---|
| HYDROGEL_PACK | 0 |
| VELVETFRUIT_EXTRACT | 0 |
| VEV_4500 | 0 |
| VEV_4000 | 0 |
| VEV_5100 | 0 |
| VEV_5200 | 0 |
| OTHER(+6) | +42 |
| total | +42 |

Trade count is identical to v15 baseline (3,681) — the lean is firing very
rarely or its fair-value bumps are sub-tick and never flip an order vs the
baseline.

## Verdict

**REJECT (signal too rare to matter).** The xprod lean only fires on
VEV_5200 prints by the (Mark 14 buyer) or (Mark 22 seller) dyad. That is
a small fraction of the ~10k ticks per day on VEV_5200, and the magnitude
of the fair-value bump (max 5 ticks per strike, decayed) usually doesn't
move past the integer-price quote rounding boundary.

Per-strike Δ broken down:
- K=4000: 0 (deep-ITM accumulation never re-triggered with the bumped intr).
- K=4500: 0 (same).
- K=5000/5100: included in OTHER(+6) on the report; the +42 is essentially
  noise on K=5300+ (the OTHER bucket also includes 5300/5400/5500/6000/6500).

Day-3 picks up +41.5 of the +42 — consistent with the "spillover lift dies
in 5 ticks" hypothesis: the lean fires, briefly lifts the fair, the bot
quotes a slightly tighter sell-side, and gets filled occasionally. But
the volume is too small to dominate.

Pre-reg said *"the empirical lift is 5-tick window."* That window is
narrow enough that the BT under integer-price rounding mostly absorbs the
signal.

Recommendation: do NOT ship as a standalone. The signal sign is correct
(positive lift on dyad prints) but capacity is too small to overcome
the fixed quote rounding. Could be useful in a higher-frequency variant
(e.g. take-only on VEV_5200 itself when the dyad fires) but that is
out of scope for this probe.
