# Round 1 Ash Signal Ranking

Date: 2026-04-16

Scope: `ASH_COATED_OSMIUM` only. This memo re-derives the Ash edge from the current `v29` baseline code, the hosted `177116` official log bundle, the local Round 1 datasets, and local `v29` run artifacts. It does not assume earlier Ash notes were correct.

## Official And Source Boundaries

### Verified official facts

Verified in [current_assumptions.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/01_assumptions/current_assumptions.md):

- Round 1 products are `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`.
- Both Round 1 position limits are `80`.
- The submission interface is `Trader.run(self, state)` returning `(result, conversions, traderData)`.
- `bid()` is not used for Round 1 continuous trading.
- Order-limit enforcement is worst-case per side.

### Direct evidence used here

- Baseline trader: [round1_pepper_dual_carry_v29.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py)
- Hosted execution trace: [177116.log](/Users/tahakhan/Documents/Work/Projects/Prosperity/IMC Backtester Official Logs/177116/177116.log)
- Hosted trader file: [177116.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/IMC Backtester Official Logs/177116/177116.py)
- Hosted summary: [177116.json](/Users/tahakhan/Documents/Work/Projects/Prosperity/IMC Backtester Official Logs/177116/177116.json)
- Local Round 1 data:
  - [prices_round_1_day_-2.csv](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/datasets/round1/prices_round_1_day_-2.csv)
  - [prices_round_1_day_-1.csv](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/datasets/round1/prices_round_1_day_-1.csv)
  - [prices_round_1_day_0.csv](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/datasets/round1/prices_round_1_day_0.csv)
  - matching `trades_round_1_day_*.csv`
- Local persisted reference run: [persist-v29-default-20260416](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/runs/persist-v29-default-20260416)

### Important fact about the hosted bundle

`177116.py` is byte-for-byte identical to local `round1_pepper_dual_carry_v29.py`. So the hosted `177116` Ash trace is an official execution trace for the exact local `v29` baseline Ash logic.

## Baseline Ash Read

### What `v29` is actually doing

The Ash sleeve in `v29` is:

- anchored around `10000`,
- blended with always-on dynamic fair drift from `mm10_mid`, `wall_mid`, `microprice`, and `ret1`,
- one passive layer only,
- symmetric inside-quote preference when spread is wide enough,
- limited aggressive taking and limited recycler logic.

Inferred diagnosis from code alone:

- it is not a pure anchor maker,
- it is not a pure directional follower,
- it is a blended anchored-maker with mild tactical drift.

The rest of this memo tests whether that blend matches the data.

## Evidence Summary By Hypothesis

## 1. Neutral anchor around `10000`

### Evidence

Across the full local Round 1 bundle, simple-mid deviation from `10000` has stable mean-reverting power at 10 ticks:

- `corr(anchor_dev, future_mid_10 - mid) = -0.215`
- cheap large-deviation states (`mid <= 9996`) had positive 10-tick drift on all three days:
  - day `-2`: `+0.429`
  - day `-1`: `+1.044`
  - day `0`: `+0.655`
- rich large-deviation states (`mid >= 10004`) had negative 10-tick drift on all three days:
  - day `-2`: `-0.573`
  - day `-1`: `-0.704`
  - day `0`: `-0.515`

### Inference

The neutral anchor is real and robust. It should remain the base Ash market hypothesis. But it is not the strongest standalone alpha in the data.

## 2. Short-horizon mean reversion

### Evidence

One-step Ash returns are strongly mean-reverting:

- `corr(ret1, future_mid_10 - mid) = -0.415`
- `corr(ret1, future_mid_5 - mid) = -0.441`

Large one-step moves are especially strong:

- `ret1 <= -3`:
  - day `-2`: `+2.200` future 10-tick drift
  - day `-1`: `+2.364`
  - day `0`: `+2.370`
- `ret1 >= +3`:
  - day `-2`: `-1.912`
  - day `-1`: `-1.766`
  - day `0`: `-1.830`

### Inference

This is a stronger and cleaner edge than raw anchor deviation. Ash is not just “anchored around 10000.” It is also a fast mean-reverter around that anchor.

## 3. Post-spike reversion

### Evidence

Multi-tick spikes mean-revert even more cleanly:

- `ret3 <= -4` had about `+2.82` average 10-tick drift
- `ret3 >= +4` had about `-2.13` average 10-tick drift

This was not a one-day accident. The one-step spike-fade states above stayed strong on all three local days.

### Inference

Post-spike fade is a first-tier Ash alpha. It deserves an explicit regime, not just a small continuous fair adjustment.

## 4. Microprice / best-level imbalance

### Evidence

Best-level pressure is real:

- `corr(micro_bias, future_mid_10 - mid) = +0.439`
- `corr(level1_imbalance, future_mid_10 - mid) = +0.518`

Per-day 10-tick drift:

- `micro_up` states:
  - day `-2`: `+1.883`
  - day `-1`: `+1.813`
  - day `0`: `+1.829`
- `micro_down` states:
  - day `-2`: `-1.766`
  - day `-1`: `-1.814`
  - day `0`: `-1.755`

### Inference

Microprice and best-level imbalance have real short-horizon predictive value. But they should be treated as tactical state or regime confirmation, not as permission for an always-on directional fair drift.

## 5. Persistence or non-persistence of directional pressure

### Evidence

The strongest states are not “pressure only” states. They are mixed states where recent move and current pressure define the regime:

- `ret1 <= -2` and `micro_bias >= +0.5`:
  - normal spread: `+4.081` average 10-tick drift
  - wide spread: `+1.237`
- `ret1 >= +2` and `micro_bias <= -0.5`:
  - normal spread: `-3.541`
  - wide spread: `-1.212`

Flat wide states with pressure also have signal, but smaller:

- wide, flat, `micro_up`: `+1.165`
- wide, flat, `micro_down`: `-1.214`

### Inference

Pressure is persistent enough to matter, but the best Ash use is regime-specific:

- spike-fade with pressure confirmation,
- or wide passive quoting with pressure-aware side preference.

This argues against a permanent blended directional tilt.

## 6. Spread-regime effects

### Evidence

Wide spread is common:

- average spread across the local Round 1 bundle: `16.18`
- share with spread `>= 18`: `27.6%`

But wide spread alone is not directional:

- official day `0` wide-state future 10-tick drift: only `+0.050`

What wide spread does improve is passive economics:

- official `177116` Ash trades:
  - passive average 10-tick markout: `+6.875`
  - aggressive average 10-tick markout: `+1.540`
  - wide-trade average 10-tick markout: `+7.808`
  - narrow-trade average 10-tick markout: `+4.617`

### Inference

Wide spread is an execution regime, not a directional alpha by itself. The money is in better passive capture and better side selection, not in blindly following wide-spread moves.

## 7. Inventory drag vs turnover

### Evidence

Official `177116` Ash finished at `3205.5` PnL with only `89` own Ash trades and a max Ash position of `66`.

The position path was asymmetric:

- time with Ash position `>= +20`: `31700`
- time with Ash position `<= -20`: `13600`
- time with Ash position `>= +40`: `16300`
- time with Ash position `<= -40`: `0`

Sell execution while already long was weak:

- official flat-state sells: `+5.194` average 10-tick markout
- official sells while already `+20` or more: `+1.583`

By contrast, buy-side markouts did not degrade as severely.

### Inference

The hosted `v29` Ash trace carries long inventory too comfortably and monetizes rich / sell-side states too weakly. Inventory drag is not the only issue, but it is real and asymmetric.

## 8. Multi-level taking opportunities

### Evidence

I explicitly tested aggressive taking markouts in spike-fade and wide-spread states by asking whether buying visible ask levels or selling visible bid levels had positive 10-tick markout.

Result:

- level-1 aggressive buys in spike-fade buy states were negative on average
- level-2 aggressive buys were even worse
- symmetric sell-side aggressive levels were also negative

### Inference

There is no strong evidence that the missed Ash money is “start sweeping deeper levels.” Multi-level taking looks weak and should rank low.

## 9. Second passive layer capture on wide spreads

### Evidence

If a second passive layer fills, its conditional markout is attractive:

- wide-spread passive level-1 buy markout: about `+9.36`
- wide-spread passive level-2 buy markout: about `+10.53`
- wide-spread passive level-1 sell markout: about `+9.36`
- wide-spread passive level-2 sell markout: about `+10.53`

But the fill proxy is tiny when checked against the Round 1 trade tape:

- wide-state second-bid fill proxy: about `0.47%`
- wide-state second-ask fill proxy: about `0.18%`

### Inference

A second passive layer is not dead, but it is not the main missing alpha. It is a secondary refinement with low expected fill frequency, not the first architecture change to prioritize.

## Official `v29` Capture Versus Raw Opportunity

## What `177116` captured well

### Evidence

- official Ash passive fills were good: `+6.875` average 10-tick markout
- official spike-fade buys were monetized reasonably well:
  - raw official-day spike-fade-buy states: `46` states, `+2.174` average 10-tick drift
  - official buys in those states: `9` fills, `+3.063` average 10-tick markout

### Inference

The buy-side fade logic is not the main failure.

## What `177116` under-captured

### Evidence

Sell-side fade and rich-state monetization were weaker:

- raw official-day spike-fade-sell states:
  - `52` states
  - `-2.740` average 10-tick drift
- official sells in those states:
  - `7` fills
  - only `+0.417` average 10-tick markout

Rich-side anchor states showed the same pattern:

- raw official-day rich-big states (`mid >= 10004`):
  - `28` states
  - `-3.571` average 10-tick drift
- official sells in those states:
  - `11` fills
  - only `+0.773` average 10-tick markout

### Inference

The likely missed alpha in `v29` is not “more generic Ash direction.” It is better explicit sell-side regime handling:

- stronger rich-state fade,
- earlier flatten-only selling when already long,
- pressure-confirmed spike-fade sells,
- less reliance on a single blended fair for those states.

## Ranked Ash Edges By Robustness

1. Short-horizon spike-fade / mean reversion.
2. Pressure-confirmed regime states using microprice or best-level imbalance.
3. Neutral anchor making around `10000`.
4. Wide-spread first-layer passive capture.
5. Earlier sell-side flatten / recycler behavior when long in rich states.
6. Second passive layer on wide spreads.
7. Multi-level aggressive taking.

## Bottom Line

### Evidence-backed conclusion

The current `v29` Ash sleeve is leaving money on the table, but not because it lacks a fair anchor. The stronger missed alpha is:

- explicit regime-specific spike fade,
- especially on the sell side,
- plus earlier long-inventory flattening in rich or pressure-down states.

The data does not support “Ash wants a stronger always-on directional fair.” It supports:

- anchored maker by default,
- pressure-aware gating,
- explicit spike-fade overrides,
- and stronger recycler behavior when already long.

### Recommended next Ash strategy direction

The strongest next Ash family to build is:

- keep the `10000` anchor-maker base,
- replace the current always-on blended directional drift with explicit regimes,
- add a sell-side fade / flatten mode for `ret1 up + micro_down` and rich-long states,
- keep multi-level taking low priority,
- keep second passive layer as a secondary experiment only after the regime split is tested.

## 2026-04-16 Follow-Up Update

### New evidence from Ash-only variants `v41` to `v46`

Additional local and hosted diagnostics after the role-driven Ash pass sharpened the ranking:

- Ash passive inside fills remain good on both surfaces.
- The cleanest still-open donor bucket is not passive inside participation itself.
- The cleanest donor bucket is medium-spread aggressive taking and recycler clearing.

### Medium-spread taker quality

From local `v29` persisted runs:

- `take_a1` is strong at spreads `5`, `6`, and `8`, weak at `9`, and clearly bad at `10` and `12`.
- `take_b1` is strong at spreads `6`, `7`, and `9`, and clearly bad at `10`, `11`, and `13`.

From hosted `177116`:

- `take_b1` at spread `10` is also negative.
- hosted narrow takers remain acceptable, which means the bad region is not “all takers,” but a specific spread-conditioned tactical state.

### What this changes

The signal ranking now becomes:

1. Narrow-spread taker / recycle states with real edge.
2. Post-spike fade with pressure confirmation.
3. Wide-spread passive inside capture.
4. Medium-spread taker suppression and recycler gating.
5. Microprice / imbalance as tactical confirmation.

### Family verdicts from `v41` to `v46`

- Medium-spread taker gating is real and transfer-shaped.
  - `v41`, `v42`, and `v44` all improved conservative modes.
- The family appears incremental rather than breakout.
  - best result `v44` improved Ash in all local modes, but only modestly.
- Anchor-extreme passive fade overlays without a richer state model were not enough.
  - `v45` and `v46` regressed `default`, `queue05`, and `worse`.
- Conservative fade-side second-layer quoting is not currently supported by evidence.
  - `v46` collapsed outside `none`, so the second-layer extension is not presently a credible transfer path.

### Updated bottleneck

The remaining Ash bottleneck is no longer “find another simple signal.” The remaining bottleneck is an action-state mapping gap:

- which medium-spread states should be `hold` instead of `take`,
- which rich / cheap states deserve passive one-sided leaning instead of symmetric quoting,
- and how to approximate those decisions without the current hand-built rules becoming too blunt.
