# Manual Trading Context (Round 4 / Aether Crystal options)

## Scope

Round 4 manual challenge: trade the **Aether Crystal** and a set of vanilla
and exotic options written on it. Independent of the algorithmic trader.
Submit once before the round timer expires; final manual submission counts.

## Official mechanics (from `New Context/round_4_trading_round.md`)

- Underlying: **Aether Crystal**. Manual-only — does not appear in
  algorithmic `order_depths`.
- Available contracts: standard vanilla calls and puts on the Aether Crystal,
  plus three exotics:
  - **Chooser**: K=50 XIRECS, expiry 21 Solvenarian days, decision at day 14.
    After the decision date, contract auto-converts to whichever of call/put
    is **in the money** at that moment, then behaves vanilla until expiry.
  - **Binary put**: K=40 XIRECS, expiry 21 days. Pays a fixed **10 XIRECS**
    if `S_T < 40`, else 0.
  - **Knockout (down-and-out) put**: K=45 XIRECS, barrier 35 XIRECS, expiry
    21 days. Settles as a vanilla put with K=45 *iff* the Aether Crystal
    never falls below 35 during the contract's lifetime; if the barrier is
    breached even momentarily, the contract is knocked out and pays 0.
- The full list of vanilla strikes, sizes, and prices appears only in the
  Manual Challenge Overview window in the Prosperity UI; we do not have a
  CSV. Expect a small number of strikes (single-digit count is typical for
  Prosperity manual rounds).
- Submission interface: the Manual Challenge Overview window. You may adjust
  your submission as long as time remains. **Final submission counts.**
- Position constraint: **available volume per contract** is the only
  practical limit; otherwise pick whatever combination you like.

## Currency

The brief uses `XIRECS` for binary-put payoffs and `ZYREX` for the chooser /
knockout strikes. The ARIA uplink uses `Zyrex / XYX`. They all refer to the
same in-game currency. Use `XIRECS` in code and notes.

## Pricing model — what to use

Use Black-Scholes with `r = 0` as the baseline pricer. The in-repo utilities
are at `prosperity_rust_backtester/scripts/round4_options/exotic_pricers.py`:

- `vanilla_call(S, K, T, sigma)` — standard BS call.
- `vanilla_put(S, K, T, sigma)` — standard BS put.
- `chooser_value(S, K, T, T_choice, sigma)` — simple-chooser identity:
  `Chooser = C(S, K, T) + P(S, K * exp(-r * (T - T_c)), T_c)`.
  Under `r = 0`, this collapses to `C(S,K,T) + P(S,K,T_c)`.
- `digital_put_value(S, K, T, sigma, payoff=10)` — closed-form digital put;
  pays `payoff` if `S_T < K`. For BS: `payoff * N(-d2)`.
- `down_and_out_put(S, K, B, T, sigma)` — Reiner-Rubinstein closed-form for
  down-and-out put (vanilla put minus down-and-in put rebate).

All pricers default to `r = 0` and the year basis = 365.

## Strategy — phase-by-phase

The Round 4 hint cards are explicit: think about the exotic exposure FIRST,
then layer vanillas to bound the risk.

### Step 1 — calibrate σ on the Aether Crystal

The wiki / brief does not give you historical Aether Crystal price data. You
have only:
- The current best ask / best bid on each contract in the Manual Challenge
  window.
- The strikes and expiries listed above.

Recover an implied σ by inverting BS on whichever vanilla you trust most
(typically near-the-money, longest-dated). Use that σ to price the exotics
and the rest of the vanilla chain.

### Step 2 — fair-value the exotics

| Contract | Closed-form fair value | Greeks to watch |
|---|---|---|
| Chooser K=50 | `C(S,50,21d,σ) + P(S,50,14d,σ)` | Long both vol AND delta; positive convexity. |
| Binary put K=40 | `10 * N(-d2(S,40,21d,σ))` | Tiny vega; pure short-tail exposure. |
| Knockout put K=45, B=35 | `Put(45) - DownInPut(45, B=35)` | Path-dependent; falls fast as S → B. |

Compare each market price to the BS fair. The hint card's framing is "look
for the contract that prices in materially more uncertainty than the rest."

### Step 3 — replicate / hedge with vanillas

The hint cards' core advice (Cards 5 and 6):

> "before you get too attached to your exotic position, ask yourself whether
> part of that exposure could be replicated with vanilla options."

Concretely:

- **Chooser** decomposes exactly into a call + a put (above formula). If the
  chooser is over-priced vs. the synthetic call+put, sell chooser and buy the
  call+put combo. Net delta ≈ 0; you collect the mispricing.
- **Binary put** ≈ tight put-spread. `Digital(K) ≈ (Put(K+ε) - Put(K-ε)) /
  (2ε) * notional`. If the digital trades far from the put-spread fair, do
  the same arb.
- **Knockout put** has no clean linear replication, but its fair value is
  bounded above by the vanilla put with the same K. If the knockout trades
  *above* the vanilla put (it cannot be worth more), short the knockout and
  long the vanilla put — risk-free arb modulo execution.

### Step 4 — size by conviction (Card 3 — "Volume")

> "Bigger gap, bigger position. Smaller gap, smaller position."

Score each opportunity by `|market - fair| / σ_market_price` and allocate
budget proportionally, capped by available volume per contract.

## Specific Round 4 Aether Crystal heuristics

These are tentative until we observe the live Manual Challenge window:

1. **Knockout put (K=45, B=35)**: barrier sits 10 below the strike. If the
   underlying is currently > 50 with low realised vol, the knockout is close
   to a vanilla put — arbitrage opportunity if it trades materially below.
2. **Binary put (K=40)**: only pays 10. Maximum value is 10. If the offer is
   significantly above the BS digital fair (e.g. > 6 with S = 50, σ = 0.3,
   T = 21d), it is over-priced.
3. **Chooser**: the simple-chooser identity is exact under r = 0; if the
   chooser asks more than `C(S,50,21) + P(S,50,14)` you can sell-chooser
   buy-vanillas for a deterministic edge.

Run the math in
`prosperity-research/07_manual_round/round4_aether/decision_memo.md`
once the live prices are visible.

## Decision memo template

For each manual submission, populate
`prosperity-research/07_manual_round/round4_aether/decision_memo.md` with:

1. **Observed inputs**: spot S, vanilla bids/asks per strike, exotic
   bids/asks, available volume per contract.
2. **Calibrated σ**: which vanilla(s) you used, what σ they implied, and a
   robustness check across two strikes.
3. **Fair value table**: per-contract market vs. BS fair, plus signed gap.
4. **Replication trades**: which exotics you replicate with which vanillas,
   net Greeks of the package.
5. **Chosen positions**: contract / direction / size, with reasoning.
6. **Worst-case PnL**: max loss across plausible terminal Aether Crystal
   prices, and the path-sensitivity of the knockout leg.
7. **Invalidation test**: what would change your view enough to resubmit.

## Pitfalls

- **Knockout put barrier is touch, not close.** "Not even momentarily" — if
  the underlying ticks 35 once and bounces back, the contract dies. Do not
  assume daily-close monitoring.
- **Chooser auto-conversion is "ITM at decision"**, not "ATM straddle held
  open". After day 14, chooser becomes a fixed call or put, no further
  optionality. The simple-chooser identity is still the right pricer until
  the decision date; after that, price as a vanilla.
- **Binary put pays a discrete 10**, not a continuous payoff. Vega is tiny
  and second-order: do not over-fit σ to it.
- **No live data for Aether Crystal in CSVs.** The `prices_round_4_day_*.csv`
  files only cover the algorithmic products. Calibration uses the on-screen
  vanilla prices, period.
- **Final submission wins** — adjust freely while time remains, but do not
  forget to save the version you actually want.

## Archived manual tasks (for reference only)

- **Round 3 — Bio-Pods / Celestial Gardeners** (closed): two-bid auction
  against a hidden reserve, with a μ̄-driven cubic penalty arm on the second
  bid. Resale value 920. Optimal `(b1, b2) ≈ (907, 915)` for the typical
  μ̄ ≈ 910–912. Decision memo at
  `prosperity-research/07_manual_round/round3_biopods/decision_memo.md`.
- **Round 1 Exchange Auction** (ember mushrooms, dryland flax) — static book,
  single clearing price, volume-maximising with higher-price tiebreak.
  Fees: 0.05 per-unit on ember mushroom trades.
- **Round 2 Invest & Expand** — 50,000 XIRECs across Research (log),
  Scale (linear), Speed (rank-based). Formula
  `PnL = Research × Scale × Speed - Budget_Used`.

All historical; manual R4 PnL is independent.
