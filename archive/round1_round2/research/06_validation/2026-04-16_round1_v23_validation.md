# Round 1 Validation Summary - 2026-04-16

## Verdict

SHIP the dynamic carry-target family, with the current best implementation at:

- `prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v23.py`

This is the strongest local Round 1 strategy found in this run.

## Benchmark comparison

Named baseline:
- `prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v13.py`

Fresh full-matrix comparison for `v23` vs `v13`:
- `default`: `297007.0` vs `295902.0` (`+1105.0`)
- `worse`: `296950.0` vs `295845.0` (`+1105.0`)
- `queue05`: `274572.5` vs `273575.5` (`+997.0`)
- `none`: `250362.5` vs `249785.0` (`+577.5`)
- robust score: `628117.625` vs `625976.125` (`+2141.5`)
- non-regression: `true`

Product contribution:
- Ash is unchanged.
- The entire gain comes from Pepper:
  - `v13` Pepper default: `240671.0`
  - `v23` Pepper default: `241776.0`

## Serious candidates attempted in this run

1. `round1_pepper_dual_carry_v23.py`
   - Dynamic carry-target surface, refined from `v22`
   - Best local result from this run
2. `round1_pepper_dual_carry_v22.py`
   - First dynamic carry-target surface
   - `default +863`, `queue05 +781`, `none +547.5`, robust `+1722.5`
3. `round1_pepper_dual_carry_v21.py`
   - Tight-spread exact-action overlay
   - Better `default`, but bad `none` and `queue05`; reject as fill-sensitive
4. `round1_pepper_dual_carry_v19.py`
   - Pepper leaning-state passive gate
   - Small negative vs baseline; reject
5. `round1_pepper_dual_carry_v20.py`
   - Pepper passive action-template overlay
   - Materially worse; reject

Strong prior near-miss retained for comparison:
- `trader_archive/Round1/research/round1_v13_pepper_recycle_overlay_v1.py`
  - robust delta vs `v13`: `+88.25`
  - still much weaker than `v22` and `v23`

## What worked

- The deep-report prior that Pepper is directionally right on carry but under-monetized tactically was correct.
- The productive mechanism was not another fair-value tweak or threshold sweep.
- The best improvement came from reclassifying Pepper inventory into better and worse carry states and trimming the target inventory surface as:
  - session progress increases,
  - remaining carry shrinks,
  - flow weakens,
  - residuals turn less favorable,
  - book pressure leans against the held inventory.
- The gain is credible because it survives `none` and `queue05`, not just optimistic default fills.

## What failed

- Leaning-state quote suppression alone (`v19`) did not beat the baseline.
- A more explicit passive action-template controller (`v20`) sharply underperformed.
- Tight-spread exact-action aggression (`v21`) improved default but hurt conservative modes enough to reject it.

## Artifact-level support

Persisted default artifacts:
- baseline: `prosperity_rust_backtester/runs/persist-v13-default-20260416/`
- best candidate: `prosperity_rust_backtester/runs/persist-v23-default-20260416/`

Observed Pepper behavior from persisted default bundles:
- `v23` improves Pepper PnL on all three days:
  - day `-2`: `79081.0` vs `78179.0`
  - day `-1`: `81083.0` vs `81070.0`
  - day `0`: `81612.0` vs `81422.0`
- `v23` does this with fewer Pepper trades on every day:
  - day `-2`: `414` vs `443`
  - day `-1`: `345` vs `362`
  - day `0`: `340` vs `355`
- `v23` also spends less time parked at `>=78` Pepper:
  - day `-2`: `8091` vs `8819`
  - day `-1`: `6152` vs `6371`
  - day `0`: `5662` vs `5937`

Interpretation:
- the dynamic target surface improves inventory monetization rather than merely increasing activity.

## Research-report ideas that were most productive

Most productive:
- Pepper dynamic carry-target plus recycler logic
- Execution residuals on top of the best current strategy

Informative but not shippable in this run:
- Pepper spread-intention / leaning-state control
- Pepper action-template / finite-state control
- Exact-control-inspired tactical overlays

## Significance statement

I did find a meaningful, well-supported local improvement over the current best robust baseline.

I did not find a breakout anywhere close to the original stretch target of `>5%` over the baseline.

The best defensible claim is:
- the dynamic carry-target family is materially better than the repo’s prior frontier,
- but the broader Round 1 search space still looks hard and incremental rather than explosively underexploited.

## Near-miss candidates worth future follow-up

- `round1_pepper_dual_carry_v21.py`
  - default looked good, but conservative-mode damage was too large
  - might still be useful as a gated submodule if its aggressive take logic is made more fill-robust
- `round1_v13_pepper_recycle_overlay_v1.py`
  - tiny but real prior improvement
  - could still combine with a later, stronger carry-target surface if rewritten submission-safe

## Exact commands used

Fresh baseline / comparison benchmarks:

```bash
cd /Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester
python3 scripts/round1_benchmark.py --trader trader_archive/Round1/research/round1_v13_pepper_recycle_overlay_v1.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v13.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v15.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v13.py --dataset round1 --json
```

Exact-control reference:

```bash
cd /Users/tahakhan/Documents/Work/Projects/Prosperity
python3 prosperity_rust_backtester/scripts/round1_exact_control.py --product INTARIAN_PEPPER_ROOT --days=-2,-1,0 --json
```

New-candidate benchmarks:

```bash
cd /Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v19.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v13.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v20.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v13.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v21.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v13.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v22.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v13.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v23.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v13.py --dataset round1 --json
```

Persisted artifact runs:

```bash
cd /Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester
./scripts/cargo_local.sh run -- --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v13.py --dataset round1 --run-id persist-v13-default-20260416 --output-root runs --persist --flat --products summary
./scripts/cargo_local.sh run -- --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v22.py --dataset round1 --run-id persist-v22-default-20260416 --output-root runs --persist --flat --products summary
./scripts/cargo_local.sh run -- --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v23.py --dataset round1 --run-id persist-v23-default-20260416 --output-root runs --persist --flat --products summary
```

## Next most informative experiment

If more time were available, the next best experiment would be:
- keep `v23` as the base,
- add a submission-safe version of the best recycle overlay logic only where the new target surface still leaves Pepper too sticky in moderately overheated states,
- require it to preserve the `none` and `queue05` gains from `v23`.
