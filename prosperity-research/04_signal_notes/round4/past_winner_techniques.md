# Past-winner technique menu (Phase 5)

## Repos studied

- **TimoDiehm/imc-prosperity-3** (Frankfurt Hedgehogs, 2nd P3) — Wall-Mid + IV scalping with parabolic smile detrend, daily-extreme informed-trader detector.
- **chrispyroberts/imc-prosperity-3** (CMU Physics, 7th P3) — quadratic moneyness smile pivoted to **rolling mid-IV** as fair, z-score basket arb, no-hedge gamma.
- **CarterT27/imc-prosperity-3** (Alpha Animals, 9th P3) — Black-Scholes IV w/ rolling vol, rolling "good-trades" classifier per counterparty in R5.
- **jmerle/imc-prosperity-3** (camel_case, 25th P3) — open-source backtester/optimizer; gridsearched hyperparams; counterparty adjustments in R5.
- **ericcccsliu/imc-prosperity-2** (linear utility, 2nd P2) — MM-bot-mid as fair, modified rolling-stdev z-score, **DP optimal-trading algorithm** w/ position-limit state.

5 repos read in full. Optiver writeup deferred for word budget.

## Technique menu

| Technique | Source | What it does | Already in v15? | Hypothesis for R4 |
|---|---|---|---|---|
| Wall-Mid (deepest-level avg) | TimoDiehm; ericcccsliu | Avg of deep bid/ask walls | Yes (VFE) | n/a |
| Microprice (Stoikov size-weighted) | menu add | bid·ask_qty + ask·bid_qty | **No** | Better HYD anchor in unbalanced books |
| Quadratic moneyness smile | TimoDiehm; CMU | v(m)=am²+bm+c, m=ln(K/S)/√TTE | Yes | n/a |
| **Rolling mid-IV per strike** | CMU Physics R3 | Short rolling-mean of mid-IV beat quadratic on day 3 | Partial (static bias) | **Top gap.** Could double TTE-smile PnL |
| Daily-extreme insider detector | TimoDiehm; CarterT27 | Running daily min/max + size-15 | n/a (no Olivia) | Mark-14 follow replaces this |
| Online good-trade classifier | CarterT27 R5 | Rolling % profitable per counterparty | Partial | Online ID if Mark-14 changes |
| z-score w/ small rolling stdev | ericcccsliu; CMU | small σ inflates z near reversal | No | VEV residual ladder firing |
| DP optimal-trading planner | ericcccsliu R5 | Bellman over positions for forecast path | **No** | DP over voucher inventory if Mark-14 forecast holds |
| Spike-vol regime gate | CMU R1 | Halt MM when σ(Δp)>20, take opposite | No | Guard for HYD 100-tick anomalies |
| No-hedge / partial-delta | CMU R3 | Skip hedge when spread > delta-loss | Partial | Quantify spread vs delta-VaR |
| Aggressor-sign cumulant | menu add | Σ sign(trade) over window | **No** | Likely leads VFE AC1 |
| VPIN toxicity | menu add | Volume-bucketed buy/sell skew | No | Mark-14 active vs Marks 1/22 noise |
| HMM 2-state regime | menu add | Online trend/MR filter | No | Switch HYD MM ↔ momentum |
| Hawkes self-excitation | menu add | λ=μ+Σα·e^{-β(t-tᵢ)} on prints | No | Voucher print clusters near IV jumps |
| Lee-Mykland jump test | menu add | Threshold on \|r\|/σ_local | No | Post-jump drift on HYD |
| Avellaneda-Stoikov reservation MM | menu add | r=S−qγσ²(T−t) | No | TTE→0 voucher inventory penalty |
| Cross-day overnight gap | menu add | Close→open across days | No | TTE 5→4 step gap on fair IV |
| Per-strike volume imbalance | menu add | Δ(buy_q−sell_q)_K vs ΔIV_K | No | Pre-emptive smile shift |
| Calendar time-of-day buckets | menu add | Hour-bucket fixed effects | Tested, weak | Skip; confirmed not material |

## High-priority gaps (ranked)

1. **Per-strike rolling mid-IV as fair (replacing fixed quadratic + per-strike static bias on VEV_5000–5500).** CMU Physics' direct backtest showed the parabola broke on submission day while a short-window rolling mid-IV held; their PnL went 80k→200k. **Falsifier:** if `rolling_mid_iv_K(t)` does not lower per-strike residual MAE versus current TTE-fit on R4 day-3 data, abandon. Target: VEV_5000, 5100, 5200, 5300, 5400, 5500.

2. **Microprice fair value for HYDROGEL_PACK and VELVETFRUIT_EXTRACT.** v15 anchors HYD at clamp(EMA-200) and VFE at wall-mid. Microprice (Stoikov) uses size-weighting that approximates next-tick mid better when the book is unbalanced; AC1-fade slope on VFE ≈3 implies imbalance has live signal. **Falsifier:** microprice on R4 day-1/2/3 should beat raw-mid and EMA-200 in 1-tick forward-MSE on HYD by >5%; otherwise stay with EMA.

3. **Cumulative aggressor-sign signal scoped to Mark-14 vs Mark-38 prints.** Unique to R4: counterparty IDs let us compute a sign(trade)·1{trader∈{14}} − sign(trade)·1{trader∈{38}} cumulant. Combined with our existing top-2 imb skew (slope ~12 on HYD), this turns a passive MM into a directional MM. **Falsifier:** the rolling-sum signal must Granger-cause 5-tick-forward HYD mid-return on R4 day-3 with p<0.05; else it is noise dominated by Marks 1/22/55.
