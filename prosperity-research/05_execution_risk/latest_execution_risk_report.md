# Round 1 Ash Execution Risk Report

Date: 2026-04-16

Scope:
- role: `execution_risk`
- product: `ASH_COATED_OSMIUM` only
- local baseline trader: `prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py`
- hosted evidence bundle: `IMC Backtester Official Logs/177116/`

Evidence surface:
- official continuous-book facts were verified separately from the two official Round 1 context files
- hosted artifacts:
  - `IMC Backtester Official Logs/177116/177116.py`
  - `IMC Backtester Official Logs/177116/177116.log`
  - `IMC Backtester Official Logs/177116/177116.json`
- local persisted artifacts:
  - `prosperity_rust_backtester/runs/persist-v29-default-20260416/`
  - `prosperity_rust_backtester/runs/persist-v29-queue05-20260416-execrisk/`
  - `prosperity_rust_backtester/runs/persist-v29-none-20260416-execrisk/`

Commands used:
```bash
cd /Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester
./scripts/cargo_local.sh run -- --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --dataset round1 --run-id persist-v29-queue05-20260416-execrisk --output-root runs --persist --flat --products summary --trade-match-mode worse --queue-penetration 0.5
./scripts/cargo_local.sh run -- --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --dataset round1 --run-id persist-v29-none-20260416-execrisk --output-root runs --persist --flat --products summary --trade-match-mode none
```

## Observed Evidence

### 1. Hosted `177116` is the same Ash logic family as local `v29`

Observed from code:
- `177116.py` contains the same Ash constants and control structure as local `v29`:
  - `ASH_ANCHOR = 10000.0`
  - the same `ash_fair_and_state(...)` construction
  - `take_edge = 1.75 if not shock else 1.25`
  - `prefer_inside_buy = spread >= 15`
  - `prefer_inside_sell = spread >= 15`
  - `use_second_layer = False`

Interpretation:
- hosted `177116` is valid direct execution evidence for the Ash sleeve of the current baseline family, not just a loose historical analogy.

### 2. Hosted Ash result is positive but much smaller than local default

Hosted `177116` final PnL:
- total: `10655.5`
- `ASH_COATED_OSMIUM`: `3205.5`
- `INTARIAN_PEPPER_ROOT`: `7450.0`

Local `v29` Ash PnL:
- `default`: `55231.0`
- `worse + queue=0.5`: `34380.5`
- `none`: `13569.0`

Per-day local Ash PnL:
- `default`: `17948.0`, `19617.0`, `17666.0`
- `queue05`: `11366.0`, `12265.0`, `10749.5`
- `none`: `4784.0`, `4797.0`, `3988.0`

Interpretation:
- the local Ash edge is real under all tested modes
- the hosted result sits far closer to conservative local behavior than to local `default`

### 3. Maker/taker mix is directionally similar, but local passive value is overstated

| Surface | Ash PnL | Fill count | Maker qty | Taker qty | Avg abs pos | `|pos| >= 60` | `|pos| >= 70` | Max abs pos |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Hosted `177116` | `3205.5` | `89` | `318` | `157` | `22.30` | `1.9%` | `0.0%` | `66` |
| Local `default` | `55231.0` | `1943` | `5571` | `4320` | `40.68` | `35.5%` | `25.1%` | `80` |
| Local `queue05` | `34380.5` | `1913` | `2772` | `4205` | `40.63` | `37.6%` | `29.2%` | `80` |
| Local `none` | `13569.0` | `778` | `0` | `4116` | `40.85` | `37.9%` | `32.0%` | `80` |

Observed fill-spread context:
- hosted passive inside fills occur at average spread `16.77`
- hosted taker fills occur at average spread `6.42`
- local `default` passive inside fills occur at average spread `16.61`
- local `default` taker fills occur at average spread `7.62`

Interpretation:
- the spread regimes selected by the local strategy are not obviously wrong
- the local issue is not “filling in the wrong spread bucket”
- the bigger issue is that the local passive fills are worth much more than the hosted passive fills

### 4. Hosted and local taker quality are closely aligned at longer horizon

10-step post-fill markout per unit:

| Surface | Passive inside | Taker |
| --- | ---: | ---: |
| Hosted `177116` | `+7.09` | `+1.22` |
| Local `default` | `+16.51` | `+1.21` |
| Local `queue05` | `+14.75` | `+1.25` |
| Local `none` | n/a | `+1.24` |

1-step post-fill markout per unit:

| Surface | Passive inside | Taker |
| --- | ---: | ---: |
| Hosted `177116` | `+7.33` | `+1.89` |
| Local `default` | `+10.90` | `+22.15` |
| Local `queue05` | `+14.52` | `+22.76` |
| Local `none` | n/a | `+23.20` |

Interpretation:
- the Ash taker edge survives very well from local to hosted at the 10-step horizon
- the local short-horizon taker markout is much more flattering than hosted
- the local passive-inside edge is materially richer than hosted at every measured horizon

### 5. Inventory occupancy is the cleanest operational risk signal

Hosted `177116` Ash position path:
- final position: `+16`
- average absolute position: `22.30`
- time at `|pos| >= 60`: `1.9%`
- time at `|pos| >= 70`: `0.0%`
- max absolute position: `66`

Local `v29` Ash position path:
- aggregate average absolute position stays around `40.6` to `40.9` under all matching modes
- time at `|pos| >= 60` stays around `35.5%` to `37.9%`
- time at `|pos| >= 70` stays around `25.1%` to `32.0%`
- time at `|pos| = 80` remains material even under `none`
- end-of-day Ash positions are often still very large:
  - `default`: `-69`, `+51`, `+74`
  - `queue05`: `-75`, `+49`, `+77`
  - `none`: `-80`, `+29`, `+68`

Interpretation:
- local Ash inventory is sticky even when passive fills are removed
- the current recycler is too slow to reduce carried exposure under harsher fill assumptions

### 6. Raw drawdown from the persisted local PnL series is not decision-useful

Observed:
- the local `pnl_by_product` path for Ash swings by roughly `+0.8m / -0.8m` intraday before finishing around `+18k`
- hosted `profit_and_loss` is much smoother and ends near `+3205.5`

Interpretation:
- the raw local persisted PnL path appears to include inventory financing / cash-accounting conventions that are not directly comparable to the hosted reported PnL
- for Ash execution risk, inventory occupancy, fill class markouts, and conservative-mode degradation are more reliable than raw local drawdown magnitudes

## Inferred Risk Conclusions

### 1. The main transfer risk is passive-fill optimism, not absence of Ash alpha

Evidence:
- local `none` Ash PnL remains positive at `13569.0`
- local 10-step taker markout stays around `+1.21` to `+1.24` per unit
- hosted 10-step taker markout is `+1.22` per unit

Conclusion:
- the baseline has a real Ash taker / recycle edge
- the hosted shortfall is more likely caused by over-crediting local passive inside fills than by a totally wrong Ash market thesis

### 2. The recycler is too timid for transfer-robust Ash

Evidence:
- hosted `177116` almost never sits above `|pos| = 60`
- local `v29` spends roughly a third of time above `|pos| = 60` even in `none`
- local end-of-day Ash positions remain near the limit on multiple days

Conclusion:
- the current Ash sleeve carries inventory far longer than the hosted path suggests is safe
- stronger Ash should reduce time near `60+` and especially `70+` materially, not just add more passive fills

### 3. The current passive layer is too broad relative to what likely transfers

Evidence:
- hosted passive inside fills are positive, but only `318` units in the sample
- local `default` passive inside fills contribute `5571` units across the three local days
- local passive inside markout per unit is roughly double the hosted 10-step result

Conclusion:
- passive inside quoting is still valuable
- but the current local baseline is likely quoting too many Ash passive opportunities that the hosted matcher does not monetize as well

### 4. A stronger Ash strategy should look different operationally

It should:
- keep the taker edge and recycle edge intact
- cut passive participation to higher-quality inside states instead of assuming broad inside-spread capture transfers
- flatten earlier when inventory drifts away from neutral, especially later in the session
- reduce time at `|pos| >= 60` from the current `35%` to `38%` range toward something much closer to the hosted single-digit profile
- avoid ending days with `50+` or `70+` Ash unless the signal is unusually strong

## Practical Implications For The Next Ash Variant

Highest-priority operational targets:
1. Preserve or improve Ash `none` performance before trusting any default-only gain.
2. Reduce `|pos| >= 60` time materially.
3. Reduce late-day sticky inventory and large terminal positions.
4. Narrow passive inside quoting to states with stronger expected value instead of broad always-on inside placement.
5. Do not sacrifice the currently credible taker edge for a prettier passive profile.

## Execution-Risk Verdict

- **REJECT** any Ash candidate that only improves local `default` by harvesting more passive inside fills.
- **PROMOTE** only candidates that either:
  - improve Ash under `none` or `queue05`, or
  - keep Ash PnL roughly flat while materially reducing high-inventory occupancy.
- Current `v29` Ash edge is real, but its local `default` performance is too passive-fill-dependent to treat as transfer-robust without tighter gating and faster recycling.

## 2026-04-16 Follow-Up Update

### Best transfer-shaped near miss

The best Ash-only candidate from the follow-up search is [round1_pepper_dual_carry_v44.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v44.py).

Against `v29`, `v44` improved Ash in every local mode while reducing total own-trade count:

| Mode | Ash delta | Total own-trade delta |
| --- | ---: | ---: |
| `default` | `+33.0` | `-30` |
| `worse` | `+101.0` | metrics-only compare not summarized here |
| `queue05` | `+123.0` | `-24` |
| `none` | `+156.0` | `-14` |

Interpretation:

- the improvement is execution-quality shaped, not activity-shaped
- the gain is largest in conservative modes, which is exactly what transfer-aware Ash work should prefer
- the improvement is still modest, so it is a near miss rather than a ship signal

### What worked

The only family that improved Ash robustly in this pass was medium-spread taker and recycler suppression:

- `v41`
- `v42`
- `v44`

These variants selectively removed bad aggressive actions in Ash spreads `10` to `13`, especially sell-side bid-hit recycling, while leaving the strong passive inside capture mostly intact.

### What failed on execution-risk grounds

The anchor-extreme passive fade family regressed once it moved beyond taker cleanup:

- `v45` and `v46` improved `none`
- but both lost `default`, `queue05`, and `worse`

Interpretation:

- the second-layer / extra passive fade extension is too fill-sensitive
- current repo evidence does not support promoting broader passive Ash overlays without a richer state model

### Updated risk conclusion

The remaining Ash execution-risk bottleneck is now narrower:

- not “passive inside is bad”
- not “the anchor is wrong”
- but “the current hand-built controller still cannot separate good from bad tactical actions inside the medium-spread regime with enough precision”

That is an action-state mapping problem more than a simple fill-quality problem.
