# Round 1 Execution Risk Report

Date: 2026-04-14

Scope:
- Named baseline: `prosperity_rust_backtester/traders/round1_baseline_v1.py`
- Candidate lineage reviewed:
  - `prosperity_rust_backtester/traders/round1_candidate_v1.py`
  - `prosperity_rust_backtester/traders/round1_candidate_v2.py`
- Validation artifacts reviewed from:
  - `prosperity_rust_backtester/runs/round1-baseline-v1-fairstate`
  - `prosperity_rust_backtester/runs/round1-baseline-v1-worse`
  - `prosperity_rust_backtester/runs/round1-baseline-v1-none`
  - `prosperity_rust_backtester/runs/round1-candidate-v1-fairstate`
  - `prosperity_rust_backtester/runs/round1-candidate-v1-none`
  - `prosperity_rust_backtester/runs/round1-candidate-v2`
  - `prosperity_rust_backtester/runs/round1-candidate-v2-worse`
  - `prosperity_rust_backtester/runs/round1-candidate-v2-none`
  - `prosperity_rust_backtester/runs/round1-candidate-v2-worse-q035`

## Bottom Line

- `round1_candidate_v1.py` had two execution-risk problems:
  - first, one-sided `INTARIAN_PEPPER_ROOT` books forced a constant fallback fair and caused day-dependent sign flips;
  - second, after that was fixed, the extra Pepper book-pressure overlay still looked too fill-model-sensitive.
- `round1_candidate_v2.py` is safer because it replaces the noisy Pepper pressure overlay with a smoother session-trend fair floor. That preserves the main drift edge while reducing dependence on market-trade matching.
- The edge survives stricter local assumptions:
  - default: `239,372.0`
  - `trade-match-mode=worse`: `239,584.0`
  - `trade-match-mode=none`: `216,731.5`
  - `trade-match-mode=worse`, `queue-penetration=0.35`: `227,724.0`

## Dominant Failure Mode In Candidate V1

### First failure: broken one-sided fair fallback

- In the initial v1 logic, `INTARIAN_PEPPER_ROOT` fell back to a constant `11000` fair whenever the book was one-sided.
- That was catastrophic because one-sided rows are common enough to matter:
  - `ASH_COATED_OSMIUM`: about `7.7%`
  - `INTARIAN_PEPPER_ROOT`: about `7.7%`
- Result:
  - day `-2` accidentally became strongly long Pepper and made money;
  - day `-1` and day `0` accidentally became strongly short Pepper and lost heavily;
  - the strategy repeatedly pinned to `+/-80` in the wrong direction.

### Second failure: fill-model-sensitive Pepper pressure tilt

- After carrying forward the last valid Pepper fair, v1 became profitable in the default mode:
  - v1 default total: `168,399.5`
- But robustness was poor:
  - v1 `none` total: `122,457.0`
  - baseline `none` total: `159,915.5`
- The signal diagnosis was:
  - the session drift was real and robust;
  - the added book-pressure tilt improved default-mode monetization;
  - but it also reduced retained long Pepper inventory under `none`, where robust edge should still come mainly from owning the drift.

## Why Candidate V2 Is Safer

- `round1_candidate_v2.py` keeps the valuable part:
  - upward Pepper session drift bias
- It removes the risky part:
  - noisy Pepper microstructure pressure tilt as a direct fair-value add-on
- It replaces it with:
  - a smoother stateful Pepper fair floor that decays slowly instead of snapping around with the current book

Practical effect:
- v2 holds long Pepper inventory more consistently.
- v2 is less dependent on convenient local market-trade matching.
- v2 still keeps the `ASH_COATED_OSMIUM` engine unchanged, so the stable anchored spread-capture logic is preserved.

## Inventory Path

### Baseline (`round1_baseline_v1.py`)

Pepper inventory is meaningful but moderate:

| Mode | Day | Min | Max | Final | Avg abs pos | Time `abs(pos) >= 60` |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| default | `-2` | `-12` | `71` | `27` | `35.20` | `3.1%` |
| default | `-1` | `-4` | `80` | `30` | `33.05` | `6.4%` |
| default | `0` | `-53` | `75` | `43` | `25.86` | `2.5%` |

### Candidate v2

Pepper inventory is deliberately larger and closer to the hard limit:

| Mode | Day | Min | Max | Final | Avg abs pos | Time `abs(pos) >= 60` |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| default | `-2` | `0` | `80` | `58` | `58.77` | `50.7%` |
| default | `-1` | `0` | `80` | `51` | `59.85` | `45.6%` |
| default | `0` | `-7` | `80` | `58` | `57.37` | `40.4%` |
| none | `-2` | `0` | `80` | `71` | `66.07` | `77.9%` |
| none | `-1` | `0` | `80` | `60` | `63.33` | `61.8%` |
| none | `0` | `0` | `80` | `68` | `62.64` | `57.5%` |

Interpretation:
- The strategy is intentionally using position capacity as the main Pepper monetization channel.
- That is acceptable only because the local Pepper sample shows highly consistent upward session drift.
- It is also the main remaining risk if live Round 1 drift weakens or reverses.

## Fill Realism And Matching-Mode Sensitivity

### Trade-count sensitivity

- Baseline:
  - default own trades: `2,348`
  - none own trades: `1,155`
- Candidate v2:
  - default own trades: `2,355`
  - none own trades: `1,164`

Interpretation:
- Removing market-trade matching roughly halves trade count for both strategies.
- The candidate does not collapse when that happens.

### PnL sensitivity

| Strategy | Default total | Worse total | None total |
| --- | ---: | ---: | ---: |
| Baseline | `152,305.5` | `156,131.0` | `159,915.5` |
| Candidate v2 | `239,372.0` | `239,584.0` | `216,731.5` |

Interpretation:
- The candidate is not “good only under optimistic fills.”
- It still beats the baseline materially under `none`.
- The edge compresses under `none`, but remains strong.

### Product mix under stress

- Baseline `none`:
  - `ASH`: `10,521.0`
  - `PEPPER`: `149,394.5`
- Candidate v2 `none`:
  - `ASH`: `10,521.0`
  - `PEPPER`: `206,210.5`

Interpretation:
- `ASH_COATED_OSMIUM` is meaningfully more passive-fill-sensitive than Pepper.
- The candidate’s gain over baseline under strict settings comes almost entirely from better Pepper inventory ownership, not from fragile `ASH` microstructure tricks.

## Passive vs Aggressive Mix

This backtester does not label fills as passive or aggressive directly, but the modes give a usable proxy:

- `trade-match-mode=none` removes market-trade matching.
- v2 still makes `216,731.5` there, with Pepper doing `206,210.5`.
- That strongly suggests the core edge is not “aggressive crossing plus favorable market-trade attribution.”
- It is mainly:
  - owning the Pepper drift,
  - quoting around a rising fair,
  - keeping `ASH` as a separate anchored spread-capture sleeve.

## Adverse Fill / Drawdown Notes

- The initial v1 Pepper logic showed the clearest adverse-fill pathology:
  - wrong-sign inventory accumulation into one-sided books,
  - repeated hard-limit exposure,
  - day-sign flips driven by a bad fallback fair.
- v2 removes that failure mode.
- v2 still accepts a different risk:
  - concentrated long Pepper inventory for long stretches of the session.
- Local evidence says that trade is worth it in this sample.
- Live-round risk remains:
  - if the Pepper session drift weakens, pauses, or reverses for extended periods, the candidate’s PnL will compress much faster than the baseline’s.

## Remaining Risks

1. `INTARIAN_PEPPER_ROOT` drift persistence is the single biggest model assumption.
2. v2 spends `40%` to `78%` of time near the Pepper soft/hard-cap zone depending on stress mode and day.
3. `ASH_COATED_OSMIUM` remains profitable, but much of that profit weakens when market-trade matching is disabled.
4. The candidate is robust in the local backtester, but it is still a sample of only three local Round 1 days.

## Execution-Risk Verdict

- `round1_candidate_v2.py` survives the important local falsification checks.
- It is materially safer than candidate v1.
- It is still a concentration strategy through Pepper inventory, not a low-risk neutral market maker.
- The remaining risk is acceptable for a first Round 1 ship candidate because:
  - the data support for Pepper drift is unusually strong,
  - the edge survives `worse`, `none`, and queue stress,
  - and the anchored `ASH` sleeve remains intact as a separate profit source.
