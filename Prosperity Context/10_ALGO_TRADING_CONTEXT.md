# Algorithmic Trading Context (Round 3 / GOAT)

## Scope

Round 3 ("Gloves Off", Salvinar) algorithmic trading facts, constraints,
and strategy-relevant hints extracted from the official Round 3 doc, the
ARIA uplink transcript, and ten+ public Prosperity 2/3 winner repositories.

Do **not** use this file as the sole source for repo/tooling behavior. For
that, read `30_REPO_AND_TOOLING_CONTEXT.md`.

## Hard interface facts

From the official general context:

- Python `Trader` class with `run(self, state)`; return
  `orders, conversions, traderData`.
- Testing uses 1,000 simulation iterations; final scoring uses 10,000.
- `bid()` is only evaluated in Round 2; ignored in Round 3+. Include or omit.
- `traderData` is the persistence channel across hosted calls (≤ 50,000 chars).
- Hosted execution is stateless with respect to class/global variables.
- `TradingState` includes: `traderData`, `timestamp`, `listings`,
  `order_depths`, `own_trades`, `market_trades`, `position`, `observations`.
- `OrderDepth.sell_orders` volumes are negative.
- Orders that exceed the worst-case aggregated position limit for a product
  in a single iteration cause the exchange to reject **all** orders for that
  product in that iteration. Size defensively.
- Outstanding unmatched orders are canceled at the end of the iteration.
- Hosted execution is effectively instantaneous versus bots.

## Round 3 products

| Symbol | Type | Limit | Notes |
|---|---|---|---|
| `HYDROGEL_PACK` | Delta-1 | 200 | Anchored ~10000 (range 9890–10080 in hist) |
| `VELVETFRUIT_EXTRACT` | Delta-1 underlying | 200 | Trading ~5250, slow drift |
| `VEV_4000` | Call voucher | 300 | K=4000, deep ITM (~intrinsic) |
| `VEV_4500` | Call voucher | 300 | K=4500, deep ITM |
| `VEV_5000` | Call voucher | 300 | K=5000, slightly ITM |
| `VEV_5100` | Call voucher | 300 | K=5100, near-ATM |
| `VEV_5200` | Call voucher | 300 | K=5200, near-ATM |
| `VEV_5300` | Call voucher | 300 | K=5300, OTM |
| `VEV_5400` | Call voucher | 300 | K=5400, OTM |
| `VEV_5500` | Call voucher | 300 | K=5500, OTM |
| `VEV_6000` | Call voucher | 300 | K=6000, far OTM (stuck ~0.5) |
| `VEV_6500` | Call voucher | 300 | K=6500, far OTM (stuck ~0.5) |

**TTE convention**: at start of live Round 3, TTE = 5 days. Historical files
`prices_round_3_day_{0,1,2}.csv` correspond to TTE = 8, 7, 6. Each round is
one day. Prosperity timestamps increment by 100 per tick; a round is 100
ticks (timestamp 0 → 999_900 inclusive, but end-of-round handling varies).

**Year basis**: there is no stated risk-free rate. Use `r = 0`. For IV on an
annualized scale, convert TTE using `T = days / 365` (or 252 if you prefer
trading-day basis — be consistent). The winning P3 team (Timo) used `/365`.

## Strategy playbook (synthesized from past Prosperity 2/3 winners)

The ranking below is ordered by empirical PnL impact in prior rounds and by
how robust each approach is on only three historical days of data.

### 1. Hydrogel Pack — anchored market making

Historical data shows HYDROGEL_PACK oscillating tightly around 10000. This
matches the "pinned fair-value" family (P3 RAINFOREST_RESIN, P2 AMETHYSTS).

Canonical recipe:
- `fair = 10000` hardcoded; revert to market mid only if `|mid - 10000| > 5`.
- Take any ask ≤ `fair - 1` and any bid ≥ `fair + 1` up to full capacity.
- Quote one tick inside the next resting level outside `[fair-1, fair+1]`.
- Skew quote by 1 tick when `|position| > 40` (soft threshold; hard limit 200).
- Keep 2–3 levels of "popular volume" filtering: ignore thin resting quotes
  (`|qty| < 15`) when computing any adaptive mid.

### 2. Velvetfruit Extract — adaptive delta-1 market making

VELVETFRUIT_EXTRACT is slower-drifting (range ~5200–5300). Treat as a KELP /
STARFRUIT analog:
- Compute **wall mid**: average of the bid and ask levels with the largest
  volume in the current book (excluding retail-sized quotes).
- Optional AR(1) adjustment: `fair = wall_mid * (1 + β * last_return)` with
  `β ≈ -0.2` (negative; weak mean-reversion).
- Take when ask ≤ `fair - 1` / bid ≥ `fair + 1`.
- Clear-layer: post an unwind at `fair` when position is non-zero.
- Quote width: `fair ± 2` default, `fair ± 3` when inventory is heavy.

### 3. Voucher IV-residual scalping (core alpha)

Per tick:
1. Compute mid per strike; derive IV per strike (Newton on BS).
2. Fit quadratic `IV(m) = a0 + a1·m + a2·m²` where `m = log(S/K)`.
3. Restrict fit to strikes with meaningful vega and `|m| < 0.35`. Deep-OTM
   strikes (VEV_6000, VEV_6500) should be excluded until data proves otherwise.
4. Residual per strike `res = IV_market - IV_fit`.
5. EMA-smooth `res` with half-life ~20 ticks. Trade when `|res_t - EMA_20|`
   exceeds a per-strike threshold (start ~0.5–1.0 IV-vol points).
6. Widen the threshold on low-vega strikes by +0.5.
7. Convert residual mispricing into price-space via vega; never trade a
   voucher whose vega < 1 for residual scalping (too noisy).

Top P3 winners **froze** their smile coefficients from historical fit and
did not refit live (overfit risk with 3 days of data). Our freeze-candidates:
ATM IV ≈ 0.24, skew slightly negative, convexity positive (see
`prosperity-research/04_signal_notes/round3/vol_surface_coeffs.csv`).

### 4. Delta hedging policy

Empirical rule from P3 post-mortems: hedging every tick burns more PnL than
it saves. Adopt a **dead-band hedge**:
- Compute portfolio delta `D = Σ Δ_i × pos_i` across all 10 vouchers.
- Rebalance only when `|D| > 40` units of VE (tunable). Never hedge to zero;
  hedge to ±20.
- Never hedge with HYDROGEL_PACK — it is uncorrelated.
- The in-repo tooling emits per-strike deltas via
  `scripts/round3_options/bs.py::bs_call_delta`.

### 5. Parity arbitrage (identity gates)

Identity-only checks that are always bounded-payoff arbs if violated *in
tradeable size*:
- Intrinsic floor: `V_K ≥ max(S - K, 0)` — if best-ask < intrinsic: buy.
- Upper bound:    `V_K ≤ S` — if best-bid > S: sell.
- Monotonicity:   for `K1 < K2`, `V_{K1} ≥ V_{K2}` — if best-bid(K1) >
  best-ask(K2): short K1, long K2.
- Convexity:      for equally-spaced `K1 < K2 < K3`,
  `V_{K1} - 2 V_{K2} + V_{K3} ≥ 0` — if violated, butterfly trade.

Important caveat: compute these on the *tradeable side* (ask for buys,
bid for sells), not on mids. Historical mid-based parity scan flags many
0.5 violations that collapse once spreads are respected.

### 6. Counterparty flow

Prosperity typically plants a named "smart" bot. The single highest-alpha
move in P3 was copying `Olivia`. Round 3 has anonymized buyer/seller strings
in historical `trades_round_3_day_*.csv`; run
`scripts/round3_options/counterparty_scan.py` early and watch for
consistently-positive horizon-PnL traders. If such a name appears in
`market_trades` during live trading, copy their direction.

## Ceci n'est pas une pipe — structural warnings to validate

The Round 3 data folder contains a Magritte image as a deliberate hint.
Before trusting any "option" machinery, confirm with data:
- Do the vouchers settle at `max(S_T - K, 0)`? Yes, per official doc.
- Is there time value? Check `time_value_{K}` in the panel. If deep-ITM
  vouchers trade at exactly intrinsic (no time value), the chain is behaving
  more like a set of shifted spot positions than true options.
- Do VEV_6000 / VEV_6500 ever move? Historically no; treat as non-tradable.
- Is there a hidden parity relationship (like put-call) we are missing? There
  are no puts in the chain, but strike-ladder monotonicity must hold.

## Known failure modes

- **Fill model slack**: local Rust backtester can over-report PnL on mean
  reversion strategies that send aggressive marketable quotes. Cross-check
  with official submissions before trusting backtest deltas.
- **Hedge bleed**: naive every-tick portfolio hedging costs ~40k/day on 10
  vouchers given the 1-tick VELVETFRUIT_EXTRACT spread.
- **IV floor collapse**: for deep-ITM vouchers, observed time value may be
  negative due to mid-vs-ask. Do not trade these on IV residual.
- **Off-by-one TTE on the last day**: use sub-tick TTE
  `T = (days_left - timestamp/1e6) / 365` rather than discrete-day rounding.

## Minimal checklist for any algorithm task

- Which round are we shipping into? (Currently 3.)
- Which trader file? Explicit path, no auto-pick.
- Which dataset? Explicit `--dataset round3` / `--day X`.
- What is the baseline we're improving on?
- Is this a structural change (model, hedge band) or a parameter sweep?
- What single backtest will validate the change?
- Are we preserving `(orders, conversions, traderData)` compatibility?

## Condensed reminders

- Pin `HYDROGEL_PACK` fair at 10000 with a ±5 safety band.
- Treat `VELVETFRUIT_EXTRACT` as a drift-aware MM with wall-mid fair value.
- Freeze your vol smile; do not refit live on 3 days of data.
- Exclude VEV_6000 and VEV_6500 from scalping unless they start trading.
- Dead-band the delta hedge; never rebalance to zero.
- Run `parity_scan.py` on every new dataset before trading vouchers.
- Use `counterparty_scan.py` early to catch any planted bot.
