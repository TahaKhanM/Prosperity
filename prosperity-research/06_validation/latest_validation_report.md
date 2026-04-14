# Round 1 Validation Report

Date: 2026-04-14

Named baseline:
- `prosperity_rust_backtester/traders/round1_baseline_v1.py`

Reference controls:
- `prosperity_rust_backtester/traders/round1_candidate_v2.py`
- `prosperity_rust_backtester/traders/round1_overhaul_v1.py`
- `prosperity_rust_backtester/traders/round1_overhaul_v2.py`

New serious contenders:
- `prosperity_rust_backtester/traders/round1_overhaul_v3.py`
- `prosperity_rust_backtester/traders/round1_overhaul_v4.py`

Final decision in this report:
- **SHIP** `round1_overhaul_v3.py`
- Keep `round1_candidate_v2.py` as the lower-concentration fallback.
- Keep `round1_overhaul_v4.py` only as a diagnostic counterfactual, not as a ship candidate.

## Candidate-Family Comparison

| Family | Core idea | Why it could win | Why it could fail | Outcome |
| --- | --- | --- | --- | --- |
| Baseline | Ash anchored MM, Pepper rolling wall-mid MM | Clean benchmark | Under-owns Pepper local edge | Benchmark only |
| Lower-concentration fallback | Pepper drift-aware but more reactive and less pinned | Less single-story dependence | Leaves too much Pepper edge unowned | Reserve only |
| Overhaul v1 / v2 family | Stronger Pepper ownership plus improved Ash maker | First serious redesign beyond `candidate_v2` | Still under-specifies the template generator story | Superseded |
| Template-aware redesign (`v3`) | Explicit Pepper session-template fair with local book residual control | Best match to the current mechanism map | More concentrated Pepper exposure | Chosen |
| Slower-build template counterfactual (`v4`) | Same template story, more reserve capacity | Tests whether slower accumulation is safer without giving up much edge | Gives up too much local score | Rejected as ship |

## Exact Commands Run

Commands run from `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester` in this iteration:

```bash
python3 -m py_compile traders/round1_overhaul_v3.py traders/round1_overhaul_v4.py
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v3.py --dataset round1 --persist --flat --products full --run-id round1-overhaul-v3
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v4.py --dataset round1 --persist --flat --products full --run-id round1-overhaul-v4
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v3.py --dataset round1 --persist --flat --products full --trade-match-mode worse --run-id round1-overhaul-v3-worse
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v3.py --dataset round1 --persist --flat --products full --trade-match-mode none --run-id round1-overhaul-v3-none
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v3.py --dataset round1 --persist --flat --products full --trade-match-mode worse --queue-penetration 0.35 --run-id round1-overhaul-v3-worse-q035
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v4.py --dataset round1 --persist --flat --products full --trade-match-mode worse --run-id round1-overhaul-v4-worse
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v4.py --dataset round1 --persist --flat --products full --trade-match-mode none --run-id round1-overhaul-v4-none
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v4.py --dataset round1 --persist --flat --products full --trade-match-mode worse --queue-penetration 0.35 --run-id round1-overhaul-v4-worse-q035
```

Benchmark artifacts reused for comparison:

```bash
./scripts/cargo_local.sh run -- --trader traders/round1_baseline_v1.py --dataset round1 --persist --flat --products full --run-id round1-baseline-v1-fairstate
./scripts/cargo_local.sh run -- --trader traders/round1_baseline_v1.py --dataset round1 --persist --flat --products full --trade-match-mode worse --run-id round1-baseline-v1-worse
./scripts/cargo_local.sh run -- --trader traders/round1_baseline_v1.py --dataset round1 --persist --flat --products full --trade-match-mode none --run-id round1-baseline-v1-none
./scripts/cargo_local.sh run -- --trader traders/round1_candidate_v2.py --dataset round1 --persist --flat --products full --run-id round1-candidate-v2
./scripts/cargo_local.sh run -- --trader traders/round1_candidate_v2.py --dataset round1 --persist --flat --products full --trade-match-mode worse --run-id round1-candidate-v2-worse
./scripts/cargo_local.sh run -- --trader traders/round1_candidate_v2.py --dataset round1 --persist --flat --products full --trade-match-mode none --run-id round1-candidate-v2-none
./scripts/cargo_local.sh run -- --trader traders/round1_candidate_v2.py --dataset round1 --persist --flat --products full --trade-match-mode worse --queue-penetration 0.35 --run-id round1-candidate-v2-worse-q035
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v1.py --dataset round1 --persist --flat --products full --run-id round1-overhaul-v1
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v1.py --dataset round1 --persist --flat --products full --trade-match-mode worse --run-id round1-overhaul-v1-worse
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v1.py --dataset round1 --persist --flat --products full --trade-match-mode none --run-id round1-overhaul-v1-none
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v1.py --dataset round1 --persist --flat --products full --trade-match-mode worse --queue-penetration 0.35 --run-id round1-overhaul-v1-worse-q035
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v2.py --dataset round1 --persist --flat --products full --run-id round1-overhaul-v2
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v2.py --dataset round1 --persist --flat --products full --trade-match-mode worse --run-id round1-overhaul-v2-worse
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v2.py --dataset round1 --persist --flat --products full --trade-match-mode none --run-id round1-overhaul-v2-none
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v2.py --dataset round1 --persist --flat --products full --trade-match-mode worse --queue-penetration 0.35 --run-id round1-overhaul-v2-worse-q035
```

## Artifact Set Inspected

- `metrics.json`
- `bundle.json`
- `activity.csv`
- `pnl_by_product.csv`
- `trades.csv`

Reviewed under:
- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/runs/round1-overhaul-v3*`
- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/runs/round1-overhaul-v4*`
- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/runs/round1-overhaul-v1*`
- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/runs/round1-overhaul-v2*`
- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/runs/round1-candidate-v2*`
- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/runs/round1-baseline-v1-*`

## Headline Results

### Full-bundle totals

| Strategy | default | `worse` | `none` | `worse + q=0.35` |
| --- | ---: | ---: | ---: | ---: |
| Baseline | `152,305.5` | `156,131.0` | `159,915.5` | n/a |
| Candidate v2 | `239,372.0` | `239,584.0` | `216,731.5` | `227,724.0` |
| Overhaul v1 | `276,821.0` | `276,835.0` | `241,552.0` | `254,590.0` |
| Overhaul v2 | `276,828.0` | `276,842.0` | `241,564.0` | `254,602.0` |
| Overhaul v3 | `282,373.0` | `282,340.0` | `245,303.0` | `259,507.0` |
| Overhaul v4 | `281,652.0` | `281,619.0` | `242,893.0` | `257,793.0` |

### `v3` deltas versus prior ships

| Comparison | default | `worse` | `none` | `worse + q=0.35` |
| --- | ---: | ---: | ---: | ---: |
| `v3 - candidate_v2` | `+43,001.0` | `+42,756.0` | `+28,571.5` | `+31,783.0` |
| `v3 - overhaul_v1` | `+5,552.0` | `+5,505.0` | `+3,751.0` | `+4,917.0` |
| `v3 - overhaul_v4` | `+721.0` | `+721.0` | `+2,410.0` | `+1,714.0` |

### Default per-day comparison

| Day | Candidate v2 | Overhaul v1 | Overhaul v3 | Overhaul v4 |
| --- | ---: | ---: | ---: | ---: |
| `-2` | `78,662.0` | `91,495.0` | `92,534.0` | `92,081.0` |
| `-1` | `82,058.0` | `93,751.0` | `95,750.0` | `95,187.0` |
| `0` | `78,652.0` | `91,575.0` | `94,089.0` | `94,384.0` |

### Default product contribution

| Strategy | `ASH_COATED_OSMIUM` | `INTARIAN_PEPPER_ROOT` |
| --- | ---: | ---: |
| Candidate v2 | `38,318.0` | `201,054.0` |
| Overhaul v1 | `45,608.0` | `231,213.0` |
| Overhaul v3 | `45,608.0` | `236,765.0` |
| Overhaul v4 | `45,608.0` | `236,044.0` |

## Artifact-Backed Diagnosis

### What `round1_overhaul_v1.py` already got right

- Pepper should be owned early rather than treated as a neutral market-making product.
- Ash should stay in an anchored maker architecture.
- One-sided Pepper books are too brief to deserve primary strategy status.

### What `round1_overhaul_v1.py` still over-assumed

- It mostly treated Pepper as a reactive rising state inferred from the visible book.
- The deeper adversarial analysis showed a stronger story:
  - Pepper fair looks session-template-driven,
  - the book mostly reveals and locally overshoots that path,
  - and trades often precede quote refresh.

### Why `round1_overhaul_v3.py` is a real redesign

- `v3` replaces the Pepper fair model with an explicit session-template curve.
- It uses the book as a residual-control layer rather than as the root drift signal.
- That yields more Pepper PnL in every tested mode without degrading Ash.
- The improvement is therefore explainable by a stronger generator hypothesis, not just by threshold retuning.

### Why `round1_overhaul_v4.py` matters even though it lost

- `v4` was the slower-build counterfactual:
  - same template story,
  - more reserve capacity,
  - later max-long acquisition.
- It still beat the older ships.
- It still lost to `v3` in every tested mode.
- That is useful because it argues the bundle rewards earlier template ownership, not merely any drift-aware carry posture.

## Concentration And Inventory Read

- `v3` Pepper average absolute position: `78.96`
- `v3` Pepper time `|pos| >= 60`: `99.94%`
- `v3` Pepper time `|pos| >= 70`: `99.94%`
- `v3` first Pepper `|pos| >= 60` by day: `[900, 200, 600]`
- `v3` first Pepper `|pos| >= 78` by day: `[1000, 300, 900]`

Interpretation:
- `v3` is not lower-concentration than `v1`.
- It is a more explicit version of the same core local bet:
  - Pepper fair is telegraphed,
  - acquire early,
  - defend and recycle around the long.

## Competition-Specific Robustness Check

Adversarial question:
- Does the edge mostly come from opening acquisition, or does the strategy still monetize the local generator later in the session?

Pepper default PnL by coarse session split:
- Candidate v2: first quarter `45,523.5`, middle half `52,973.5`, second half `102,557.0`
- Overhaul v1: first quarter `55,992.0`, middle half `59,001.0`, second half `116,220.0`
- Overhaul v3: first quarter `57,912.0`, middle half `60,586.0`, second half `118,267.0`
- Overhaul v4: first quarter `56,705.0`, middle half `60,658.0`, second half `118,681.0`

Interpretation:
- `v3` does benefit from earlier acquisition.
- The uplift versus `v1` is not only an opening burst.
- It also improves later-session Pepper monetization through more active template-relative recycling.

## Validation Decision

**SHIP `round1_overhaul_v3.py`**

Reason:
- It is the best-performing contender across the full bundle and all required stress modes.
- Its edge is consistent with the strongest current mechanism map:
  - Ash: anchored replenishing maker,
  - Pepper: competition-specific session-template fair with lagged book revelation.
- `v4` weakens the case for a slower-build alternative.

Caveat:
- The strategy remains highly concentrated in Pepper.
- It should be understood as a competition-specific exploit, not a generally safer architecture.

## Fallback Note

- If the team wants the most mechanism-humble and lower-concentration option, keep `round1_candidate_v2.py` ready.
- If the team wants the strongest current exploit of the observed local Round 1 generator, use `round1_overhaul_v3.py`.
