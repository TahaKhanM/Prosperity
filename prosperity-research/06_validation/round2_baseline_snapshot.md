# Round 2 Baseline Snapshot

Date: 2026-04-19

Named baseline:
- [baseline.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round%202/baseline.py)

Primary validation surface:
- explicit non-carry Round 2 day runs on:
  - day `-1`
  - day `0`
  - day `1`
- dataset root:
  [datasets/round2](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/datasets/round2)

Reason for explicit day split:
- the current multi-day Round 2 harness collides day `-1` and day `1` artifact
  names, so persisted bundle outputs are not durable enough for diagnosis
- the baseline snapshot below uses explicit single-day runs to avoid that bug

## Baseline Runs

- day `-1`:
  [round2-baseline-dayneg1-day-1](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/runs/round2-baseline-dayneg1-day-1)
- day `0`:
  [round2-baseline-day0-day0](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/runs/round2-baseline-day0-day0)
- day `1`:
  [round2-baseline-day1-day1](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/runs/round2-baseline-day1-day1)

Per-day diagnosis packets:
- [baseline day -1 packet](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/05_execution_risk/diagnosis_packets/2026-04-19_round2_baseline_dayneg1/diagnosis_packet.md)
- [baseline day 0 packet](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/05_execution_risk/diagnosis_packets/2026-04-19_round2_baseline_day0/diagnosis_packet.md)
- [baseline day 1 packet](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/05_execution_risk/diagnosis_packets/2026-04-19_round2_baseline_day1/diagnosis_packet.md)

## Headline Metrics

- summed total PnL: `310101.5`
- summed per-product PnL:
  - `INTARIAN_PEPPER_ROOT`: `246449.5`
  - `ASH_COATED_OSMIUM`: `63652.0`

Per-day totals:

| Day | Total PnL | Pepper PnL | Ash PnL | Own trades |
| --- | ---: | ---: | ---: | ---: |
| `-1` | `102962.5` | `81715.5` | `21247.0` | `959` |
| `0` | `102777.0` | `82194.0` | `20583.0` | `912` |
| `1` | `104362.0` | `82540.0` | `21822.0` | `990` |

## Inventory Behavior

Dominant inventory fact:
- baseline Pepper spends almost the entire day near the hard limit on all three
  days

Pepper near-limit occupancy from the day packets:
- day `-1`: `94.51%`
- day `0`: `94.58%`
- day `1`: `94.24%`

Pepper average absolute position:
- day `-1`: `77.4709`
- day `0`: `77.4326`
- day `1`: `77.3212`

Ash near-limit occupancy:
- day `-1`: `8.60%`
- day `0`: `17.56%`
- day `1`: `1.85%`

Interpretation:
- the baseline is effectively a max-long Pepper carry strategy with some
  recycling around that inventory
- Ash contributes meaningfully, but Pepper dominates the total baseline PnL

## Fill / Execution Read

Pepper aggressive buy edge h5 average from the day packets:
- day `-1`: `2.9755`
- day `0`: `3.0424`
- day `1`: `3.5000`

Pepper passive sell edge h5 average:
- day `-1`: `5.2506`
- day `0`: `6.0267`
- day `1`: `6.2389`

Interpretation:
- baseline Pepper monetizes the structural up-drift by staying long and
  repeatedly refilling on small pullbacks
- any winning candidate must either improve Pepper monetization without losing
  too much carry or add enough Ash/selection edge to overcome this carry-heavy
  baseline

## Baseline To Beat

Primary threshold for success:
- a candidate must exceed `341111.65` total PnL on the declared primary
  surface, which is `1.10 x 310101.5`

## Baseline Verdict

- This is a strong local baseline, not a trivial strawman.
- The largest local weakness is structural:
  Pepper is driven by a crude open-anchor / long-carry controller and sits near
  the long limit almost all session.
- The largest validation risk is also structural:
  the local surface may reward near-max Pepper carry so strongly that smaller
  execution gains elsewhere are insufficient to clear the `>10%` bar.
