# R4 Final Implementation — Running Decision Log

Append-only ship/reject decisions per probe. Phase 1 onward.

| Probe ID | Description | 3-day total | Δ vs floor (+228,510.50) | Per-day Δ vs floor | Verdict | Notes |
|---|---|---:|---:|---|---|---|
| R4-1-CompV02 | (v08 minus M67) + V_5000 imb2 | +225,124.00 | **−3,386.50** | -1,426 / -981 / -980 | **REJECT** | v08 machinery retired; CP_MULT + larger weights are net-negative once M67 removed. Floor unchanged. |
| R4-2A-AdaptiveBiasEMA | per-strike EMA replaces static SMILE_PER_STRIKE_BIAS | +212,192.00 | **−16,318.50** | -2,219 / -20,814 / +6,714 | **REJECT** | Day-2 catastrophic at TTE 7→6 transition; static dict was PnL-tuned, not residual-tuned. G1 family permanently retired. |
| R4-2B-V5200SelfTake | event-take V_5200 on aggressive prints | +228,018.50 | **−492.0** | -75 / -39 / -378 | **REJECT** | Captures Mark 22 noise (Mark 14 prints qty<5). Day-3 worst (momentum-following on down day). |
| R4-2C-FVBiasDeadband | -D/8 deadband bias to VFE fair | +191,055.50 | **−37,455.0** | -21,479 / -14,463 / -1,513 | **REJECT** | Bias saturates at ±1 cap given v15's deep-ITM accumulation (D~280); VFE quoting suppressed -22%. FV-bias family retired. |
| R4-3-RaceToTouch | inside-touch HYD quoting vs Mark 14 | +227,959.50 | **−551.0** | +91 / -440 / -202 | **REJECT** | Falsifier triggered: HYD own_trades DROPPED. Pre-reg formula (`min`/`max`) only loosens, never tightens. Reformulation needed outside pre-reg. |
| R4-4A-MarkInvGate | per-Mark inventory threshold lean reducer | +227,419.00 | **−1,091.5** | -370 / -559 / -163 | **REJECT** | Threshold of 50 units is reached too quickly; reduces VFE Mark 49 copy lean. Marks are flow-consistent, not inventory-reverting. |
| R4-4B-TTESmileZeroBias | TTE-conditional a2 + zeroed bias dict | +228,182.50 | **−328.0** | -2,636 / -17,576 / +19,884 | **REJECT** | Day-3 huge gain (+19,884 on V_5200) but day-1/2 cancel it. Needs TTE-conditional bias too — outside pre-reg. |

## Composite floor

`r4_composite_v01_probe.py` — **+228,510.50 / 3-day BT**.
- Per-day: +68,985.50 / +110,025.50 / +49,499.50.
- Δ vs v15 baseline (+222,775): +5,735.5.
- Per-product Δ: HYD +519, VFE +2,560, V_5000 (in OTHER) +2,656.5.

Any probe must beat this on at least 2 of 3 days to enter the production
trader. Composite v01's structure (mark_lean v02_no_m67 + V_5000 imb2 skew)
is the structural template; new probes layer on top of it.
