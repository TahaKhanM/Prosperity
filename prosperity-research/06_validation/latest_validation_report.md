# Round 1 Validation Report

Date: 2026-04-14

Named baseline:
- `prosperity_rust_backtester/traders/round1_baseline_v1.py`

Reference controls:
- `prosperity_rust_backtester/traders/round1_candidate_v2.py`
- `prosperity_rust_backtester/traders/round1_overhaul_v3.py`

New serious contenders:
- `prosperity_rust_backtester/traders/round1_overhaul_v5.py`
- `prosperity_rust_backtester/traders/round1_overhaul_v6.py`
- `prosperity_rust_backtester/traders/round1_overhaul_v7.py`

Final decision in this report:
- **SHIP** `round1_overhaul_v6.py`
- Keep `round1_overhaul_v3.py` as the simpler prior ship.
- Keep `round1_candidate_v2.py` as the lower-concentration fallback.
- Reject `round1_overhaul_v7.py` as unnecessary tactical complexity.

## Candidate-Family Comparison

| Family | Core idea | Why it could win | Why it could fail | Outcome |
| --- | --- | --- | --- | --- |
| `v3` template exploit | Explicit Pepper session-template fair plus local residual control | Strongest clean redesign beyond `candidate_v2` | Coarse Pepper curve can miss phase detail | Superseded |
| `v5` trade-aware overlay | Add Pepper trade-tape state on top of `v3` | Tape may sharpen dip-chasing and recycling | Tape effect may be too small to matter | Small improvement only |
| `v6` phase-corrected template | Replace the coarse Pepper curve with a finer session-shape model | Better fair path should improve both carry and recycling | Could overfit three local days | Chosen |
| `v7` residual × imbalance tactical overlay | Add more conditional Pepper recycling on top of `v6` | Could exploit local residual-state asymmetry | Extra complexity may not pay for itself | Rejected |

## Exact Commands Run

Commands run from `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester` in this pass:

```bash
python3 -m py_compile traders/round1_overhaul_v5.py
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v5.py --dataset round1 --persist --flat --products full --run-id round1-overhaul-v5
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v5.py --dataset round1 --persist --flat --products full --trade-match-mode worse --run-id round1-overhaul-v5-worse
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v5.py --dataset round1 --persist --flat --products full --trade-match-mode none --run-id round1-overhaul-v5-none
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v5.py --dataset round1 --persist --flat --products full --trade-match-mode worse --queue-penetration 0.35 --run-id round1-overhaul-v5-worse-q035
python3 -m py_compile traders/round1_overhaul_v6.py
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v6.py --dataset round1 --persist --flat --products full --run-id round1-overhaul-v6
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v6.py --dataset round1 --persist --flat --products full --trade-match-mode worse --run-id round1-overhaul-v6-worse
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v6.py --dataset round1 --persist --flat --products full --trade-match-mode none --run-id round1-overhaul-v6-none
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v6.py --dataset round1 --persist --flat --products full --trade-match-mode worse --queue-penetration 0.35 --run-id round1-overhaul-v6-worse-q035
python3 -m py_compile traders/round1_overhaul_v7.py
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v7.py --dataset round1 --persist --flat --products full --run-id round1-overhaul-v7
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v7.py --dataset round1 --persist --flat --products full --trade-match-mode worse --run-id round1-overhaul-v7-worse
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v7.py --dataset round1 --persist --flat --products full --trade-match-mode none --run-id round1-overhaul-v7-none
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v7.py --dataset round1 --persist --flat --products full --trade-match-mode worse --queue-penetration 0.35 --run-id round1-overhaul-v7-worse-q035
```

Benchmark artifacts reused for comparison:

```bash
./scripts/cargo_local.sh run -- --trader traders/round1_candidate_v2.py --dataset round1 --persist --flat --products full --run-id round1-candidate-v2
./scripts/cargo_local.sh run -- --trader traders/round1_candidate_v2.py --dataset round1 --persist --flat --products full --trade-match-mode worse --run-id round1-candidate-v2-worse
./scripts/cargo_local.sh run -- --trader traders/round1_candidate_v2.py --dataset round1 --persist --flat --products full --trade-match-mode none --run-id round1-candidate-v2-none
./scripts/cargo_local.sh run -- --trader traders/round1_candidate_v2.py --dataset round1 --persist --flat --products full --trade-match-mode worse --queue-penetration 0.35 --run-id round1-candidate-v2-worse-q035
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v3.py --dataset round1 --persist --flat --products full --run-id round1-overhaul-v3
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v3.py --dataset round1 --persist --flat --products full --trade-match-mode worse --run-id round1-overhaul-v3-worse
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v3.py --dataset round1 --persist --flat --products full --trade-match-mode none --run-id round1-overhaul-v3-none
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v3.py --dataset round1 --persist --flat --products full --trade-match-mode worse --queue-penetration 0.35 --run-id round1-overhaul-v3-worse-q035
```

## Artifact Set Inspected

- `metrics.json`
- `bundle.json`
- `activity.csv`
- `pnl_by_product.csv`
- `trades.csv`

Reviewed under:
- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/runs/round1-overhaul-v5*`
- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/runs/round1-overhaul-v6*`
- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/runs/round1-overhaul-v7*`
- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/runs/round1-overhaul-v3*`
- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/runs/round1-candidate-v2*`

## Headline Results

### Full-bundle totals

| Strategy | default | `worse` | `none` | `worse + q=0.35` |
| --- | ---: | ---: | ---: | ---: |
| Candidate v2 | `239,372.0` | `239,584.0` | `216,731.5` | `227,724.0` |
| Overhaul v3 | `282,373.0` | `282,340.0` | `245,303.0` | `259,507.0` |
| Overhaul v5 | `282,407.0` | `282,374.0` | `245,314.0` | `259,542.0` |
| Overhaul v6 | `282,974.0` | `282,941.0` | `245,673.0` | `259,990.0` |
| Overhaul v7 | `282,920.0` | `282,887.0` | `245,630.0` | `259,919.0` |

### Deltas versus `v3`

| Strategy | default | `worse` | `none` | `worse + q=0.35` |
| --- | ---: | ---: | ---: | ---: |
| `v5 - v3` | `+34.0` | `+34.0` | `+11.0` | `+35.0` |
| `v6 - v3` | `+601.0` | `+601.0` | `+370.0` | `+483.0` |
| `v7 - v3` | `+547.0` | `+547.0` | `+327.0` | `+412.0` |

### Deltas versus `v6`

| Strategy | default | `worse` | `none` | `worse + q=0.35` |
| --- | ---: | ---: | ---: | ---: |
| `v5 - v6` | `-567.0` | `-567.0` | `-359.0` | `-448.0` |
| `v7 - v6` | `-54.0` | `-54.0` | `-43.0` | `-71.0` |

### Default product contribution

| Strategy | `ASH_COATED_OSMIUM` | `INTARIAN_PEPPER_ROOT` |
| --- | ---: | ---: |
| Candidate v2 | `38,318.0` | `201,054.0` |
| Overhaul v3 | `45,608.0` | `236,765.0` |
| Overhaul v5 | `45,608.0` | `236,799.0` |
| Overhaul v6 | `45,608.0` | `237,366.0` |
| Overhaul v7 | `45,608.0` | `237,312.0` |

## Artifact-Backed Diagnosis

### What `v5` proved

- Pepper trade processing matters.
- But the gain is too small for tape logic alone to be the main story.

### What `v6` proved

- The current strongest remaining inefficiency in `v3` was the Pepper fair curve itself.
- Once the phase shape is corrected, the strategy improves in every required stress mode.
- The gain is still all Pepper, which matches the mechanism map.

### Why `v7` was rejected

- The residual × imbalance interaction is real in analysis.
- But on top of `v6`, it was already being captured well enough by the simpler design.
- The extra tactical branching reduced performance slightly in every tested mode.

## Concentration And Inventory Read

- `v6` Pepper average absolute position: `78.88`
- `v6` Pepper time `|pos| >= 60`: `99.94%`
- `v6` Pepper time `|pos| >= 70`: `99.94%`
- `v6` first Pepper `|pos| >= 78` by day: `[900, 1000, 300]`

Interpretation:
- `v6` is still a high-conviction Pepper strategy.
- The improvement is better fair modeling, not lower inventory concentration.

## Validation Decision

**SHIP `round1_overhaul_v6.py`**

Reason:
- It is the strongest contender across default, `worse`, `none`, and queue stress.
- Its gain over `v3` is not a one-mode artifact.
- Its mechanism story is cleaner than `v5` and less over-engineered than `v7`.

Caveat:
- This remains a competition-specific exploit of the local Pepper generator.
- `round1_candidate_v2.py` is still the correct fallback when lower Pepper concentration is preferred.
