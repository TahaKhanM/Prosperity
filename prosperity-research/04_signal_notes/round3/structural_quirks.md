# Round 3 structural quirks — "Ceci n'est pas une pipe"

This document collects every place where the Round 3 chain *looks* like a
textbook object but **does not behave like one** in data. Any model whose
assumptions clash with these facts is disqualified before sizing.

Source artefacts:
- `prosperity-research/03_eda/round3/voucher_panel.csv` (30 000 rows)
- `prosperity-research/03_eda/round3/notebooks/_cache/axes_results.json`
- `prosperity-research/04_signal_notes/round3/parity_violations.csv`
- `prosperity-research/03_eda/round3/notebooks/_cache/parity_corrected.json`

---

## 1. HYDROGEL_PACK is NOT tightly pinned at 10 000

The playbook claim was "oscillating tightly around 10 000, RAINFOREST_RESIN
analog". Data (axis A):

| day | mean | median | std | min | max | % within ±1 | % within ±5 |
|---|---|---|---|---|---|---|---|
| 0 | 9990.96 | 9991.0 | 25.33 | 9928 | 10071 | 4.2% | 15.7% |
| 1 | 9992.06 | 9999.0 | 37.61 | 9908.5 | 10079 | 3.5% | 12.6% |
| 2 | 9989.40 | 9993.0 | 31.62 | 9891 | 10051 | 3.4% | 13.1% |
| pooled | 9990.81 | 9994.0 | 31.93 | 9891 | 10079 | 3.7% | 13.8% |

Only **13.8 %** of ticks sit within ±5 of 10 000. Mid persistence ρ₁ = 0.997,
OU half-life ≈ 300 ticks, Hurst ≈ 0.47 (near random walk).

**Implication.** Treat HYDROGEL as a **slowly mean-reverting** series, not a
pin. A `fair = 10000` hardcode with a ±5 anchor-guard will be **out of band
~86 % of the time**, and the canonical "revert to market mid otherwise"
clause is active far more than expected. This is the single most important
correction to the playbook.

**Actionable change.** Use `fair_value ≈ 9991` (empirical mean) with a slow
EMA (half-life ≈ 200 ticks) bounded to [9980, 10010], rather than a hard
10 000 pin. See alpha card A1.

---

## 2. Deep-ITM vouchers have zero (or negative) time value

Axis E. For VEV_4000 and VEV_4500, the time value distribution is not an
option's decay curve — it is a noisy band around zero:

| strike | TTE | mean TV | median | std | % (TV ≤ 0) | % (TV ≤ 0.5) |
|---|---|---|---|---|---|---|
| 4000 | 6–8d | +0.012 | 0.0 | 0.83 | 90.0 % | 95.4 % |
| 4500 | 6–8d | +0.011 | 0.0 | 0.76 | 70.6 % | 95.4 % |
| 5000 | 6–8d | +4.92  | 4.5 | 1.93 | 0.08 % | 0.20 % |

For VEV_4000 and VEV_4500:
- Median time value is exactly **0** across all 30 000 ticks.
- Min time value goes to **−7** for VEV_4000 (voucher trades strictly below
  intrinsic on a mid basis).
- Implied volatility from the BS solver returns **0** on those strikes (the
  panel column `iv_4000` and `iv_4500` are 0 most of the time).

**Interpretation ("Ceci n'est pas une pipe").** VEV_4000 and VEV_4500 are
not really options in the econometric sense — they are synthetic delta-1
positions: `V_{K} ≈ max(S − K, 0) ≈ S − K` for K ≪ S. The market prices them
as if they carry no optionality.

**Consequences.**
1. **Do NOT run IV-residual scalping on K ∈ {4000, 4500}.** The IV is 0,
   vega is 0, and any residual signal is numerical noise. (This matches the
   playbook's exclude-strikes-low-vega guidance.)
2. **Additional delta-1 capacity.** At expiry, long 1 VEV_4000 pays
   `S_T − 4000` with probability ~1 (VE has been ≥ 5200 for all 30 000
   historical ticks). That is equivalent to 1 unit of VE + a cash payment.
   Net effect: VEV_4000 and VEV_4500 give you **up to 600 additional**
   VE-equivalent position capacity at the cost of K seashells / unit of
   up-front capital. Useful as hedges or as an overlay when the VE 200-limit
   binds.
3. **No riskless arb (tradeable).** The 11 801 mid-based "intrinsic floor"
   violations collapse once spreads are respected (see `parity_arbs_true_size.md`).

---

## 3. Vol-smile convexity drifts upward as TTE shrinks

Axis F, per-tick quadratic fit in log-moneyness `IV(m) = a0 + a1·m + a2·m²`:

| day | TTE | mean ATM IV | mean skew a1 | mean convexity a2 |
|---|---|---|---|---|
| 0 | 8d | 0.2420 | −0.011 | 7.21 |
| 1 | 7d | 0.2449 | −0.086 | 7.85 |
| 2 | 6d | 0.2475 | −0.161 | 8.84 |
| median | — | 0.244 | −0.077 | 7.70 |

Observations:
- ATM IV rises by ~0.005 per day as TTE falls (≈ 2 % of level).
- Skew becomes markedly more negative at shorter TTE (−0.011 → −0.161).
- Convexity rises ~22 % over 2 days.

**Implication.** A "frozen smile" fit is optimistic. The smile has a
deterministic **TTE-drift** that you can exploit: sell ATM/near-ATM IV as
TTE shrinks if the smile drift repeats in live. Conservatively: the smile
is stable enough **intra-day** (σ(ATM IV) ≈ 0.004–0.008 per day) to mark
rich/cheap vs the per-day mean.

---

## 4. Implied forward = spot; no basis to harvest

Axis O. Solving for the forward `F` that minimises IV dispersion across
K ∈ [5000, 5500] at three snapshots:

| day | ts | S | F* | basis (F*−S) | disp(F*) |
|---|---|---|---|---|---|
| 0 | 100 000 | 5237.5 | 5237.5 | 0.0 | 0.003 |
| 1 | 500 000 | 5243.5 | 5243.5 | 0.0 | 0.006 |
| 2 | 900 000 | 5286.5 | 5286.5 | 0.0 | 0.007 |

No futures-like basis. The grid-search minimum sits exactly at `F = S`.

---

## 5. Monotonicity, cap, and butterfly parity are clean

Axis H (corrected). Tradeable violations at edge ≥ 1 seashell:

| day | floor (S_bid) | cap | monotonicity | butterfly |
|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 0 |
| 1 | 0 | 0 | 0 | 0 |
| 2 | 2 | 0 | 0 | 0 |

The chain respects bounded-payoff arb identities **on the tradeable side**.
The earlier 11 801 "intrinsic floor" violations were all mid-based at
0.5 seashell edge. They disappear against S_bid.

---

## 6. Counterparty anonymisation

Axis D. `trades_round_3_day_{0,1,2}.csv` have 100 % **empty** buyer/seller
strings. No named "smart bot" is detectable in historical data.

**Implication.** The Counterparty Copy alpha (P3 Olivia-style) cannot be
pre-staked. It can still work **live** — `state.market_trades[symbol]` may
expose names in the hosted environment — but the historical priors are zero.
Card F1 sits in "research-more" until a name appears in live uplink.

---

## Summary — the pipe is not a pipe

| Assumption | Data verdict |
|---|---|
| HYDROGEL pinned at 10 000 | ✗ — centred at 9 991 with ±30 noise |
| Deep-ITM calls have time value | ✗ — TV ≈ 0 with negative tail |
| Frozen smile is identical across days | ✗ — TTE drift in skew and convexity |
| Forward ≠ spot | ✗ — basis is zero |
| Bounded-payoff arb on tradeable side | ✓ — chain is clean (1–2 events in 30 k ticks) |
| Named counterparty in historical | ✗ — all anonymous |

Every alpha card in `alpha_registry.md` has been reviewed against this list.
