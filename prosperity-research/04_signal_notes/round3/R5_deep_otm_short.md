# R5 — Deep-OTM voucher short (VEV_6000 / VEV_6500)

Data: `voucher_panel.csv` (30 000 ticks), three days of
`prices_round_3_day_*.csv` / `trades_round_3_day_*.csv`. Bootstrap memoised
to `03_eda/round3/notebooks/_cache/r5_*.json`.

**Verdict.** `PARK`. Historical bid = 0, ask = 1 for all 30 000 ticks on
both strikes; every historical trade prints at price 0. The 0.5 "mid" is a
quote-midpoint artefact, not a fillable price — the naive "sell 300 at 0.5"
trade does not exist in this data.

---

## 1. Probability of expiry ITM

Anchor S₀ = 5258, σ = 0.24/yr, T = 5/365. Lognormal:
log(S_T/S₀) ~ N(−½σ²T, σ²T). Empirical resamples tick log-returns
(n = 29 997, std ≈ 2.15e−4), sums 50 000-tick blocks, 100 000 bootstraps.

| K | Lognormal z | Lognormal Pr(S_T > K) | Empirical Pr(S_T > K) | E[(S_T−K)⁺] (empirical) | E[S_T \| S_T > K] |
|---|---:|---:|---:|---:|---:|
| 6000 | 4.71 | 1.2 × 10⁻⁶ | **6.79 × 10⁻³** | 0.616 | 6 090.7 |
| 6500 | 7.56 | 2.0 × 10⁻¹⁴ | **1.0 × 10⁻⁵** | 0.00040 | 6 540.4 |

Empirical tail is drastically fatter than lognormal: p(S_T > 6000) is
**~5 600×** higher, p(S_T > 6500) ~5 × 10⁸× higher. Empirical q99(S_T)
≈ 5 960, q99.9 ≈ 6 180. Bootstrap ignores serial correlation; any live
drift or regime shift widens the tail further.

## 2. Book depth and fill capacity

Per-day medians on the first level, filtered from the raw L3 CSV.

| day | product | med_bid | med_bid_vol | med_ask | med_ask_vol | med_spread | max_bid | max_ask |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | VEV_6000 | 0 | 22 | 1 | 22 | 1 | 0 | 1 |
| 0 | VEV_6500 | 0 | 15 | 1 | 15 | 1 | 0 | 1 |
| 1 | VEV_6000 | 0 | 22 | 1 | 22 | 1 | 0 | 1 |
| 1 | VEV_6500 | 0 | 15 | 1 | 15 | 1 | 0 | 1 |
| 2 | VEV_6000 | 0 | 22 | 1 | 22 | 1 | 0 | 1 |
| 2 | VEV_6500 | 0 | 16 | 1 | 16 | 1 | 0 | 1 |

bid_price_1 = 0 for **10 000 / 10 000 ticks every day both strikes**;
ask_price_1 = 1 identically. Degenerate book:

- "Hit the bid" = sell at 0, not 0.5.
- "Post at the ask" = post at 1 and queue behind a 15–22-lot MM wall that
  cycles ~225k (6000) / ~155k (6500) contracts per day.

Historical trade counts (from `trades_round_3_day_*.csv`):

| day | VEV_6000 (trades / qty) | VEV_6500 (trades / qty) |
|---|---|---|
| 0 | 91 / 320 | 91 / 320 |
| 1 | 98 / 345 | 98 / 345 |
| 2 | 95 / 337 | 95 / 337 |

All trades print at price **0.0** (100% of 284/285 executions per strike).
Average trade size ≈ 3.5; max 5. Realistic daily sell capacity if live
behaves like history is ~300–350 contracts *per strike per day — at a fill
price of 0*.

## 3. Naive-hold PnL (sell 300 each, hold to expiry)

Using empirical E[max(S_T−K,0)]:

| fill assumption | strike | premium / contract | E[payoff] | E[PnL] / contract | E[PnL] × 300 |
|---|---|---:|---:|---:|---:|
| 0.50 (optimistic — wall-mid) | VEV_6000 | 0.500 | 0.6159 | −0.116 | **−34.78** |
| 0.50 | VEV_6500 | 0.500 | 0.00040 | +0.4996 | **+149.88** |
| 0.25 (mid-of-spread) | VEV_6000 | 0.250 | 0.6159 | −0.366 | −109.78 |
| 0.25 | VEV_6500 | 0.250 | 0.00040 | +0.2496 | +74.88 |
| 0.00 (empirical trade price) | VEV_6000 | 0.000 | 0.6159 | −0.616 | −184.78 |
| 0.00 | VEV_6500 | 0.000 | 0.00040 | −0.00040 | −0.12 |

Aggregate across both strikes at 300 contracts each (600 total):
- `sell at 0.5`: **E[PnL] = +115.1 seashells.**
- `sell at 0.25`: E[PnL] = −34.9.
- `sell at 0.0`: E[PnL] = −184.9.

Even in the *optimistic* case the total expectation is ≈ +115 seashells of
profit against hundreds of thousands of seashells of tail loss capacity
(see §5). The VEV_6500 leg carries almost all of the positive expectation;
the VEV_6000 leg is **negative-EV at every realistic fill price** because
empirical 5-day fat tails drive E[(S_T−6000)⁺] ≈ 0.62 > 0.50 premium.

## 4. Capped version / stop-loss realism

Panel mid for both V_6000 and V_6500 is exactly 0.5 for every one of the
30 000 ticks. Raw best-ask never exceeds 1 on any day. A stop at mid ≥ 5
is therefore **never binding in history** — but that is cold comfort,
because a live S shock would make mid skip from 0.5 to multi-hundred in
a few ticks (the option is deep OTM until it suddenly isn't), so a mid-based
stop gives only illusory protection. A stop expressed in the underlier
(S breaching, say, 5700 = roughly the historical 95th percentile bootstrap)
is the only sensible hedge, but the short is still exposed to overnight /
end-of-round gaps that the 48-hour live window will not reveal.

## 5. Tail loss matrix (300 contracts each strike, credited at 0.5/contract)

| S_T | loss per VEV_6000 | loss per VEV_6500 | total loss, 300 + 300 |
|---:|---:|---:|---:|
| 6 000 | −0.5 (profit) | −0.5 (profit) | **−300** (profit 300) |
| 6 250 | 249.5 | −0.5 | **+74 700** |
| 6 500 | 499.5 | −0.5 | **+149 700** |
| 7 000 | 999.5 | 499.5 | **+449 700** |
| 7 500 | 1 499.5 | 999.5 | **+749 700** |

Position-limit PnL floor is effectively unbounded on the upside of S. The
empirical 99.9-percentile S_T ≈ 6 180 already pushes us into a **~54 000
seashell** tail on the 6000 leg alone before the 6500 leg contributes.

## 6. Fill realism check

- Daily traded volume per strike ≈ 320–345 contracts, 100 % printing at
  price 0. If live sellers can only transact when a buyer lifts the 1-tick
  ask stack (median depth 15–22 contracts), there is **no historical
  evidence of buy-side liquidity above 0**. Shorting 300 contracts at any
  meaningful premium means hoping live markets quote above 1 — an
  assumption the whole 30 000-tick history actively refutes.
- Even if we can realise 0.5 × 300 = 150 premium per strike, the worst-case
  loss in §5 is 3–5 orders of magnitude larger. Sharpe is dominated by
  the tail, not the body.

## 7. Verdict and recommendation

**Park.** The trade fails three of the five rejection gates:

1. *Fill realism.* The 0.5 "mid" is unfillable in history: bid = 0, ask = 1,
   trades print at 0 only. The expected premium is, at best, 1 seashell per
   contract (a lift at the ask), and history shows zero lifts.
2. *Fat-tail dominance.* Empirical Pr(S_T > 6000) is ~5 600× the lognormal
   prior; E[payoff | short 6000 strike] = 0.62 already exceeds the
   optimistic 0.50 premium, so the 6000 leg is negative-EV before
   transaction costs.
3. *Asymmetric risk.* Worst-case S_T = 7 000 (lognormal 7σ, but the
   empirical tail is heavier) inflicts −449 700 seashells on a 600-contract
   book for a maximum gross credit of +300.

If live Round 3 data shows something the history cannot (a genuine bid
above 0 on Day 1, or a visible customer buy flow), revisit with:
- Live first-hour best-bid distribution for VEV_6000 / VEV_6500.
- Any observed trade prints at price ≥ 1 (the signature that premium is
  realisable).

Until then the expected ship-now upside (~115 seashells best case) is
a rounding error versus PnL-at-risk (tens to hundreds of thousands of
seashells) and far worse than the ship-now alphas already in the
registry (A1, B1, C1, G1). Do **not** carry this into the next
iteration without a new data source.
