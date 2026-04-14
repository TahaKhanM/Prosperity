# Round 1 Validation Report

Date: 2026-04-14

Named baseline:
- `prosperity_rust_backtester/traders/round1_baseline_v1.py`

Reference controls:
- `prosperity_rust_backtester/traders/round1_candidate_v2.py`
- `prosperity_rust_backtester/traders/round1_overhaul_v8.py`
- `prosperity_rust_backtester/traders/round1_overhaul_v10.py`

New contenders from this pass:
- `prosperity_rust_backtester/traders/round1_overhaul_v12.py`
- `prosperity_rust_backtester/traders/round1_overhaul_v13.py`
- `prosperity_rust_backtester/traders/round1_overhaul_v14.py`
- `prosperity_rust_backtester/traders/round1_overhaul_v15.py`
- `prosperity_rust_backtester/traders/round1_overhaul_v16.py`
- `prosperity_rust_backtester/traders/round1_overhaul_v17.py`
- `prosperity_rust_backtester/traders/round1_overhaul_v18.py`
- `prosperity_rust_backtester/traders/round1_overhaul_v19.py`
- `prosperity_rust_backtester/traders/round1_overhaul_v20.py`
- `prosperity_rust_backtester/traders/round1_overhaul_v21.py`
- `prosperity_rust_backtester/traders/round1_overhaul_v22.py`

Final decision in this report:
- **SHIP** `round1_overhaul_v22.py`
- Keep `round1_overhaul_v14.py` as the prior clean control.
- Keep `round1_overhaul_v20.py` as the key intermediate branch.
- Keep `round1_overhaul_v12.py` only as a rejected research branch.

## Candidate-Family Comparison

| Family | Core idea | Why it could improve official | Why it could fail | Outcome |
| --- | --- | --- | --- | --- |
| `v10` reference | Pepper template carry plus template-anchored recycle | current best prior ship | Ash still under-monetized and fill-sensitive | benchmark |
| `v12` Ash directional redesign | explicit Ash signal-state engine | attacks local/official Ash bottleneck directly | too much Ash complexity at once | rejected |
| `v13` conservative Ash upgrade | same Ash market type, better take and quote placement | cleaner Ash execution with little model risk | may leave some Ash edge untapped | strong |
| `v14` assertive Ash maker/taker | push the same `v13` idea further with unchanged Pepper | better second edge, still explainable | Ash matching could still be harsher officially | prior ship |
| `v15` Ash regime-gated skew | implement a mild report-driven Ash regime lean | safe way to test Ash hidden-pattern logic | did not beat simpler `v14` | rejected |
| `v16` Pepper recycle–reacquire | add small symmetric Pepper reacquire after recycle | direct test of report’s residual-domain recycle thesis | only a near-tie, not a new frontier | rejected |
| `v17` Ash book-aware quoting | replace fixed Ash passive offsets with join/undercut logic around the live book | better monetization of anchored spread states | can still leave Ash capacity trapped | strong |
| `v20` Ash fair-based clearing | recycle large Ash inventory against current fair instead of the hard anchor | frees Ash capacity and improves all days | could over-clear if fair is too noisy | strong |
| `v21` Ash execution stack | combine fair-based clearing with stronger wide-spread Ash sizing | stronger Ash monetization without changing Pepper | still partially anchored on a hybrid clear reference | strong |
| `v22` full-fair Ash recycling | clear large Ash inventory directly against current fair with the same book-aware quoting stack | strongest clean Ash improvement in all required modes | official Ash may still match more harshly | chosen |

## Exact Commands Run

Commands run from `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester` in this pass:

```bash
python3 -m py_compile traders/round1_overhaul_v12.py
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v12.py --dataset round1 --persist --flat --products full --run-id round1-overhaul-v12

python3 -m py_compile traders/round1_overhaul_v13.py
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v13.py --dataset round1 --persist --flat --products full --run-id round1-overhaul-v13
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v13.py --dataset round1 --persist --flat --products full --trade-match-mode worse --run-id round1-overhaul-v13-worse
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v13.py --dataset round1 --persist --flat --products full --trade-match-mode none --run-id round1-overhaul-v13-none
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v13.py --dataset round1 --persist --flat --products full --trade-match-mode worse --queue-penetration 0.35 --run-id round1-overhaul-v13-worse-q035

python3 -m py_compile traders/round1_overhaul_v14.py
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v14.py --dataset round1 --persist --flat --products full --run-id round1-overhaul-v14
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v14.py --dataset round1 --persist --flat --products full --trade-match-mode worse --run-id round1-overhaul-v14-worse
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v14.py --dataset round1 --persist --flat --products full --trade-match-mode none --run-id round1-overhaul-v14-none
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v14.py --dataset round1 --persist --flat --products full --trade-match-mode worse --queue-penetration 0.35 --run-id round1-overhaul-v14-worse-q035

python3 -m py_compile traders/round1_overhaul_v15.py
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v15.py --dataset round1 --persist --flat --products full --run-id round1-overhaul-v15

python3 -m py_compile traders/round1_overhaul_v16.py
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v16.py --dataset round1 --persist --flat --products full --run-id round1-overhaul-v16

python3 -m py_compile traders/round1_overhaul_v17.py
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v17.py --dataset round1 --persist --flat --products full --run-id round1-overhaul-v17
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v17.py --dataset round1 --persist --flat --products full --trade-match-mode worse --run-id round1-overhaul-v17-worse
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v17.py --dataset round1 --persist --flat --products full --trade-match-mode none --run-id round1-overhaul-v17-none
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v17.py --dataset round1 --persist --flat --products full --trade-match-mode worse --queue-penetration 0.35 --run-id round1-overhaul-v17-worse-q035

python3 -m py_compile traders/round1_overhaul_v18.py
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v18.py --dataset round1 --persist --flat --products full --run-id round1-overhaul-v18

python3 -m py_compile traders/round1_overhaul_v19.py
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v19.py --dataset round1 --persist --flat --products full --run-id round1-overhaul-v19

python3 -m py_compile traders/round1_overhaul_v20.py
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v20.py --dataset round1 --persist --flat --products full --run-id round1-overhaul-v20

python3 -m py_compile traders/round1_overhaul_v21.py
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v21.py --dataset round1 --persist --flat --products full --run-id round1-overhaul-v21
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v21.py --dataset round1 --persist --flat --products full --trade-match-mode worse --run-id round1-overhaul-v21-worse
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v21.py --dataset round1 --persist --flat --products full --trade-match-mode none --run-id round1-overhaul-v21-none
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v21.py --dataset round1 --persist --flat --products full --trade-match-mode worse --queue-penetration 0.35 --run-id round1-overhaul-v21-worse-q035

python3 -m py_compile traders/round1_overhaul_v22.py
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v22.py --dataset round1 --persist --flat --products full --run-id round1-overhaul-v22
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v22.py --dataset round1 --persist --flat --products full --trade-match-mode worse --run-id round1-overhaul-v22-worse
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v22.py --dataset round1 --persist --flat --products full --trade-match-mode none --run-id round1-overhaul-v22-none
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v22.py --dataset round1 --persist --flat --products full --trade-match-mode worse --queue-penetration 0.35 --run-id round1-overhaul-v22-worse-q035
```

Reference benchmark artifacts reused:

```bash
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v10.py --dataset round1 --persist --flat --products full --run-id round1-overhaul-v10c
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v10.py --dataset round1 --persist --flat --products full --trade-match-mode worse --run-id round1-overhaul-v10c-worse
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v10.py --dataset round1 --persist --flat --products full --trade-match-mode none --run-id round1-overhaul-v10c-none
./scripts/cargo_local.sh run -- --trader traders/round1_overhaul_v10.py --dataset round1 --persist --flat --products full --trade-match-mode worse --queue-penetration 0.35 --run-id round1-overhaul-v10c-worse-q035
```

## Artifact Set Inspected

- `manifest.json`
- `metrics.json`
- `bundle.json`
- `activity.csv`
- `pnl_by_product.csv`
- `trades.csv`

Reviewed under:
- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/runs/round1-overhaul-v10c*`
- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/runs/round1-overhaul-v13*`
- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/runs/round1-overhaul-v14*`

## Headline Results

### Full-bundle totals

| Strategy | default | `worse` | `none` | `worse + q=0.35` |
| --- | ---: | ---: | ---: | ---: |
| Overhaul v10 | `283,766.0` | `283,733.0` | `246,184.0` | `260,765.0` |
| Overhaul v12 | `280,326.0` | not run | not run | not run |
| Overhaul v13 | `286,236.0` | `286,224.0` | `247,519.0` | `261,973.0` |
| Overhaul v14 | `286,971.0` | `286,916.0` | `247,998.0` | `262,604.0` |
| Overhaul v15 | `286,851.0` | not run | not run | not run |
| Overhaul v16 | `286,963.0` | not run | not run | not run |
| Overhaul v17 | `287,714.0` | `287,714.0` | `247,998.0` | `262,803.0` |
| Overhaul v18 | `287,664.0` | not run | not run | not run |
| Overhaul v19 | `287,768.0` | not run | not run | not run |
| Overhaul v20 | `287,940.0` | not run | not run | not run |
| Overhaul v21 | `287,993.0` | `287,993.0` | `248,108.0` | `263,032.0` |
| Overhaul v22 | `288,401.0` | `288,401.0` | `248,290.0` | `263,370.0` |

### Deltas versus `v10`

| Strategy | default | `worse` | `none` | `worse + q=0.35` |
| --- | ---: | ---: | ---: | ---: |
| `v13 - v10` | `+2,470.0` | `+2,491.0` | `+1,335.0` | `+1,208.0` |
| `v14 - v10` | `+3,205.0` | `+3,183.0` | `+1,814.0` | `+1,839.0` |
| `v22 - v14` | `+1,430.0` | `+1,485.0` | `+292.0` | `+766.0` |
| `v22 - v10` | `+4,635.0` | `+4,668.0` | `+2,106.0` | `+2,605.0` |

### Product contribution

Default:

| Strategy | `ASH_COATED_OSMIUM` | `INTARIAN_PEPPER_ROOT` |
| --- | ---: | ---: |
| Overhaul v10 | `45,608.0` | `238,158.0` |
| Overhaul v13 | `48,078.0` | `238,158.0` |
| Overhaul v14 | `48,813.0` | `238,158.0` |
| Overhaul v22 | `50,243.0` | `238,158.0` |

`none`:

| Strategy | `ASH_COATED_OSMIUM` | `INTARIAN_PEPPER_ROOT` |
| --- | ---: | ---: |
| Overhaul v10 | `10,262.0` | `235,922.0` |
| Overhaul v13 | `11,597.0` | `235,922.0` |
| Overhaul v14 | `12,076.0` | `235,922.0` |
| Overhaul v22 | `12,368.0` | `235,922.0` |

`worse + q=0.35`:

| Strategy | `ASH_COATED_OSMIUM` | `INTARIAN_PEPPER_ROOT` |
| --- | ---: | ---: |
| Overhaul v10 | `23,316.0` | `237,449.0` |
| Overhaul v14 | `25,155.0` | `237,449.0` |
| Overhaul v22 | `25,921.0` | `237,449.0` |

## Targeted Ablations

### `v10` Ash sleeve vs `v13`

- Same Pepper engine.
- New ingredient:
  - tighter Ash take thresholds,
  - tighter Ash passive quotes,
  - modestly larger Ash capacity.

Result:
- `v13` beats `v10` in all required modes.

### `v13` vs `v14`

- Same Pepper engine.
- Same Ash strategic family.
- `v14` pushes the Ash execution upgrade slightly further:
  - tighter take edge again,
  - slightly tighter first quote,
  - slightly larger Ash sizing and cap.

Result:
- `v14` beats `v13` again in all required modes.

### `v12` rejection

- `v12` attempted a more complex Ash signal-state redesign.
- Result:
  - default fell to `280,326.0`,
  - so the branch was rejected before stress expansion.

### `v15` rejection

- `v15` tested the deep-report idea of a safe-regime Ash directional skew.
- Result:
  - default `286,851.0`,
  - still below `v14`,
  - so the added directional complexity was rejected.

### `v16` near-tie

- `v16` tested the deep-report idea of a Pepper recycle–reacquire state.
- Result:
  - default `286,963.0`,
  - only `8` below `v14`,
  - Pepper changed slightly but not enough to move the frontier.

### `v17` validation

- `v17` changed only Ash passive quote placement.
- Result:
  - default `287,714.0`,
  - `worse` `287,714.0`,
  - `none` unchanged at `247,998.0`,
  - `worse + q=0.35` `262,803.0`.

Interpretation:
- Better Ash quoting alone was real, but it did not yet improve aggressive Ash monetization.

### `v20` validation

- `v20` changed the Ash clear reference from the hard anchor toward current fair.
- Result:
  - default `287,940.0`.

Interpretation:
- Inventory recycling against current fair was the next real Ash bottleneck.

### `v21` validation

- `v21` combined fair-based Ash clearing with stronger wide-spread Ash sizing.
- Result:
  - default `287,993.0`,
  - `worse` `287,993.0`,
  - `none` `248,108.0`,
  - `worse + q=0.35` `263,032.0`.

Interpretation:
- Quote quality and capacity release both mattered.
- This was the first branch to beat `v14` in every required mode by a clearly non-trivial margin.

### `v22` validation

- `v22` pushes the same Ash execution stack one step further:
  - clear large Ash inventory directly against current fair.
- Result:
  - default `288,401.0`,
  - `worse` `288,401.0`,
  - `none` `248,290.0`,
  - `worse + q=0.35` `263,370.0`.

Interpretation:
- `v22` is the new best local frontier.
- Pepper remains unchanged.
- All uplift over `v14` is Ash:
  - default `+1,430.0`,
  - `none` `+292.0`,
  - `worse + q=0.35` `+766.0`.

## Artifact-Backed Diagnosis

### Why `v22` improvement is real

- Pepper is unchanged:
  - same Pepper totals as `v14` in every tested mode.
- All gain is Ash:
  - default `+1,430.0`,
  - `worse` `+1,485.0`,
  - `none` `+292.0`,
  - `worse + q=0.35` `+766.0`.
- Ash own-trade activity increases further:
  - `v14`: `795` Ash buys / `764` Ash sells
  - `v22`: `824` Ash buys / `794` Ash sells
- `none`-mode Ash own-trade activity also increases:
  - `v14`: `306` Ash buys / `273` Ash sells
  - `v22`: `339` Ash buys / `299` Ash sells

Interpretation:
- `v22` is not winning on a bookkeeping artifact.
- It is converting more real Ash opportunities into executed trades, including under stricter matching.

### Day-by-day Ash improvement versus `v14`

`v14` default Ash:
- day `-2`: `15,390.0`
- day `-1`: `17,655.0`
- day `0`: `15,768.0`

`v22` default Ash:
- day `-2`: `15,710.0`
- day `-1`: `18,319.0`
- day `0`: `16,214.0`

Interpretation:
- The gain is distributed across all local days, not one lucky slice.

## Validation Decision

**SHIP `round1_overhaul_v22.py`**

Reason:
- It materially improves on `v14` in default, `worse`, `none`, and queue stress.
- The gain comes from a cleaner Ash execution and recycling stack rather than from more Pepper curve fitting.
- It is the strongest current Round 1 strategy on the local validation surface while remaining explainable and attributable.

Caveat:
- Pepper still dominates total PnL.
- The local sample is still small, so official generalization remains unproven.
- The strongest unshipped report-driven continuation is still a more official-oriented Pepper regularization branch, not a more complex local-only branch.
