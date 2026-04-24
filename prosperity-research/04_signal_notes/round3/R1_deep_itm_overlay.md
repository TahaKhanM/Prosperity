# R1 — Deep-ITM voucher overlay (VEV_4000 / VEV_4500)

Can VEV_4000 and VEV_4500 serve as legal delta-1 capacity beyond the 200 VE
position limit? Each has a 300-contract limit → up to 600 units of extra
VE-equivalent exposure. Cache: `_cache/r1_deep_itm_overlay.json`.

## 1. Residual `r_K = V_K + K − S` (mid), pooled 30 000 ticks

| strike | mean | median | std | min | max | p01 | p05 | p95 | p99 | %\|r\|>2 | %\|r\|>5 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 4000 | +0.012 | 0 | 0.83 | −7.0 | +7.0 | −1.5 | −0.5 | +0.5 | +2.0 | 1.86 % | 0.92 % |
| 4500 | +0.011 | 0 | 0.76 | −6.0 | +5.5 | −1.5 | −0.5 | +0.5 | +2.0 | 1.83 % | 0.03 % |

Per-day std 0.75–0.84; **median r = 0 every day**. corr(r, dS) ≈
−0.17 / −0.25; corr(dr, dS) ≈ −0.25 / −0.36. Small negative drift —
voucher mid lags S by 0.1–0.2 per 1-shell move. Stale-mid friction, not
alpha.

## 2. Beta of dV_K on dS

| strike | lag 0 β | lag 0 ρ | lag 1 β | lag 1 ρ |
|---|---|---|---|---|
| V_4000 | **0.745** | 0.60 | −0.030 | −0.02 |
| V_4500 | **0.662** | 0.60 | +0.011 | +0.01 |

Not pure 1.0 — mid updates discretised on 1-shell grid with a wide book,
so 25–34 % of a 1-shell S move is missed each tick. Lag-1 β ≈ 0 ⇒ no
"VEV lags VE" free alpha. Delta-1 holds on average, noisy tick-by-tick.

## 3. Book depth and spread — the show-stopper

| product | mean bid | mean ask | mean spread | spread≤2 % | L1 ask vol | total ask vol | % ticks ask≥50 |
|---|---|---|---|---|---|---|---|
| VEV_4000 | 1239.7 | 1260.5 | **20.8** | 0 % | 11 | 33.5 | 0.007 % |
| VEV_4500 | 742.2 | 758.0 | **15.9** | 0 % | 9 | 27.0 | 0 % |

Both books are posted as fixed-width wide MM (spread 20–22 / 15–17 on
≥ 97 % of ticks). **Zero ticks ever expose ≥ 300 ask size** — one-tick
max-size lifts are impossible. Books are never one-sided (bid and ask
both present 100 % of ticks).

### Entry cost `best_ask − (S_mid − K)`

| strike | mean | median | p01 | p05 | min | % ask ≤ intrinsic+1 |
|---|---|---|---|---|---|---|
| VEV_4000 | +10.42 | +10.5 | +8.5 | +9.5 | −2.0 | 0.93 % |
| VEV_4500 | +7.94 | +8.0 | +6.0 | +7.5 | −2.0 | 0.93 % |

Crossing the book costs **~10 shells (4000) or ~8 shells (4500) over
intrinsic** on ~99 % of ticks. Only 0.93 % of ticks show a narrow ask
(within intrinsic+1), with 991 total contracts of ask volume across all
narrow ticks over 3 days — enough for ~330 contracts/day per strike via
opportunistic sniping, not enough for a one-shot max build.

## 4. Settlement — **A: mark-to-mid, no cash settlement**

Rust — `prosperity_rust_backtester/src/runner.rs:277-293`:

```rust
let mid_price = snapshot.and_then(|row| row.mid_price);
let mark_to_market = mid_price
    .map(|price| position.get(product).copied().unwrap_or(0) as f64 * price)
    .unwrap_or(0.0);
let pnl = cash_by_product.get(product).copied().unwrap_or(0.0) + mark_to_market;
```

Python — `imc-prosperity-4-backtester/prosperity4bt/runner.py:95-99`:

```python
position = state.position.get(product, 0)
if position != 0:
    product_profit_loss += position * row.mid_price
```

No end-of-run branch in either (Rust loop `:333`, Python iterator
`:352-355`). Neither runner simulates `max(S_T − K, 0)`.

Gate-4-binding impact: a trader holding 300 long VEV_4000 entered at
mean ask 1260.5, closing via backtester mark at mid 1250.1, records
**−3 126 shells** of backtest PnL while the live grader (cash-settled at
day-2 close S_T = 5295.5) returns **+10 495 shells**.

**Test-trader recipe.** Post-run patch: on the final tick, for each
VEV_* product replace `position × last_mid` with
`position × max(last_S − K, 0)` using VE's last mid as S_T. Rust: branch
after `runner.rs:284` on `tick_idx == last_idx && product.starts_with("VEV_")`.
Or Python post-processor over `pnl_series.csv` + positions. Validate:
same trader flat vs. 300-long → PnL delta = `300 × (S_T − 4000 − entry)`.

## 5. Expected PnL of static 300-long VEV_4000 to expiry

S0 = 5250.10 (pooled mean), σ = 0.244, T = 5/365. Lognormal
`E[max(S_T − 4000, 0)] = 1250.10` (no TV). Entry = mean ask = 1260.52.

| scenario | S_T | payoff | entry | PnL / ctr | 300 lot |
|---|---|---|---|---|---|
| day-0 close | 5244.0 | 1244.0 | 1260.5 | **−16.52** | −4 956 |
| day-1 close | 5265.5 | 1265.5 | 1260.5 | **+4.98** | +1 495 |
| day-2 close | 5295.5 | 1295.5 | 1260.5 | **+34.98** | +10 495 |
| lognormal E | — | 1250.1 | 1260.5 | **−10.42** | **−3 126** |
| narrow-ask  | — | ≈ 1250 | ≤ 1251 | 0 to +45 | 0 to +13 k |

P(S_T < 4000) ≈ 0 (z ≈ −19); worst hist S = 5198 leaves 1 198 cushion.
**No zero-or-negative-payoff risk in 5 days.** But at mean-ask entry
the static overlay is a **structural loser** — premium paid > drift
expectation. Profitable only via narrow-ask sniping or as a hedge leg
netted against a short-vol book.

## 6. Sizing and hedging formula

> For every Δ_short units of short-vol voucher delta, hold **Δ_short
> units of VEV_4500 (or VEV_4000) long** to offset. Net VE-equivalent
> delta = 0, core VE inventory untouched.

Ceiling interaction: VE limit 200, VEV_4000 300, VEV_4500 300 →
total VE-equivalent long cap = 800. Worked example: short 100 VEV_5300
with summed dealer delta +70 (long 70 VE-equivalent needed to hedge) →
hold 70 VEV_4000 long; VE position = 0, net delta = 0, books
independent.

## 7. Parameter recommendations

- **Prefer VEV_4500.** Ask premium ~8 vs ~10, half the capital per
  contract, p_|r|>5 is 0.03 % vs 0.92 %.
- **Max overlay size: 200 / strike** (keep 100 headroom to the 300 cap).
- **Entry rule.** Only take when `best_ask − (S_bid − K) ≤ 1`. Fires on
  0.93 % of ticks, supplies ~330 contracts/day — adequate for a 200-lot
  build, not for 300+300 in a day.
- **Exit rule.** Hold to expiry (final tick) **iff the settlement patch
  is live**. Otherwise unwind on penultimate tick at mid to avoid the
  mark-to-mid trap. In real live play: just hold — grader cash-settles.
- **No vega on these strikes.** IV ≡ 0; the overlay is strictly delta-1.

## 8. Falsifier

> Live `best_ask(VEV_4000) − (S_mid − 4000) > 3` shells **for 200
> consecutive ticks** → overlay invalid.

Justification: historical p99 of ask premium is 11.5 so > 11 is normal
wide-MM noise. The diagnostic is *disappearance of narrow-ask windows*:
if for 200 consecutive ticks (~2 % of a day) no ask prints within
intrinsic+3, the MM band has regime-shifted and the funding cost of the
overlay has changed. 200 ticks is long enough to filter single-tick
chatter, short enough to react same-session.

## 9. Verdict

> **Research-more — conditional on settlement patch.**
>
> Structurally the overlay is real: residuals tight (median 0, 98 %
> within ±2), lag-0 β ≈ 0.7, book never one-sided, zero-or-negative
> payoff probability ~0 over 5 days. Two hard frictions bind:
>
> 1. **Backtester mid-fill settlement error** (gate 4). Held-to-expiry
>    overlay loses in historical backtests while actually making money
>    live. Patch the runner or add a post-run settle script before
>    shipping.
> 2. **Market-ask entry is a structural loser** (premium ~10 > drift
>    expectation). Only profitable via narrow-ask sniping (0.93 % of
>    ticks) or as a hedge leg netted against short-vol book.
>
> Ship when (a) settlement patch is merged and round-trip validated
> against `300 × (S_T − K − entry)`, and (b) trader has explicit
> `ask ≤ intrinsic + 1` entry gate. Start at 50 / strike. Stand-alone
> alpha 0–1 k / day (matches E1 card); primary value is as a hedge
> vehicle for a larger short-vol book.
