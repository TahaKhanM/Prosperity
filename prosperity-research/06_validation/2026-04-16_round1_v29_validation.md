# Round 1 Phase 2 Validation: `v29`

Date: 2026-04-16

## Best new strategy

- `prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py`

## Best comparison vs `v23`

Baseline:
- `traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v23.py`

Result:
- `default`: `297347.0` vs `297007.0` (`+340.0`)
- `worse`: `297290.0` vs `296950.0` (`+340.0`)
- `queue05`: `275088.5` vs `274572.5` (`+516.0`)
- `none`: `250540.5` vs `250362.5` (`+178.0`)
- robust score: `628933.625` vs `628117.625` (`+816.0`)

Interpretation:
- This is a clean non-regressing improvement over `v23`.
- The gain is more transfer-shaped than a default-only win because the biggest delta is in `queue05`, and `none` also improves.

## Useful anchor comparison vs `v13`

Anchor:
- `traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v13.py`

Result:
- `default`: `+1445.0`
- `worse`: `+1445.0`
- `queue05`: `+1513.0`
- `none`: `+755.5`
- robust score delta: `+2957.5`

## Candidate ranking from this run

1. `round1_pepper_dual_carry_v29.py`
   - family: `v28` spread-intention gate + conservative stalled-book recycle timing
   - verdict: promote
2. `round1_pepper_dual_carry_v28.py`
   - family: Pepper spread-intention / stalled-book gate
   - verdict: strong winner and main mechanism discovery
3. `round1_pepper_dual_carry_v25.py`
   - family: Pepper high-inventory buy hazard / policy-over-policy gate
   - verdict: real winner, weaker than `v28` and `v29`
4. `round1_pepper_dual_carry_v24.py`
   - family: first narrow Pepper buy hazard gate
   - verdict: small but real winner
5. `round1_pepper_dual_carry_v30.py`
   - family: top-3 depth-shape / ask-heavy wall-state gate
   - verdict: near miss; tiny score gain over `v29` but slight `queue05` regression
6. `round1_pepper_dual_carry_v26.py`
   - family: delayed replenishment / buy cooldown after sells
   - verdict: near miss; helped `none` and `queue05`, hurt `default`
7. `round1_pepper_dual_carry_v27.py`
   - family: narrowed cooldown residual
   - verdict: functionally identical to `v25`; too narrow to matter

## What worked

- The winning family was not another fair-value tweak.
- The best gains came from identifying a specific Pepper donor state:
  - already long,
  - wide spread,
  - wide book stale or weakening,
  - buy-side execution still firing too eagerly.
- `v28` converted that into a spread-intention gate using one-step symbolic state:
  - ask not lifting,
  - bid not strengthening,
  - wide book,
  - high inventory.
- `v29` then improved the same state by nudging recycle timing earlier without giving back the conservative-mode gains.

## What failed

- Delayed replenishment as a broad cooldown (`v26`) was too blunt.
- The very narrow cooldown residual (`v27`) added nothing once constrained to the exact state.
- Top-3 ask-heavy depth shape (`v30`) was informative, but adding it on top of `v29` slightly weakened `queue05`; that makes it a near miss, not a ship candidate.

## Artifact read on `v29` vs `v23`

Persisted runs:
- `prosperity_rust_backtester/runs/persist-v23-default-20260416/`
- `prosperity_rust_backtester/runs/persist-v29-default-20260416/`

Pepper changes:
- day `0`: PnL `81583.0` vs `81612.0` (`-29.0`), but `ge78` drops `5434` vs `5662`
- day `1`: PnL `81122.0` vs `81083.0` (`+39.0`), and `ge78` drops `5967` vs `6152`
- day `2`: PnL `79411.0` vs `79081.0` (`+330.0`), and `ge78` drops `7664` vs `8091`

Pepper activity changes:
- day `2` buy quantity falls `1027` vs `1090`
- day `2` sell quantity falls `947` vs `1010`
- day `2` Pepper trade count falls `387` vs `414`

Target donor bucket:
- definition: Pepper aggressive buys with `position >= 76`, `spread >= 12`, and stalled / weakening top book
- `v23`: quantity `824`, count `156`, horizon-10 edge sum `-102679.0`
- `v29`: quantity `674`, count `111`, horizon-10 edge sum `-102059.5`

Interpretation:
- The bucket is still negative, but `v29` cuts it materially while also reducing time spent very long.
- That is the mechanism most consistent with the benchmark lift.

## Families status after this run

Alive:
- Pepper quote-worthiness / hazard gating
- Pepper spread-intention / leaning-state gating
- Pepper stalled-book recycle timing

Near-alive but not yet shippable:
- delayed replenishment after sells
- top-3 depth-shape / ask-heavy wall-state gating

Not exhausted:
- richer quote-worthiness logging with explicit per-quote EV labels on top of `v29`
- symbolic short-sequence mining beyond the current one-step stalled-book motif
- exact-control residuals only inside the remaining `v29` donor states

## Exact commands used

```bash
cd /Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v24.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v23.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v25.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v23.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v26.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v23.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v28.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v23.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v28.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v30.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v23.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v13.py --dataset round1 --json
./scripts/cargo_local.sh run -- --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v24.py --dataset round1 --run-id persist-v24-default-20260416 --output-root runs --persist --flat --products summary
./scripts/cargo_local.sh run -- --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v25.py --dataset round1 --run-id persist-v25-default-20260416 --output-root runs --persist --flat --products summary
./scripts/cargo_local.sh run -- --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v28.py --dataset round1 --run-id persist-v28-default-20260416 --output-root runs --persist --flat --products summary
./scripts/cargo_local.sh run -- --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --dataset round1 --run-id persist-v29-default-20260416 --output-root runs --persist --flat --products summary
```
