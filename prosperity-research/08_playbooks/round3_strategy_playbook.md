# Round 3 Strategy Playbook

Synthesis of public Prosperity 2/3 winner code + our own EDA on the 3-day
Round 3 historical dataset. This is a concrete, ranked set of alphas with
starting hyperparameters, ready to be turned into trader variants.

## 1. HYDROGEL_PACK — soft-anchor market making (high confidence)

**Claim.** `HYDROGEL_PACK` has a slowly-moving empirical mean of **9991**,
NOT 10000. Per the alpha hunt (see `structural_quirks.md` §1), only 13.8 %
of ticks sit within ±5 of 10000. Mid persistence ρ₁ = 0.997, OU half-life
≈ 300 ticks, Hurst ≈ 0.47 (near random walk). Treat it as a slow-OU series,
not a pin.

**Hyperparameters (start):**
```
anchor_mean         = 9991
anchor_lo           = 9980
anchor_hi           = 10010
ema_half_life       = 200      # ~observed OU half-life / 1.5
take_width          = 1
clear_width         = 0
quote_edge          = 4
soft_position_limit = 80       # hard limit is 200
adverse_volume      = 15       # ignore levels below this when computing mmmid
```

**Tick logic:**
1. Compute `mmmid` from levels with `|qty| >= adverse_volume`.
2. Compute `fair = clamp(EMA(mid, half_life), anchor_lo, anchor_hi)`; seed
   the EMA with `anchor_mean = 9991` on the first tick.
3. For each ask level `p_a, q_a` with `q_a > 0`: if `p_a ≤ fair - take_width`,
   buy min(`q_a`, capacity_buy).
4. Symmetric for bids.
5. Post one bid: the lowest of (best_bid + 1, fair - quote_edge). Skew by
   the imbalance overlay (§3) and by -1 if position > soft_limit.
6. Post one ask: the highest of (best_ask - 1, fair + quote_edge). Skew by
   the imbalance overlay and by +1 if position < -soft_limit.

**Validation:** backtest against Round 3 day 0/1/2. Expect positive PnL on
every day; ~1/3 of PnL should come from takes, rest from the quote book.

**Why NOT `fair = 10000`.** Alpha hunt axis A showed `fair = 10000` sits
outside the empirical 9991±5 basin 86 % of the time, burning ~40 % of
available PnL through missed takes and asymmetric adverse-selection.

## 2. VELVETFRUIT_EXTRACT — wall-mid adaptive MM (medium confidence)

**Claim.** VE drifts slowly. Use the thick ("wall") levels as fair; AR(1)
correction optional.

**Hyperparameters (start):**
```
wall_qty_threshold = 20
ar1_beta           = -0.2       # mild mean reversion
take_width         = 1
clear_width        = 1
default_edge       = 3
soft_limit         = 40         # hard 200
```

**Tick logic:**
1. Find `bid_wall` = top bid level with `qty ≥ wall_qty_threshold`, similar
   `ask_wall`. Fair = `(bid_wall + ask_wall) / 2`.
2. Optional AR(1) adjustment: `fair += β * last_return`.
3. Take / quote / skew identically to HYDROGEL_PACK.

**Validation:** stability of fair series across days; no drift of cumulative
PnL toward negative.

## 3. Order-book imbalance overlay (additive to §1 and §2)

**Claim.** Top-2-level order-book imbalance predicts 1-tick return. Alpha
hunt axis C: `imb = (Σbid_1+Σbid_2 − Σask_1−Σask_2) / total`. t-stat ~35 on
HYDROGEL, ~20 on VE. `k=3` flips sign (level-3 quotes are adversarial), so
stay at k ≤ 2.

**Hyperparameters:**
```
imb_k              = 2
hydrogel_skew_beta = 12   # fair += 12 * imb, capped ±2 ticks
ve_skew_beta       = 3    # fair += 3  * imb, capped ±2 ticks
skew_cap_ticks     = 2
```

**Tick logic.** Apply the skew after computing fair in §1/§2 and before
posting quotes. Never exceed `skew_cap_ticks` displacement.

## 4. Voucher IV-residual scalping — exploratory, not shipping yet

**Claim.** The smile is approximately parabolic in log-moneyness with
observed coefficients (from our EDA):
```
ATM_IV     ≈ 0.24
skew (a1)  ≈ -0.08
convexity  ≈ +7.7
```
(`year_basis = 365` assumed; all 30,000 historical ticks fit).

**Hyperparameters (start):**
```
year_basis          = 365
smile_fit_band      = [-0.35, +0.35]   # log-moneyness window
residual_ema_hl     = 20 ticks
scalp_threshold     = 0.5              # |residual - EMA| in IV points
vega_min_threshold  = 1.0              # skip strikes with vega < 1
low_vega_threshold_bump = 0.5          # widen threshold on borderline strikes
exclude_strikes     = [6000, 6500]     # stuck ~0.5 historically
```

**Tick logic:**
1. Compute underlying mid S. Compute TTE in years:
   `T = (days_left - ts / 1_000_000) / 365`.
2. For each voucher K not in exclude_strikes: compute mid V, IV via BS
   Newton, vega via BS.
3. Fit quadratic `IV(m) = a0 + a1·m + a2·m²`, `m = log(S/K)`. Consider
   *freezing* the coefficients from historical fit; do **not** refit live
   in the first submission (overfit risk).
4. `res_K = IV_market(K) - IV_fit(m)`.
5. EMA residual with half-life 20. Trade when
   `|res_K - EMA(res_K)| > scalp_threshold + low_vega_bump·𝟙{vega<2}`.
6. Direction: residual > threshold → voucher rich → sell (buy VE delta to
   hedge band). Residual < -threshold → voucher cheap → buy.
7. Size: Δposition = min(available_capacity, `floor(|residual| / threshold) * unit`).

**Validation:** PnL per strike is positive on at least 2 of 3 historical
days; hedge bleed stays below 20% of scalping PnL.

**⚠️ Gate 4 warning from alpha-hunt.** The Rust backtester fills at mid on
aggressive quotes, so a naive D1 residual-scalp over-reports PnL by ~2×.
Do NOT ship D1 until (a) the fill model is tightened to require crossing
the book, OR (b) the scalp validates on hosted submission logs.

**TTE-drift calendar alpha (new, card L1 in registry).** ATM IV, skew, and
convexity all drift monotonically as TTE shrinks:

| TTE | ATM IV | skew | convexity |
|---|---|---|---|
| 8d | 0.242 | −0.011 | 7.21 |
| 7d | 0.245 | −0.086 | 7.85 |
| 6d | 0.247 | −0.161 | 8.84 |

Linear projection to live TTE = 5d: convexity ≈ 9.6, skew ≈ −0.24, ATM IV
≈ 0.249. A butterfly `-1·VEV_5100 +2·VEV_5200 -1·VEV_5300` profits if
convexity keeps rising. The drift is large vs daily noise (+0.8/day vs σ
≈ 0.4/day). Flagged for deeper research before shipping.

## 4a. Deep-ITM synthetic delta-1 overlay (VEV_4000 / VEV_4500) — NEW

**Claim from alpha-hunt (card E1, structural quirk §2).** VEV_4000 and
VEV_4500 carry zero time value (median TV = 0 across 30,000 historical
ticks). They trade as synthetic delta-1 proxies: `V_K ≈ max(S - K, 0) ≈
S - K` for K ≪ S. This gives a legal way to exceed the 200 VE position
limit: holding 1 long VEV_4000 is economically equivalent to 1 unit of VE +
cash payment of 4000 at expiry. With pos limit 300 per strike × 2 deep-ITM
strikes = **+600 additional VE-equivalent capacity**.

**Probability of S_T < 4000 over live 5-day horizon.** At S_0 ≈ 5250,
σ_ATM ≈ 0.24, σ_5d = 0.24 √(5/365) ≈ 0.028, z = log(4000/5250)/σ ≈ −9.7.
Effectively zero. Similar for S_T < 4500 (z ≈ −5.5, P ≈ 2·10⁻⁸).

**Hyperparameters (start, subject to E1 research validation):**
```
deep_itm_strikes    = [4000, 4500]
deep_itm_size_cap   = 100 per strike   # well below 300 pos limit
entry_price_edge    = 1       # buy only if ask ≤ S_bid − K + 1
expected_pnl_hedge  = "use as VE hedge for short-vol voucher positions"
```

**Risk flag.** The Rust backtester's end-of-round liquidation behavior for
voucher positions may diverge from hosted (per §30_REPO_AND_TOOLING_CONTEXT
— conversions and settlement are not faithfully simulated). Validate before
committing capital. See `round3_deep_structural_research.md` prompt.

## 5. Delta hedging policy

**Claim.** Every-tick portfolio hedging bleeds more than it protects.

**Hyperparameters (start):**
```
delta_band          = 40        # VE units
rebalance_target    = 0         # hedge to flat (not ±0)
hedge_only_in_VE    = True      # never use HYDROGEL
```

**Tick logic:**
1. `D = Σ_K Δ(K) * pos(K)` across all vouchers (sign: long call → +Δ).
2. If `|D| ≤ delta_band`: no hedge.
3. Else trade `-D` units of VELVETFRUIT_EXTRACT (cross the book if needed;
   otherwise post an aggressive limit at best bid/ask).

## 5. Identity parity gates

**Claim.** Any violation in tradeable size is a bounded-payoff arb. Must
be evaluated on best-bid/best-ask, not mids.

**Hyperparameters (start):**
```
parity_min_edge     = 1         # seashells, gross of spread
parity_size         = 10        # per-trade size cap
```

**Tick logic:**
1. For each K: if best_ask(K) < max(S - K, 0) - parity_min_edge, buy up to
   parity_size. If best_bid(K) > S + parity_min_edge, sell.
2. Strike-monotonicity: for K1 < K2, if best_bid(K1) > best_ask(K2) +
   parity_min_edge, short K1 + long K2.
3. Convexity butterflies: skip in first iteration (three-leg execution risk).

## 6. Counterparty copy

**Claim.** A named bot may appear with consistently-positive horizon PnL on
VE or VEV_* trades.

**Tick logic:**
1. In traderData, maintain a rolling-window (last 50 trades per product) of
   `{counterparty → (count, signed_qty, horizon_pnl_proxy)}`.
2. If any counterparty has mean horizon PnL > 2 seashells over ≥ 20 trades,
   flag as "informed".
3. When an "informed" name appears on `state.market_trades[symbol]` in the
   current tick: adjust skew +1 in their direction for the next 20 ticks.

## Integration plan

Build one trader that combines (1), (2), (3), (4), (5), (6) behind
feature flags in traderData:
```json
{
  "config": {
    "mm_hydrogel": true,
    "mm_ve": true,
    "iv_scalp": true,
    "delta_hedge": true,
    "parity_gates": true,
    "counterparty_copy": false
  }
}
```

**Shipping order:**
1. (1) + (2) only — validate delta-1 MM PnL.
2. Add (5) parity gates — cheap and safe.
3. Add (3) scalping + (4) hedging — the core alpha.
4. Add (6) counterparty copy only once a "smart" bot is confirmed.

**Success criterion:** cumulative PnL on Round 3 day 0 + day 1 + day 2
exceeds (10k × days) with no single-day drawdown > 5k.
