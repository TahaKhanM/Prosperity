# Algorithmic Trading Context (Round 4 / GOAT)

## Scope

Round 4 ("The More The Merrier", Salvinar) algorithmic trading facts,
constraints, and strategy-relevant hints extracted from the official Round 4
doc (`New Context/Round 4 Trading round.md`), the ARIA uplink, the Round 4
hint cards, and the Round 3 alpha-hunt results that carry over (same
products, same dynamics).

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

## Round 4 — what is new

1. **Counterparty IDs are disclosed.** The `buyer` and `seller` fields on
   every `Trade` object now contain a string like `"Mark 14"` instead of
   `None`. This is the central new alpha for the round.
2. **No new tradable algorithmic products.** Same 12 symbols as Round 3.
3. **TTE shifts.** Round 4 historical days correspond to TTE 7/6/5; live
   Round 4 = TTE 4 days.

```python
# Datamodel snippet (from the official brief)
class Trade:
    def __init__(self, symbol, price, quantity,
                 buyer=None, seller=None, timestamp=0):
        self.symbol = symbol
        self.price = price
        self.quantity = quantity
        self.buyer = buyer        # ← now populated, e.g. "Mark 14"
        self.seller = seller      # ← now populated
        self.timestamp = timestamp
```

The same fields are populated in `state.market_trades[symbol]` and
`state.own_trades[symbol]`.

## Round 4 products

| Symbol | Type | Limit | Notes |
|---|---|---|---|
| `HYDROGEL_PACK` | Delta-1 | 200 | Mean ~9992–10003 (range 9908–10081 in R4 hist) |
| `VELVETFRUIT_EXTRACT` | Delta-1 underlying | 200 | Range ~5191–5300, slow downward drift across 3 days |
| `VEV_4000` | Call voucher | 300 | K=4000, deep ITM (~intrinsic, TV≈0) |
| `VEV_4500` | Call voucher | 300 | K=4500, deep ITM (~intrinsic, TV≈0) |
| `VEV_5000` | Call voucher | 300 | K=5000, slightly ITM |
| `VEV_5100` | Call voucher | 300 | K=5100, near-ATM |
| `VEV_5200` | Call voucher | 300 | K=5200, near-ATM |
| `VEV_5300` | Call voucher | 300 | K=5300, OTM |
| `VEV_5400` | Call voucher | 300 | K=5400, OTM |
| `VEV_5500` | Call voucher | 300 | K=5500, OTM |
| `VEV_6000` | Call voucher | 300 | K=6000, far OTM (stuck ~0.5) |
| `VEV_6500` | Call voucher | 300 | K=6500, far OTM (stuck ~0.5) |

**TTE convention**: at start of live Round 4, TTE = **4 days**. Historical
files `prices_round_4_day_{1,2,3}.csv` correspond to TTE = 7, 6, 5. Each
round is one day. Prosperity timestamps increment by 100 per tick; a round
is 10,000 ticks (timestamp 0 → 999_900 inclusive, but end-of-round handling
varies).

**Year basis**: there is no stated risk-free rate. Use `r = 0`. For IV on an
annualized scale, convert TTE using `T = days / 365` (or 252 if you prefer
trading-day basis — be consistent). The winning P3 team (Timo) used `/365`.

## Counterparty intelligence (the headline R4 alpha)

Source: `prosperity-research/03_eda/round4/headline_findings.md` and
`counterparty_summary.csv`. Numbers are total horizon-500 PnL across days
1+2+3 for each Mark.

| Mark | Buy qty | Sell qty | h500 PnL | per-unit | Role | Action |
|---|---|---|---|---|---|---|
| Mark 14 | 4510 | 4208 | +49,777 | +5.71 | **Smart bot** | **Copy** their direction |
| Mark 01 | 6053 | 1375 | +10,334 | +1.39 | High-volume MM-ish | Lean weakly with |
| Mark 67 | 1510 | 0 | +1,796 | +1.19 | **Buy-only on VE** | **Lean long VE** when seen |
| Mark 49 | 115 | 1071 | −1,356 | −1.14 | Modest informed seller of VE | Fade their buys |
| Mark 22 | 206 | 5683 | −3,058 | −0.52 | Voucher MM seller (paired w/ Mark 01) | Noise |
| Mark 55 | 3254 | 3297 | −15,798 | −2.41 | Loss-maker | Mild fade |
| Mark 38 | 2493 | 2507 | −41,696 | −8.34 | **Bag-holder** | **Fade** explicitly |

Pair structure:
- **Mark 14 ↔ Mark 38** (1,442 trades): closed loop on HYDROGEL / VE / VEV_4000.
  Mark 14 takes the right side, Mark 38 takes the wrong side, by ~8/unit.
- **Mark 01 ↔ Mark 22** (1,339 trades): voucher MM pair on the OTM strikes
  (VEV_5300+, including the stuck VEV_6000/VEV_6500). PnL ±0.5/unit. Noise.

VEV_4000 and VEV_4500 PnL numbers reflect VE drift, not options alpha
(deep-ITM, TV≈0). When Mark 14 buys VEV_4000, treat it as a "Mark 14 thinks
VE goes up" signal, not as an options trade.

Implementation pattern (intended for a R4 trader):

```python
# In your run():
for trade in state.market_trades.get("VELVETFRUIT_EXTRACT", []):
    if trade.buyer == "Mark 14":          # smart bot bought VE
        ve_lean += +1                       # join the long
    elif trade.seller == "Mark 14":        # smart bot sold VE
        ve_lean -= 1
    if trade.buyer == "Mark 38":           # bag-holder bought VE
        ve_lean -= 1                        # fade them
    elif trade.seller == "Mark 38":
        ve_lean += 1
    if trade.buyer == "Mark 67":           # buy-only informed buyer
        ve_lean += 1
```

Persist the per-product lean in `traderData` (it should decay over a few
hundred ticks; a Mark print should not influence quotes 5,000 ticks later).

## Carry-over alphas from Round 3 (re-validated, ship-now)

The R3 alpha hunt produced 5 alphas that all passed the rejection gates.
Products and microstructure are unchanged in R4, so these still apply:

### A1 — HYDROGEL soft-anchor MM (carry over)

Round 4 day 1 HYDROGEL mean = 9992.06; day 3 = 10002.50. **HYDROGEL is not
pinned at 10000.** Use:

- `fair = clamp(EMA_200, 9980, 10010)`, seed at the empirical day-mean.
- Take any ask ≤ `fair - 1` and bid ≥ `fair + 1` up to capacity.
- Quote one tick inside the next resting level outside `[fair-1, fair+1]`.
- Skew quote by 1 tick when `|position| > 40`.
- Ignore retail-thin quotes (`|qty| < 15`) when computing adaptive mid.

### B1 — VE wall-mid MM (carry over)

VE day 1 mean = 5248; day 3 mean = 5239. Slow downward drift, narrow range.
- **Wall mid**: average of the bid and ask levels with the largest volume.
- Optional AR(1): `fair = wall_mid * (1 + β * last_return)` with `β ≈ -0.2`.
- Take when ask ≤ `fair - 1` / bid ≥ `fair + 1`.
- Clear-layer at `fair` when position is non-zero.
- Quote width: `fair ± 2` default, `fair ± 3` when inventory is heavy.

### C1 — Top-2 imbalance skew (carry over)

For HYDROGEL and VE, compute order-book imbalance from levels 1 and 2 of
both sides. Skew the fair by `±1 tick` when imbalance crosses ±0.6.

### D1 — Voucher IV-residual scalping with TTE-indexed smile (carry over)

Per tick:
1. Compute mid per strike; derive IV per strike (Newton on BS).
2. Fit quadratic `IV(m) = a0 + a1·m + a2·m²` where `m = log(S/K)`,
   **indexed by TTE bucket** (R3 found skew −0.011 → −0.161 and convexity
   7.21 → 8.84 across TTE 8d → 6d). Re-fit for R4 TTE 7/6/5/4 buckets.
3. Restrict fit to strikes with meaningful vega and `|m| < 0.35`. Exclude
   VEV_6000, VEV_6500 (stuck ~0.5).
4. Residual per strike `res = IV_market - IV_fit`.
5. EMA-smooth `res` with half-life ~20 ticks. Trade when
   `|res_t - EMA_20|` exceeds a per-strike threshold (start ~0.5–1.0 IV
   points). Widen by +0.5 on low-vega strikes.
6. Convert residual mispricing into price-space via vega; never trade a
   voucher whose vega < 1 for residual scalping.

### E1 — Deep-ITM as VE-equivalent capacity (carry over)

VEV_4000 and VEV_4500 are essentially synthetic VE with delta ≈ 1 and
TV ≈ 0. Treat them as +600 units of additional VE-equivalent position
capacity (300 × 2 strikes). Do not trade them on IV residual.

### G1 — Parity guard (defensive, carry over)

Identity-only checks, always bounded-payoff arbs if violated *in tradeable
size*:
- Intrinsic floor: `V_K ≥ max(S - K, 0)` — if best-ask < intrinsic: buy.
- Upper bound:    `V_K ≤ S` — if best-bid > S: sell.
- Monotonicity:   for `K1 < K2`, `V_{K1} ≥ V_{K2}`.
- Convexity:      for equally-spaced `K1 < K2 < K3`,
  `V_{K1} - 2 V_{K2} + V_{K3} ≥ 0`.

Compute on the *tradeable side* (ask for buys, bid for sells), not on mids.
Historical R3 mid-based scan over-reports violations.

## Delta hedging policy (carry over)

Empirical rule from P3 post-mortems: hedging every tick burns more PnL than
it saves. Adopt a **dead-band hedge**:
- Compute portfolio delta `D = Σ Δ_i × pos_i` across all 10 vouchers.
- Rebalance only when `|D| > 40` units of VE (tunable). Never hedge to zero;
  hedge to ±20.
- Never hedge with HYDROGEL_PACK — it is uncorrelated.
- The in-repo tooling emits per-strike deltas via
  `scripts/round4_options/bs.py::bs_call_delta`.

## Rejected/weak signals (do not waste cycles)

- **HYDROGEL spectral 3330-tick rhythm**: day-0-only artefact in R3; revalidate
  on R4 days 1/2/3 before trusting.
- **HYDROGEL 1-tick AC1 fade**: spread cost (8/round-trip) exceeds the
  reversion edge (~0.27).
- **HYDROGEL imb_k3 multivar skew**: signal too narrow to fire usefully.
- **VFE→voucher cross-asset lead-lag**: same-tick correlation 0.62, all lags
  ≈ 0. No predictability beyond contemporaneous delta link.
- **Per-strike static IV biases**: knife-edge; small magnitudes blow up the
  BT.
- **Counterparty time-of-day gating**: temporal concentration is weak in R4
  data (peak hour-bucket share ≤14 %). Do not gate on hour.

## Known failure modes

- **Fill model slack**: local Rust backtester can over-report PnL on mean-
  reversion strategies that send aggressive marketable quotes. Cross-check
  with official submissions before trusting backtest deltas.
- **Hedge bleed**: naive every-tick portfolio hedging costs ~40k/day on 10
  vouchers given the 1-tick VE spread.
- **IV floor collapse**: for deep-ITM vouchers, observed time value may be
  negative due to mid-vs-ask. Do not trade these on IV residual.
- **Off-by-one TTE on the last day**: use sub-tick TTE
  `T = (days_left - timestamp/1e6) / 365` rather than discrete-day rounding.
- **Counterparty-name string mismatch**: the names contain a space
  (`"Mark 14"`, not `"Mark14"`). Compare exact strings; do not strip.
- **Counterparty signal contamination on stuck strikes**: Mark 01's flow on
  VEV_6000/VEV_6500 is MM noise (PnL ±0.5/unit). Filter counterparty signals
  per (mark, product), not blanket per-mark.

## Minimal checklist for any algorithm task

- Which round are we shipping into? (Currently 4.)
- Which trader file? Explicit path, no auto-pick.
- Which dataset? Explicit `--dataset round4` / `--day 1|2|3`.
- What is the baseline we're improving on?
- Is this a structural change (model, hedge band) or a parameter sweep?
- What single backtest will validate the change?
- Are we preserving `(orders, conversions, traderData)` compatibility?
- Are we using the new counterparty fields, or ignoring them on purpose?

## Condensed reminders

- `state.market_trades[symbol][i].buyer` and `.seller` are now populated.
- Mark 14 = smart, copy. Mark 38 = bag-holder, fade. Mark 67 = lean long VE.
- HYDROGEL is NOT pinned at 10000; use a soft anchor in [9980, 10010].
- Treat VE as a drift-aware MM with wall-mid fair value.
- TTE-index your vol smile (skew + convexity drift across TTE).
- Exclude VEV_6000/VEV_6500 from scalping unless they start trading.
- Treat VEV_4000/VEV_4500 as +600 of synthetic VE capacity.
- Dead-band the delta hedge; never rebalance to zero.
- Run `parity_scan.py` on every new dataset before trading vouchers.
- Run `counterparty_scan.py` early to refresh the Mark roster and PnL ranks.
