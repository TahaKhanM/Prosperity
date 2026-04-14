# Round 1 Validation Report

Date: 2026-04-14

Named baseline:
- `prosperity_rust_backtester/traders/round1_baseline_v1.py`

Final candidate judged:
- `prosperity_rust_backtester/traders/round1_candidate_v2.py`

Intermediate rejected candidate:
- `prosperity_rust_backtester/traders/round1_candidate_v1.py`

## Candidate Families Considered

| Candidate | Fair-value hypothesis | Entry / take rules | Passive quoting | Risk controls | Expected failure mode | Why it might win |
| --- | --- | --- | --- | --- | --- | --- |
| Baseline | `ASH`: anchored `10000`; `PEPPER`: current rolling wall-mid | Take only clearly stale prices around current fair | Two-sided calm quoting around fair | Soft caps, inventory skew, light clearing | Sells too much Pepper into persistent drift | Clean, interpretable benchmark |
| Execution-aware baseline | Same fair ideas, calmer quote improvement | Same stale-quote taking | Better inside-spread discipline, smaller risk-side size | Stronger skew, less eager clearing | Leaves Pepper trend money on the table | Safer execution without bigger model risk |
| Candidate v1 | Add Pepper forward fair from session drift plus book pressure | More selective Pepper buys/sells around a lifted fair | Same quoting skeleton | Same hard/soft limits | Pressure overlay may be fill-model-sensitive | More upside if book pressure is real |
| Reversion / event candidate | Fade short spikes in both products | Contra-take after 5-step shocks | Temporary contra-skew only | Tight size, fast inventory relief | Reversion signal smaller than spread | Good secondary overlay, weak primary engine |
| Candidate v2 | Pepper should be traded around a smooth rising session fair floor | Keep stale-quote taking, but maintain long Pepper bias | Quote around a stateful upward fair | Same caps plus smoother fair persistence | Pepper drift disappears or reverses live | Strongest local support with cleaner robustness |

Selection rule used:
- choose the simplest logic that is clearly supported by local data and still survives stricter fill assumptions.

## Exact Commands Run

From `prosperity_rust_backtester/`:

```bash
python3 -m py_compile traders/round1_baseline_v1.py traders/round1_candidate_v1.py traders/round1_candidate_v2.py
./scripts/cargo_local.sh run -- --trader traders/round1_baseline_v1.py --dataset round1 --persist --flat --products full --run-id round1-baseline-v1-fairstate
./scripts/cargo_local.sh run -- --trader traders/round1_baseline_v1.py --dataset round1 --persist --flat --products full --trade-match-mode worse --run-id round1-baseline-v1-worse
./scripts/cargo_local.sh run -- --trader traders/round1_baseline_v1.py --dataset round1 --persist --flat --products full --trade-match-mode none --run-id round1-baseline-v1-none
./scripts/cargo_local.sh run -- --trader traders/round1_candidate_v1.py --dataset round1 --persist --flat --products full --run-id round1-candidate-v1-fairstate
./scripts/cargo_local.sh run -- --trader traders/round1_candidate_v1.py --dataset round1 --persist --flat --products full --trade-match-mode none --run-id round1-candidate-v1-none
./scripts/cargo_local.sh run -- --trader traders/round1_candidate_v2.py --dataset round1 --persist --flat --products full --run-id round1-candidate-v2
./scripts/cargo_local.sh run -- --trader traders/round1_candidate_v2.py --dataset round1 --persist --flat --products full --trade-match-mode worse --run-id round1-candidate-v2-worse
./scripts/cargo_local.sh run -- --trader traders/round1_candidate_v2.py --dataset round1 --persist --flat --products full --trade-match-mode none --run-id round1-candidate-v2-none
./scripts/cargo_local.sh run -- --trader traders/round1_candidate_v2.py --dataset round1 --persist --flat --products full --trade-match-mode worse --queue-penetration 0.35 --run-id round1-candidate-v2-worse-q035
```

## Intermediate Diagnosis

### Why candidate v1 was not enough

- First issue:
  - Pepper one-sided books plus a constant fallback fair created day-dependent sign errors.
- After fixing that, v1 improved to `168,399.5` in the default mode.
- But v1 still failed the robustness comparison:
  - v1 `none`: `122,457.0`
  - baseline `none`: `159,915.5`
- That justified one more iteration.

### Why candidate v2 was built

- The strong Pepper session drift remained the best local edge.
- The fill-model-sensitive part was the extra Pepper pressure tilt, not the trend itself.
- v2 therefore kept:
  - the Pepper session-trend fair
- and removed:
  - the noisier pressure-driven fair adjustments

## Baseline vs Candidate v2

### Full-bundle totals

| Mode | Baseline | Candidate v2 | Delta |
| --- | ---: | ---: | ---: |
| default | `152,305.5` | `239,372.0` | `+87,066.5` |
| `worse` | `156,131.0` | `239,584.0` | `+83,453.0` |
| `none` | `159,915.5` | `216,731.5` | `+56,816.0` |

Additional queue stress on candidate v2:

| Mode | Candidate v2 total |
| --- | ---: |
| `worse`, `queue-penetration=0.35` | `227,724.0` |

### Default per-day comparison

| Day | Baseline | Candidate v2 | Delta |
| --- | ---: | ---: | ---: |
| `-2` | `54,647.5` | `78,662.0` | `+24,014.5` |
| `-1` | `56,509.0` | `82,058.0` | `+25,549.0` |
| `0` | `41,149.0` | `78,652.0` | `+37,503.0` |

### Product contribution

Default mode aggregate by product:

| Product | Baseline | Candidate v2 | Delta |
| --- | ---: | ---: | ---: |
| `ASH_COATED_OSMIUM` | `38,318.0` | `38,318.0` | `0.0` |
| `INTARIAN_PEPPER_ROOT` | `113,987.5` | `201,054.0` | `+87,066.5` |

Interpretation:
- The whole improvement comes from better Pepper logic.
- `ASH` is stable across the lineage and serves as a clean anchored sleeve.

## Robustness Read

### What held up

- Candidate v2 beat the baseline in all three comparison modes.
- Candidate v2 stayed above the local `200,000` round objective even in the strict `none` mode.
- Queue penetration stress reduced PnL but did not break the strategy.

### What remains risky

- Candidate v2 uses more Pepper inventory than the baseline.
- It often spends large fractions of the session near the Pepper limit zone.
- The strategy is therefore robust to local fill-model stress, but not low-risk in the ordinary sense.
- The main residual model risk is live Pepper drift changing shape.

## Validation Decision

**SHIP**

Reason:
- `round1_candidate_v2.py` is the best locally validated first Round 1 strategy in this iteration.
- It beats the named baseline:
  - in the default run,
  - in `trade-match-mode=worse`,
  - in `trade-match-mode=none`,
  - and it remains strong under queue penetration stress.
- The edge is attributable and understandable:
  - `ASH` stays a simple anchored market maker;
  - `PEPPER` is traded as a drifting product around a smooth rising fair.

## Next Validation Step

- The next thing to test is not a full redesign.
- The next useful check is whether Pepper drift remains this clean on any newly available Round 1 sample or portal run artifact.
- If live evidence shows weaker or less monotonic Pepper drift, reduce the Pepper fair floor and the time spent near `+80`.
