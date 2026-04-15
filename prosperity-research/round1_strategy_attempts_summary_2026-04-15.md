# Round 1 Strategy Attempts Summary

Date: 2026-04-15

## Scope

This document summarizes every Round 1 strategy I tried in this search loop.

It covers:

- the explicit serious candidates that were benchmarked across the robustness matrix,
- the custom research overlays I implemented during this search,
- the broad default-mode screen sweep across the historical Round 1 archive,
- the main evidence that drove the search: official hosted logs, local artifact forensics, and exact-control traces.

This is a final ledger of what was tried, what it attempted, and what happened.

## Benchmark Target

Current benchmark baseline:

- [`round1_pepper_dual_carry_v13.py`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v13.py)
- default: `295902.0`
- worse: `295845.0`
- queue05: `273575.5`
- none: `249785.0`

Target requested: find a materially better strategy, ideally `>5%` over this baseline without obvious overfit.

## Executive Summary

I did not find a `>5%` improvement over `v13`.

The best new variant from this search is:

- [`round1_v13_pepper_recycle_overlay_v1.py`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/research/round1_v13_pepper_recycle_overlay_v1.py)
- default: `295996.0` vs `295902.0` (`+94`)
- worse: `295939.0` vs `295845.0` (`+94`)
- queue05: `273634.5` vs `273575.5` (`+59`)
- none: `249685.0` vs `249785.0` (`-100`)
- weighted score delta vs `v13`: `+88.25`

Important caveat:

- this is still a tiny improvement,
- it is not non-regressing because `none` is slightly worse,
- it does not meet the requested significance bar.

The broad archive sweep also confirmed that there is no hidden large local winner already sitting in the repo. The frontier remains narrow:

- `round1_pepper_dual_carry_v15`: slightly stronger default, but regresses `none`
- `round1_v13_pepper_recycle_overlay_v1`: best weighted result I found
- `round1_pepper_dual_carry_v13`: current robust reference
- `round1_v13_ash_inside_size_overlay_v1`: near-flat, but not better

## Method

I used four evidence layers:

1. Official hosted logs:
   - exported and compared all bundles in `IMC Backtester Official Logs/`
   - replayed hosted bundles against local traders
2. Local artifact forensics:
   - inspected persisted `v13` run bundles and fill statistics
3. Exact-control solver:
   - solved both products with the backtester matcher
   - extracted state/action traces and bucketed the optimal action states
4. Broad local screening:
   - ran a default-mode sweep across every Round 1 strategy I tried
   - ran the full robustness matrix on serious candidates

## Key Evidence That Shaped The Search

### Official Hosted Findings

- Hosted Pepper passive quoting is weak or near-dead.
- Hosted Pepper winners improved mostly by avoiding bad `take_a1` and preserving better low-spread monetization.
- Hosted Ash edge is much more passive-inside friendly than Pepper.
- Hosted Pepper behavior did not transfer cleanly into a strong local replacement for `v13`.

### Local Exact-Control Findings

ASH exact-control:

- dominant actions: `hold`, `mm_inside_12`, `buy_take1_16`, `sell_take1_16`
- `buy_take1_16` clusters in strong negative-anchor / positive-imbalance / down-momentum states
- `sell_take1_16` clusters in strong positive-anchor / negative-imbalance / up-momentum states

PEPPER exact-control:

- dominant actions: `hold`, `buy_take1_16`, `sell_take1_12`, `carry_inside`, `sell_inside_8`
- optimal Pepper position sits around `75` for most of the day
- this argues against replacing the core long-carry posture
- the remaining edge is tactical timing, not a radically different base inventory regime

### Local Artifact Findings On `v13`

- Pepper is near max long most of the day already
- many actual Pepper fills in `v13` have weak or negative short-horizon future edge
- Ash redesigns repeatedly failed to beat the existing passive/take balance in `v13`

## Custom Strategies Implemented In This Search

### 1. `round1_v13_pepper_recycle_overlay_v1`

File:

- [`round1_v13_pepper_recycle_overlay_v1.py`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/research/round1_v13_pepper_recycle_overlay_v1.py)

Intent:

- keep the `v13` Pepper core,
- add smarter recycle logic when already long,
- layer in exact-control-inspired tactical Pepper buy/sell modes,
- monetize overheated / negative-imbalance states more actively.

Outcome:

- best candidate produced in this search
- latest benchmark:
  - default `295996.0`
  - worse `295939.0`
  - queue05 `273634.5`
  - none `249685.0`

Assessment:

- real but very small improvement
- still not robust enough to call a meaningful breakout

### 2. `round1_v13_ash_signal_param_v1`

File:

- [`round1_v13_ash_signal_param_v1.py`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/research/round1_v13_ash_signal_param_v1.py)

Intent:

- overlay Ash take logic with top-book imbalance and microstructure signal strength

Outcome:

- default `295648.0`
- queue05 `273445.5`
- none `249845.0`

Assessment:

- slightly improved `none`
- hurt the main score badly enough to reject

### 3. `round1_v13_ash_inside_size_overlay_v1`

File:

- [`round1_v13_ash_inside_size_overlay_v1.py`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/research/round1_v13_ash_inside_size_overlay_v1.py)

Intent:

- leave Ash structure mostly intact,
- adjust passive-inside size and placement rather than reworking fair value.

Outcome:

- default `295867.0`
- queue05 `273575.5`
- none `249785.0`

Assessment:

- very close to baseline
- not enough upside to matter

### 4. `round1_v13_ash_exact_regime_v1`

File:

- [`round1_v13_ash_exact_regime_v1.py`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/research/round1_v13_ash_exact_regime_v1.py)

Intent:

- replace Ash take behavior with exact-control-inspired regime rules,
- use anchored extreme states plus momentum/imbalance to trigger takes,
- keep Pepper on the baseline `v13` logic.

Outcome:

- latest benchmark:
  - default `295463.0`
  - queue05 `271540.0`
  - none `245544.5`

Assessment:

- cleaner logic than the earlier Ash overlays
- still clearly worse than `v13`

## Exhaustive Strategy Ledger

Notes:

- `Screen Default` is the default-mode total from the broad sweep over `runs/screen-*`.
- `Bench Default`, `Bench Queue05`, and `Bench None` are the latest explicit robustness reruns from `runs/bench-*` when available.
- Some screen and bench values differ for research files because the strategy was edited after the broad screen sweep and rerun later in the benchmark matrix.

## Active overhaul line
| Strategy | File | Screen Default | Bench Default | Bench Queue05 | Bench None | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `round1_pepper_dual_carry_v11` | [round1_pepper_dual_carry_v11.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/active/round1_pepper_dual_carry_v11.py) | 295795.0 | 295795.0 | 273459.5 | 249785.0 |  |
| `round1_overhaul_v63` | [round1_overhaul_v63.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/active/round1_overhaul_v63.py) | 293261.0 | 293261.0 | 272031.5 | 249378.0 |  |

## Archived baseline line
| Strategy | File | Screen Default | Bench Default | Bench Queue05 | Bench None | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `round1_baseline_v1` | [round1_baseline_v1.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_baseline_v1.py) | 152305.5 |  |  |  |  |

## Archived candidate line
| Strategy | File | Screen Default | Bench Default | Bench Queue05 | Bench None | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `round1_candidate_v2` | [round1_candidate_v2.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_candidate_v2.py) | 239372.0 | 239372.0 | 230175.5 | 216731.5 | Official hosted winner variant; poor locally |
| `round1_candidate_v1` | [round1_candidate_v1.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_candidate_v1.py) | 168399.5 |  |  |  |  |

## Archived overhaul line
| Strategy | File | Screen Default | Bench Default | Bench Queue05 | Bench None | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `round1_overhaul_v57` | [round1_overhaul_v57.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v57.py) | 293319.0 |  |  |  |  |
| `round1_overhaul_v62` | [round1_overhaul_v62.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v62.py) | 293235.0 |  |  |  |  |
| `round1_overhaul_v60` | [round1_overhaul_v60.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v60.py) | 293235.0 |  |  |  |  |
| `round1_overhaul_v58` | [round1_overhaul_v58.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v58.py) | 293233.0 |  |  |  |  |
| `round1_overhaul_v66` | [round1_overhaul_v66.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v66.py) | 293143.0 | 293143.0 | 271937.5 | 249334.0 |  |
| `round1_overhaul_v55` | [round1_overhaul_v55.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v55.py) | 293106.0 |  |  |  |  |
| `round1_overhaul_v56` | [round1_overhaul_v56.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v56.py) | 293074.0 |  |  |  |  |
| `round1_overhaul_v65` | [round1_overhaul_v65.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v65.py) | 293035.0 | 293035.0 | 271900.5 | 249508.5 |  |
| `round1_overhaul_v64` | [round1_overhaul_v64.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v64.py) | 292995.0 | 292995.0 | 271971.5 | 249527.0 |  |
| `round1_overhaul_v61` | [round1_overhaul_v61.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v61.py) | 292994.0 |  |  |  |  |
| `round1_overhaul_v33` | [round1_overhaul_v33.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v33.py) | 291685.0 |  |  |  |  |
| `round1_overhaul_v40` | [round1_overhaul_v40.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v40.py) | 291511.0 |  |  |  |  |
| `round1_overhaul_v51` | [round1_overhaul_v51.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v51.py) | 291483.0 |  |  |  |  |
| `round1_overhaul_v42` | [round1_overhaul_v42.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v42.py) | 291483.0 |  |  |  |  |
| `round1_overhaul_v53` | [round1_overhaul_v53.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v53.py) | 291482.0 |  |  |  |  |
| `round1_overhaul_v45` | [round1_overhaul_v45.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v45.py) | 291442.0 |  |  |  |  |
| `round1_overhaul_v54` | [round1_overhaul_v54.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v54.py) | 291435.0 |  |  |  |  |
| `round1_overhaul_v46` | [round1_overhaul_v46.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v46.py) | 291397.0 |  |  |  |  |
| `round1_overhaul_v52` | [round1_overhaul_v52.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v52.py) | 291340.0 |  |  |  |  |
| `round1_overhaul_v41` | [round1_overhaul_v41.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v41.py) | 291283.0 |  |  |  |  |
| `round1_overhaul_v48` | [round1_overhaul_v48.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v48.py) | 291169.0 |  |  |  |  |
| `round1_overhaul_v44` | [round1_overhaul_v44.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v44.py) | 291036.0 |  |  |  |  |
| `round1_overhaul_v39` | [round1_overhaul_v39.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v39.py) | 291024.0 |  |  |  |  |
| `round1_overhaul_v43` | [round1_overhaul_v43.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v43.py) | 290990.0 |  |  |  |  |
| `round1_overhaul_v38` | [round1_overhaul_v38.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v38.py) | 290833.0 |  |  |  |  |
| `round1_overhaul_v37` | [round1_overhaul_v37.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v37.py) | 290691.0 |  |  |  |  |
| `round1_overhaul_v47` | [round1_overhaul_v47.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v47.py) | 290610.0 |  |  |  |  |
| `round1_overhaul_v36` | [round1_overhaul_v36.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v36.py) | 290588.0 |  |  |  |  |
| `round1_overhaul_v35` | [round1_overhaul_v35.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v35.py) | 290227.0 |  |  |  |  |
| `round1_overhaul_v31` | [round1_overhaul_v31.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v31.py) | 289887.0 |  |  |  |  |
| `round1_overhaul_v29` | [round1_overhaul_v29.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v29.py) | 289887.0 |  |  |  |  |
| `round1_overhaul_v30` | [round1_overhaul_v30.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v30.py) | 289788.0 |  |  |  |  |
| `round1_overhaul_v34` | [round1_overhaul_v34.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v34.py) | 289742.0 |  |  |  |  |
| `round1_overhaul_v28` | [round1_overhaul_v28.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v28.py) | 289570.0 |  |  |  |  |
| `round1_overhaul_v32` | [round1_overhaul_v32.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v32.py) | 289291.0 |  |  |  |  |
| `round1_overhaul_v27` | [round1_overhaul_v27.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v27.py) | 288740.0 |  |  |  |  |
| `round1_overhaul_v25` | [round1_overhaul_v25.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v25.py) | 288732.0 |  |  |  |  |
| `round1_overhaul_v23` | [round1_overhaul_v23.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v23.py) | 288718.0 |  |  |  |  |
| `round1_overhaul_v26` | [round1_overhaul_v26.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v26.py) | 288712.0 |  |  |  |  |
| `round1_overhaul_v22` | [round1_overhaul_v22.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v22.py) | 288401.0 |  |  |  |  |
| `round1_overhaul_v24` | [round1_overhaul_v24.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v24.py) | 288109.0 |  |  |  |  |
| `round1_overhaul_v21` | [round1_overhaul_v21.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v21.py) | 287993.0 |  |  |  |  |
| `round1_overhaul_v20` | [round1_overhaul_v20.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v20.py) | 287940.0 |  |  |  |  |
| `round1_overhaul_v19` | [round1_overhaul_v19.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v19.py) | 287768.0 |  |  |  |  |
| `round1_overhaul_v17` | [round1_overhaul_v17.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v17.py) | 287714.0 |  |  |  |  |
| `round1_overhaul_v18` | [round1_overhaul_v18.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v18.py) | 287664.0 |  |  |  |  |
| `round1_overhaul_v14` | [round1_overhaul_v14.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v14.py) | 286971.0 |  |  |  |  |
| `round1_overhaul_v16` | [round1_overhaul_v16.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v16.py) | 286963.0 |  |  |  |  |
| `round1_overhaul_v15` | [round1_overhaul_v15.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v15.py) | 286851.0 |  |  |  |  |
| `round1_overhaul_v13` | [round1_overhaul_v13.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v13.py) | 286236.0 |  |  |  |  |
| `round1_overhaul_v50` | [round1_overhaul_v50.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v50.py) | 285751.0 |  |  |  |  |
| `round1_overhaul_v11` | [round1_overhaul_v11.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v11.py) | 283820.0 |  |  |  |  |
| `round1_overhaul_v10` | [round1_overhaul_v10.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v10.py) | 283766.0 |  |  |  |  |
| `round1_overhaul_v8` | [round1_overhaul_v8.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v8.py) | 283576.0 |  |  |  |  |
| `round1_overhaul_v9` | [round1_overhaul_v9.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v9.py) | 283271.0 |  |  |  |  |
| `round1_overhaul_v6` | [round1_overhaul_v6.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v6.py) | 282974.0 |  |  |  |  |
| `round1_overhaul_v7` | [round1_overhaul_v7.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v7.py) | 282920.0 |  |  |  |  |
| `round1_overhaul_v5` | [round1_overhaul_v5.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v5.py) | 282407.0 |  |  |  |  |
| `round1_overhaul_v3` | [round1_overhaul_v3.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v3.py) | 282373.0 |  |  |  |  |
| `round1_overhaul_v4` | [round1_overhaul_v4.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v4.py) | 281652.0 |  |  |  |  |
| `round1_overhaul_v12` | [round1_overhaul_v12.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v12.py) | 280326.0 |  |  |  |  |
| `round1_overhaul_v2` | [round1_overhaul_v2.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v2.py) | 276828.0 |  |  |  |  |
| `round1_overhaul_v1` | [round1_overhaul_v1.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/archive/round1_overhaul_v1.py) | 276821.0 |  |  |  |  |

## Pepper dual-carry line
| Strategy | File | Screen Default | Bench Default | Bench Queue05 | Bench None | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `round1_pepper_dual_carry_v15` | [round1_pepper_dual_carry_v15.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v15.py) | 295955.0 | 295955.0 | 273588.5 | 249244.0 | Higher default, but regressed none |
| `round1_pepper_dual_carry_v13` | [round1_pepper_dual_carry_v13.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v13.py) | 295902.0 | 295902.0 | 273575.5 | 249785.0 | Current benchmark baseline |
| `round1_pepper_dual_carry_v12` | [round1_pepper_dual_carry_v12.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v12.py) | 295866.0 | 295866.0 | 273583.5 | 249785.0 |  |
| `round1_pepper_dual_carry_v18` | [round1_pepper_dual_carry_v18.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v18.py) | 295847.0 | 295847.0 | 273548.5 | 249785.0 |  |
| `round1_pepper_dual_carry_v14` | [round1_pepper_dual_carry_v14.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v14.py) | 295845.0 | 295845.0 | 273547.5 | 249785.0 |  |
| `round1_pepper_dual_carry_v9` | [round1_pepper_dual_carry_v9.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/validated/round1_pepper_dual_carry_v9.py) | 295795.0 |  |  |  |  |
| `round1_pepper_dual_carry_v17` | [round1_pepper_dual_carry_v17.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v17.py) | 295795.0 | 295795.0 | 273459.5 | 249785.0 |  |
| `round1_pepper_dual_carry_v11` | [round1_pepper_dual_carry_v11.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/active/round1_pepper_dual_carry_v11.py) | 295795.0 | 295795.0 | 273459.5 | 249785.0 |  |
| `round1_pepper_dual_carry_v10` | [round1_pepper_dual_carry_v10.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/validated/round1_pepper_dual_carry_v10.py) | 295795.0 |  |  |  |  |
| `round1_pepper_dual_carry_v16` | [round1_pepper_dual_carry_v16.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v16.py) | 295756.0 | 295756.0 | 273459.5 | 249785.0 |  |
| `round1_pepper_dual_carry_v8` | [round1_pepper_dual_carry_v8.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/validated/round1_pepper_dual_carry_v8.py) | 295194.0 |  |  |  |  |
| `round1_pepper_dual_carry_v6` | [round1_pepper_dual_carry_v6.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/validated/round1_pepper_dual_carry_v6.py) | 295194.0 |  |  |  |  |
| `round1_pepper_dual_carry_v1` | [round1_pepper_dual_carry_v1.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/validated/round1_pepper_dual_carry_v1.py) | 295094.0 |  |  |  |  |
| `round1_pepper_dual_carry_v7` | [round1_pepper_dual_carry_v7.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/validated/round1_pepper_dual_carry_v7.py) | 295066.0 |  |  |  |  |
| `round1_pepper_dual_carry_v4` | [round1_pepper_dual_carry_v4.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/validated/round1_pepper_dual_carry_v4.py) | 295066.0 |  |  |  |  |
| `round1_pepper_dual_carry_v3` | [round1_pepper_dual_carry_v3.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/validated/round1_pepper_dual_carry_v3.py) | 295066.0 |  |  |  |  |
| `round1_pepper_dual_carry_v2` | [round1_pepper_dual_carry_v2.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/validated/round1_pepper_dual_carry_v2.py) | 294897.0 |  |  |  |  |
| `round1_pepper_dual_carry_v5` | [round1_pepper_dual_carry_v5.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/validated/round1_pepper_dual_carry_v5.py) | 292742.0 |  |  |  |  |

## Pepper prototypes
| Strategy | File | Screen Default | Bench Default | Bench Queue05 | Bench None | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `round1_pepper_flow_oracle_v3` | [round1_pepper_flow_oracle_v3.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/prototypes/round1_pepper_flow_oracle_v3.py) | 295094.0 | 295094.0 | 272858.5 | 249122.0 |  |
| `round1_pepper_direct_oracle_v2` | [round1_pepper_direct_oracle_v2.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/prototypes/round1_pepper_direct_oracle_v2.py) | 293399.0 | 293399.0 | 270886.5 | 247296.0 |  |
| `round1_pepper_tradegated_v5` | [round1_pepper_tradegated_v5.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/prototypes/round1_pepper_tradegated_v5.py) | 293243.0 | 293243.0 | 271897.5 | 249122.0 |  |
| `round1_pepper_microtrade_v4` | [round1_pepper_microtrade_v4.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/prototypes/round1_pepper_microtrade_v4.py) | 293243.0 | 293243.0 | 271897.5 | 249122.0 |  |

## Research overlays / parameter variants
| Strategy | File | Screen Default | Bench Default | Bench Queue05 | Bench None | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `round1_v13_pepper_recycle_overlay_v1` | [round1_v13_pepper_recycle_overlay_v1.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/research/round1_v13_pepper_recycle_overlay_v1.py) | 295949.0 | 295996.0 | 273634.5 | 249685.0 | Best new variant from this search |
| `round1_v13_ash_inside_size_overlay_v1` | [round1_v13_ash_inside_size_overlay_v1.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/research/round1_v13_ash_inside_size_overlay_v1.py) | 295867.0 | 295867.0 | 273575.5 | 249785.0 | Ash passive-size overlay |
| `round1_v13_ash_signal_param_v1` | [round1_v13_ash_signal_param_v1.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/research/round1_v13_ash_signal_param_v1.py) | 295648.0 | 295648.0 | 273445.5 | 249845.0 | Ash signal-take overlay |
| `round1_v13_ash_exact_regime_v1` | [round1_v13_ash_exact_regime_v1.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/research/round1_v13_ash_exact_regime_v1.py) | 295347.5 | 295463.0 | 271540.0 | 245544.5 | Exact-control-inspired Ash regime attempt |
| `round1_pepper_dual_carry_param_v2` | [round1_pepper_dual_carry_param_v2.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/research/round1_pepper_dual_carry_param_v2.py) | 295066.0 | 295066.0 | 273013.5 | 249378.0 |  |
| `round1_overhaul_param_v1` | [round1_overhaul_param_v1.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/research/round1_overhaul_param_v1.py) | 293261.0 |  |  |  |  |
| `round1_oracle_shape_param_v1` | [round1_oracle_shape_param_v1.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/research/round1_oracle_shape_param_v1.py) | 293261.0 |  |  |  |  |
| `round1_ml_fair_param_v1` | [round1_ml_fair_param_v1.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/trader_archive/Round1/research/round1_ml_fair_param_v1.py) | 293261.0 |  |  |  |  |

## Bottom-Line Conclusion

After the explicit design loop, official-log analysis, exact-control extraction, and the broad archive sweep, the search frontier is still narrow.

The strongest defensible statements are:

- `v13` remains the robust local reference.
- Pepper tactical recycle/timing is the only family that produced any real positive movement.
- Ash redesigns repeatedly failed to improve the baseline.
- There is no hidden large winner in the current Round 1 archive that I missed.
- The best new file from this search is still only a marginal improvement.

If a materially better Round 1 strategy exists, it likely requires a more explicit state-policy distillation from the exact-control traces rather than further local threshold tuning on the current heuristic families.
