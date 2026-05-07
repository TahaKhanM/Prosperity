# r4_tte_smile_zero_bias_probe — REJECT

## Probe definition

Replace `_smile_prior`'s `(a2_base + a2_drift × drift)` linear formula
with a TTE-bucket lookup:
`SMILE_A2_BY_TTE = {7: 7.62, 6: 8.53, 5: 14.11, 4: 16.58, 3: 19.82}`,
linearly interpolated between adjacent buckets. Simultaneously zero out
`SMILE_PER_STRIKE_BIAS` for all strikes.

Pre-registered (locked): both sets of values exactly as above.

## Backtest result (3-day BT, datasets/round4)

| set | day | own_trades | pnl | Δ vs composite v01 (+228,510.50) |
|---|---|---|---|---:|
| day-1 | 1 | 1224 | 66,350.00 | **-2,635.5** |
| day-2 | 2 | 1224 | 92,449.50 | **-17,576.0** |
| day-3 | 3 | 1186 | 69,383.00 | **+19,883.5** |
| total | | 3,634 | **228,182.50** | **−328.0** |

Per-product 3-day breakdown shows V_5200 spectacular swing:
- V_5200 day-3: +14,408 (vs floor's -4,746 = +19,154 lift)
- V_5200 day-1: -1,264 (vs floor's -1,654.5 = +391)
- V_5200 day-2: -4,614 (vs floor's +9,251 = -13,865 hit)

The TTE-conditional convexity perfectly captures the day-3 (TTE=5)
voucher dynamics where v15's a2 was severely under-fitted.

## Diagnosis

This is exactly the prediction made in the prior `r4_chain_02_tte_conditional`
follow-up REJECT note: "directional thesis correct; needs TTE-conditional
blend, not constants swap." The TTE-conditional blend works on day-3 but
breaks day-1/2 because:

- Day-2 (TTE=6) the new a2=8.53 is HIGHER than v15's interpolation
  (~8.0 at this TTE), causing the smile to over-curve. This shifts mid
  prices for OTM strikes higher → V_5100/V_5200 fairs over-quote → MM
  gets adversely-selected on the asymmetric flow.
- Day-1 (TTE=7) the new a2=7.62 is similar to v15 (drift bumps it up
  from base 7.21), so day-1 is closer to flat. But the zeroed static
  bias dict still hurts (the per-strike biases were calibrated for the
  v15 a2 path).

The combined change (TTE-conditional + zero bias) does NOT hold up
because the static biases were calibrated for v15's specific a2
trajectory; replacing one without the other breaks per-strike
alignment, exactly as the followup_summary predicted.

## Ship gate outcome

- 3-day Δ vs baseline ≥ +500: **FAIL (-328)**.
- Day-3 Δ ≥ +1,000: **PASS (+19,883.5)** — but the AND-gate fails.

## Verdict — REJECT

The day-3 lift is real and large; the cost on day-1/2 is also real and
large. They roughly cancel at 3-day total. To capture day-3 without the
day-1/2 cost would require:
- TTE-conditional bias dict (calibrate per TTE), AND
- TTE-conditional a2.

That is two tuning axes — outside this session's pre-registration.
Punted to next session.
