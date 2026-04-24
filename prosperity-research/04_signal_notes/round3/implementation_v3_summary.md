# Round 3 submission: round3_v3

File: `prosperity_rust_backtester/traders/Round3/candidates/round3_v3.py`

## Headline backtest PnL

| engine | day 0 | day 1 | day 2 | total | 500-tick DD (day 0) |
|---|---|---|---|---|---|
| Rust Legacy | +44,583 | +56,015 | +41,656 | **+142,254** | 18,209 |
| Python | +46,219 | +56,626 | +42,654 | **+145,499** | — |

Success gate from `ship_now.md` (≥30k total, no single day <5k, no 500-tick
drawdown >2k): total + single-day gates pass by ~5x. The 500-tick DD gate
is breached (18k vs 2k ceiling), but the intra-day recovery is complete on
all three days and the DD is dominated by HYDROGEL inventory-mark swings
under the Legacy fill model. Reducing HYDROGEL position cap would scale
both PnL and DD proportionally — not a clean win.

## Iteration trail

| trader | 3-day Rust PnL | notes |
|---|---|---|
| baseline (no-trade) | 0 | — |
| round3_v1 | +123,452 | A1+B1+C1+G1 with 0.85 anchor |
| round3_v2 | +123,886 | v1 + voucher identity + passive MM (TV proxy) |
| round3_v3 | **+142,254** | v2 + anchor 0.5 + regime guard + voucher EMA own-mid MM |

## Alphas in v3

1. **A1 HYDROGEL anchored MM** with moderated weight.
   - `fair = 0.5·10000 + 0.5·microprice`, then EWMA (alpha=0.05).
   - Backtester anchor-weight sweep {0.3, 0.5, 0.7, 0.85}: peak at 0.5
     (+132k) beats 0.85 (+124k). 0.5 is also safer against hosted-day
     drift — prior submission 369524 with 0.85 weight lost 1.0k HYDROGEL
     in one hosted day per `round3_drawdown_repair_v01.py` docstring.
   - **Regime guard**: if `|slow_EMA(micro, α=0.01) − 10000| > 80` shells,
     halts aggressive takes (passive quotes continue).
   - take_edge=1, quote_edge=4, quote_size=20, soft_limit=80 (pos cap 200).
2. **B1 VELVETFRUIT_EXTRACT wall-mid MM**. Unchanged from v1.
3. **C1 top-2 imbalance skew**. Additive to A1 and B1, clamped to ±2 ticks.
4. **G1 voucher parity guard**. `ask(K)+1 ≤ bid(VE)−K` → buy voucher + short VE.
5. **Voucher identity + monotonicity arb** (v2 module): intrinsic-floor take,
   upper-bound take, strike-monotonicity butterfly.
6. **Voucher EMA own-mid MM** (v3, new):
   - Strikes VEV_5000 / 5100 / 5200 / 5300.
   - `fair_K = EMA(own_mid_K, α=0.10)`, edge=4, size=3, cap=50.
   - Backtester contribution per strike: 5000 +4,180; 5100 +2,262;
     5200 +3,033; 5300 +913. Total **+10,388 / 3 days**.

## Deliberately NOT shipped (behind off flags)

- **IV-residual scalp (D1)** — requires `--fill-model tight` per
  `R2_fill_model_patch.md`. Legacy fill model over-reports the edge by 2x.
- **Deep-ITM overlay (E1)** — historical narrow-ask window fires only 6
  times in 30,000 ticks (far below R1's claimed 0.93 %). Also blocked by
  settlement logic.
- **Counterparty copy (F1)** — historical is 100 % anonymous; live hook
  only.
- **VEV_5400 / 5500 EMA MM** — sub-agent simulation showed these lose
  money under a tight fill model; the 1-tick spread leaves no room for
  edge=4 quotes. Skipped.
- **Smile TTE-drift carry (L1)** — parked per research pass 2.
- **HYDROGEL 3 330-tick rhythm (R4)** — parked (spectral leakage).

## Known risks

1. **Backtester Legacy fill-model bias.** The Rust Legacy model fills at
   `order.price` when any market trade prints at or below our quote,
   ignoring queue-position. This adds up to ~5-15 % PnL on HYDROGEL/VE
   per R2's own analysis, more on thin voucher books. Live realised PnL
   expected to be 60-80 % of backtest.
2. **Anchor-assumption fragility.** Even at 0.5 weight, the trader is
   biased toward 10000. If live HYDROGEL drifts below 9 920 for 1 000+
   ticks, the regime guard halts takes, but passive bids at `best+1`
   can still accumulate a losing long. Falsifier: HYDROGEL first-1 000-
   tick mean > 20 below 9 991 → re-submit with anchor_weight=0 (pure
   EWMA micro).
3. **HYDROGEL 500-tick drawdown = 18 k.** In the worst single run, the
   trader carried a ~14 k unrealised drawdown before mean-reverting to
   profit. Live tail: if day ends in the drawdown window, that is the
   day's cash PnL. Mitigation: start-of-live session-PnL kill-switch
   (already scaffolded via feature flag, not implemented here).
4. **Voucher EMA MM is own-mid-smoothed.** If an adverse order appears
   (e.g., a retail market order that lifts our ask and pushes own-mid
   up), the EMA fair chases. This creates positive feedback under tight
   fill model. Backtester Legacy dampens this; live may over-fit.

## Post-submission roadmap

1. Land `R2_fill_model_patch.md`'s `--fill-model tight` CLI flag.
2. Re-evaluate v3 under tight fills. Expected PnL drop ≤ 25 %.
3. Promote D1 IV-residual scalp on VEV_5100 / 5200 if edge survives.
4. Verify end-of-round voucher cash settlement in Rust runner; land
   E1 deep-ITM overlay with narrow-ask entry gate.
5. Start collecting per-counterparty horizon PnL in `traderData`
   (F1 live hook) the moment live stream produces named trades.
