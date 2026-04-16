# Round 1 Ash Validation Report

Date: 2026-04-16

Scope:
- product: `ASH_COATED_OSMIUM` only
- local baseline: [round1_pepper_dual_carry_v29.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py)
- hosted evidence bundle: [177116](/Users/tahakhan/Documents/Work/Projects/Prosperity/IMC Backtester Official Logs/177116)

Verified official facts:
- Round 1 products are `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`.
- Both product limits are `80`.
- Continuous-book submission syntax is the standard `Trader.run(self, state)` interface returning `(result, conversions, traderData)`.

Important source boundary:
- hosted `177116.py` is byte-for-byte identical to the local `v29` Ash baseline, so it is valid hosted execution evidence for the exact current Ash logic.
- the user-provided “other teams around 3.5k official Ash-only” target is treated here as an external, unverified benchmark claim, not an official repo fact.

## Independent Diagnosis

The current Ash bottleneck is not “the 10000 anchor is wrong” and not “passive inside quoting is broadly bad.”

The strongest independently re-derived findings were:

- passive inside Ash fills are good on both hosted and local evidence
- the cleanest donor bucket is medium-spread aggressive action quality
- local and hosted both show Ash sell-side `take_b1` at spread `10` is bad
- local also shows buy-side `take_a1` becomes weak to negative in medium spreads
- the only family that improved Ash robustly in this pass was spread-conditioned taker and recycler suppression
- that family improved conservative modes more than optimistic ones, which makes it transfer-shaped
- but the size of the gain remained modest

## Hosted Reference

Hosted `177116` Ash result:
- official hosted Ash PnL: `3205.5`

Hosted `177116` execution facts used in this pass:
- passive inside buy and passive inside sell are both positive
- narrow takers are acceptable
- `take_b1` at spread `10` is negative

Interpretation:
- the hosted trace supports tactical suppression of bad medium-spread takers
- it does not support broad passive suppression

## Serious Candidates Tested

### First Ash batch

| Variant | Family | Ash delta `default` | Ash delta `worse` | Ash delta `queue05` | Ash delta `none` | Verdict |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `v38` | earlier flatten-only sell regime | `-789.0` | `-789.0` | `-556.0` | `-15.0` | reject |
| `v39` | anchor-maker plus hard-gated spike-fade rewrite | `-3859.0` | `-3881.0` | `-2964.0` | `-2370.0` | reject |
| `v40` | passive-buy suppression in long-rich states | `-864.0` | `-832.0` | `-569.0` | `0.0` | reject |

### Medium-spread taker-gate family

| Variant | Family | Ash delta `default` | Ash delta `worse` | Ash delta `queue05` | Ash delta `none` | Verdict |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `v41` | medium-spread taker gate | `+58.0` | `+33.0` | `+31.0` | `+64.0` | near miss |
| `v42` | `v41` plus tighter long sell-clear guard | `+62.0` | `+46.0` | `+40.0` | `+74.0` | near miss |
| `v43` | harder spread `10-13` aggressive-action gate | `-41.0` | `-14.0` | `+63.0` | `+103.0` | reject |
| `v44` | asymmetric spread gate, buy `9-13`, sell `10-13` | `+33.0` | `+101.0` | `+123.0` | `+156.0` | best near miss |

### Anchor-extreme passive fade family

| Variant | Family | Ash delta `default` | Ash delta `worse` | Ash delta `queue05` | Ash delta `none` | Verdict |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `v45` | one-sided anchor-extreme passive fade regime | `-384.0` | `-337.0` | `-115.0` | `+156.0` | reject |
| `v46` | `v45` plus fade-side second passive layer | `-384.0` | `-337.0` | `-115.0` | `+156.0` | reject |

## Best New Branch

Best new Ash branch from this pass:
- [round1_pepper_dual_carry_v44.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v44.py)

`v44` versus `v29`:
- `default`: total `+33.0`, Ash `+33.0`
- `worse`: total `+101.0`, Ash `+101.0`
- `queue05`: total `+123.0`, Ash `+123.0`
- `none`: total `+156.0`, Ash `+156.0`
- robust score delta: `+203.25`

Trade-count shape:
- `default` own-trade count: `2977` vs `3007`
- `queue05` own-trade count: `2903` vs `2927`
- `none` own-trade count: `1410` vs `1424`

Interpretation:
- `v44` improves Ash while trading less
- the gain is largest in `none` and `queue05`
- this is exactly the right direction for transfer-aware Ash work
- but the magnitude is still too small to call a clear or material improvement over `v29`

## What Worked

The only family that consistently worked was tactical taker cleanup:

- suppress bad Ash aggressive actions in medium spreads
- especially suppress sell-side bid-hit recycling in spreads `10` to `13`
- leave the good wide passive inside capture mostly untouched

Why it worked:
- local and hosted evidence both pointed at the same donor bucket
- the family improved conservative modes more than optimistic modes
- the best branch also lowered turnover

## What Failed

Broad regime rewrites failed:
- `v38`
- `v39`
- `v40`

Anchor-extreme passive fade overlays failed once they went beyond the taker cleanup:
- `v45`
- `v46`

Why they failed:
- they either removed too much still-good Ash activity
- or they leaned further into passive fills that did not hold up outside the optimistic surface

The fade-side second-layer extension is specifically not supported by current evidence.

## Remaining Bottleneck

The remaining Ash bottleneck is now narrow:

- not a missing anchor
- not a missing simple fair tweak
- not a missing generic passive layer

It is an action-state mapping gap:

- which medium-spread states should be `hold`
- which should still be `take`
- which should become one-sided passive fade states

The current hand-built rules are good enough to produce small transfer-shaped wins, but not good enough to produce a material breakout.

## Validation Commands Used

Grounding and hosted-log analysis:

```bash
python3 prosperity_rust_backtester/scripts/analyze_official_logs.py "IMC Backtester Official Logs/177116" --replay-trader prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --export-dir prosperity-research/official_log_analysis_current --json
python3 prosperity_rust_backtester/scripts/ash_deep_analysis.py
python3 prosperity_rust_backtester/scripts/round1_exact_control.py --product ASH_COATED_OSMIUM --json
```

Ash-only benchmark commands from this pass:

```bash
cd /Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v38.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v39.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v40.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v41.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v42.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v43.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v44.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v45.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v46.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --dataset round1 --json
```

Direct reruns used when the benchmark script hit concurrent-lock noise:

```bash
./scripts/cargo_local.sh run -- --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v43.py --dataset round1 --run-id debug-v43-worse-20260416 --output-root runs --artifact-mode none --flat --products off --trade-match-mode worse
./scripts/cargo_local.sh run -- --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v44.py --dataset round1 --run-id debug-v44-worse-20260416 --output-root runs --artifact-mode none --flat --products off --trade-match-mode worse
```

## Validator Verdict

- **SHIP**: no new Ash variant from this pass
- **REJECT replacing `v29`**: yes
- **Keep as strongest research branch**: `v44`

Reason:
- `v44` is a real, transfer-shaped improvement
- but it is not materially better than `v29`
- the remaining accessible hand-engineered Ash space now looks incremental

## Next Most Informative Experiment

If Ash work continues, the next pass should not be another generic threshold sweep.

The next most informative experiment is:

- exact-control or near-oracle Ash action-trace distillation focused only on the medium-spread regime
- compare `v29` or `v44` actions against exact-control labels
- then implement a residual controller only in the high-disagreement states

That is the narrowest unresolved bottleneck now supported by the evidence.
