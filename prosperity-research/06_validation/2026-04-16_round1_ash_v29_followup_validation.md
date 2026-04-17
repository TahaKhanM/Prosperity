# Round 1 Ash Follow-Up Validation - 2026-04-16

## Baseline

- Baseline trader:
  - [`round1_pepper_dual_carry_v29.py`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py)
- Round 1 dataset:
  - `prosperity_rust_backtester/datasets/round1/`
- Baseline local Ash contribution:
  - `default`: `55231.0`
  - `worse`: `55174.0`
  - `queue05`: `34387.5`
  - `none`: `13569.0`

## Diagnosis used for the search

- Official Round 1 facts remained unchanged: products are `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`, both with limit `80`.
- The Ash search was run on top of `v29` with Pepper unchanged in every candidate.
- Dominant open question: why the current Ash leg remains only around the low `3.2k` range on hosted logs while stronger hosted comparators are closer to the mid `3.5k` range.
- Working hypothesis at the start:
  - the remaining Ash gap was more likely in execution translation than in a missing brand-new fair-value model.

## Serious Ash candidates attempted

### 1. `v31`: asymmetric regime-gated inside quoting

- File:
  - [`round1_pepper_dual_carry_v31.py`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v31.py)
- Family:
  - quote-worthiness / inside-quote gating
- Mechanism:
  - make inside buys slightly more permissive and inside sells stricter in calm states
- Result vs `v29`:
  - `default`: `-275.0`
  - `worse`: `-173.0`
  - `queue05`: `-167.0`
  - `none`: `0.0`
- Verdict:
  - reject

### 2. `v32`: calmer passive quote fair

- File:
  - [`round1_pepper_dual_carry_v32.py`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v32.py)
- Family:
  - passive quote reference / fair-value translation
- Mechanism:
  - keep take fair unchanged, but anchor passive quote fair more heavily
- Result vs `v29`:
  - `default`: `-42.0`
  - `worse`: `-107.0`
  - `queue05`: `+11.0`
  - `none`: `0.0`
- Verdict:
  - near miss, but not promotable

### 3. `v33`: anchored reversal take-edge surface

- File:
  - [`round1_pepper_dual_carry_v33.py`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v33.py)
- Family:
  - selective aggression / maker-taker balance
- Mechanism:
  - lower Ash take thresholds only in anchored reversal states
- Result vs `v29`:
  - `default`: `-492.0`
  - `worse`: `-592.0`
  - `queue05`: `-284.0`
  - `none`: `+42.0`
- Verdict:
  - reject

### 4. `v34`: calm wide-book first-layer size expansion

- File:
  - [`round1_pepper_dual_carry_v34.py`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v34.py)
- Family:
  - passive size / quote capacity
- Mechanism:
  - increase first-layer Ash quote size in calm wide states
- Result vs `v29`:
  - identical in all benchmark modes
- Verdict:
  - effective no-op on the validation surface

### 5. `v35`: `v22` Ash stack on top of `v29` Pepper

- File:
  - [`round1_pepper_dual_carry_v35.py`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v35.py)
- Family:
  - hosted-informed legacy hybrid
- Mechanism:
  - replace current Ash leg with the older `v22`-style Ash execution stack
- Result vs `v29`:
  - `default`: `-4988.0`
  - `worse`: `-4931.0`
  - `queue05`: `-2796.0`
  - `none`: `-1201.0`
- Verdict:
  - hard reject

### 6. `v36`: earlier inside sells in calm spread-14 states

- File:
  - [`round1_pepper_dual_carry_v36.py`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v36.py)
- Family:
  - passive price selection
- Mechanism:
  - allow inside sells one tick earlier in calm spread-14 states
- Result vs `v29`:
  - identical in all benchmark modes
- Verdict:
  - effective no-op on the validation surface

### 7. `v37`: milder Ash recycle target

- File:
  - [`round1_pepper_dual_carry_v37.py`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v37.py)
- Family:
  - inventory control / recycler timing
- Mechanism:
  - relax Ash recycle target to avoid monetizing too quickly after entry
- Result vs `v29`:
  - `default`: `-84.0`
  - `worse`: `+6.0`
  - `queue05`: `-200.0`
  - `none`: `-69.5`
- Verdict:
  - reject

## What worked and what failed

What worked:
- Nothing in this follow-up search beat `v29` on Ash with a promotable, transfer-aware profile.

What failed:
- Stricter inside gating hurt Ash immediately.
- Calmer quote fair was the closest near miss, but still regressed `default` and `worse`.
- Selective take-surface changes improved `none` a little in one variant but damaged the main robust surface too much.
- The old `v22` Ash stack is now stale relative to the current `v29` Ash baseline.
- Two passive-capture ideas were literal no-ops, which suggests the current `v29` logic already saturates those simple state slices.

## Judgement

- No new candidate is clearly or materially better than `v29` on Ash.
- The credible shallow Ash search space now looks mostly exhausted:
  - inside-threshold tweaks,
  - passive size tweaks,
  - calmer quote fair,
  - mild take residuals,
  - legacy hosted-stack rollback,
  - and milder recycling.
- The remaining live bottleneck is likely not another small hand-tuned rule.
- The next informative step would need deeper Ash-specific instrumentation:
  - explicit candidate-quote logging,
  - quote EV labeling,
  - and state-cluster analysis aligned to hosted/local disagreement.

## Commands used

```bash
cd /Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v31.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v32.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v33.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v34.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v35.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v36.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --dataset round1 --json
python3 scripts/round1_benchmark.py --trader traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v37.py --compare traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py --dataset round1 --json
```
