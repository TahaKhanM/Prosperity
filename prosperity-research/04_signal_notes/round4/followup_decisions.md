# R4 follow-up — running decisions log

Session start: 2026-04-26.

| Phase | Probe | BT Δ vs v15 | BT Δ vs Probe 1 | Verdict | Notes |
|---|---|---:|---:|---|---|
| 1 | r4_phase5_g1 | **−19,244** | n/a | **REJECT** | Replacing smile-fit + static-bias with per-strike rolling EMA loses cross-strike consistency. Day-3 +2,385 (validates the IV-staleness hypothesis directionally) but day-1 −1,451 / day-2 **−20,178** collapse. EMA at HL=60 lags TTE regime shifts (TTE 6→5 transition takes ~5,000 ticks to settle in EMA). Future: shorter HL or blend with smile fit. |
| 2 | r4_v5000_c02_standalone | **+2,657** | **+1,602** | **SHIP** | Entire lift on OTHER bucket (V_5000 only changes). Day-2 +1,542 dominates. Alpha works as designed; the "+2,657 inside Probe 7 stack" estimate from Phase 8b was accurate. |
| 3 | r4_chain_02_tte_conditional | **−1,000** | **−2,054** | **REJECT** | Lookup at measured fit values, but `SMILE_PER_STRIKE_BIAS` dict was calibrated to v15's specific (a2_base=7.21, drift=0.815). Changing a2 alone breaks the per-strike alignment. Day-3 V_5200 lost −241; OTHER bucket lost −590 mostly on day 2 transition. Future: zero out static bias and re-test, OR re-fit static biases per TTE bucket. |
| 4 | r4_chain_01_fvbias | **−35,892** | n/a | **REJECT** | Pre-reg divisor=4 was too aggressive given v15's natural long-voucher inventory (D ~200-300 every tick → bias hits the ±1 hard cap constantly). Trade count drops 21% but VFE PnL crashes −35,892. Same root cause as Phase 8a hedge blowup: any constant bias overwhelms the existing MM. Future: deadband (no bias when |D| < 100) + larger divisor (≥10). |
| 5 | r4_mark_lean_v02_no_m67 | **+3,079** | **+2,025** | **SHIP** | New ship floor. Entire +2,025 lift on VFE. Mark 67 was a NET NEGATIVE leg, not just noise. |
| 6 | r4_xprod_v5200_event_take | **−1,814** | n/a | **REJECT** | Spread cost on V_4000 (21 ticks) > +5 tick spillover. Each event-take pays ~10 ticks half-spread; v15's accumulation MM unwinds at intr+EXIT_SLACK=6 below entry. Alpha is real but not tradeable as TAKE-on-target. Future: take V_5200 ITSELF (1-tick spread) instead of V_4000. |
| 7 | composite_v01 (lean_v02 + V_5000 imb2) | **+5,735.5** | +4,681 vs Probe 1 / +2,656 vs Phase 5 | **SHIP** | PERFECT additive composition (sum-of-parts +5,736 ≈ actual +5,735, within 1 shell). HYD +519, VFE +2,560, V_5000 (in OTHER) +2,656. All 3 days positive. |
