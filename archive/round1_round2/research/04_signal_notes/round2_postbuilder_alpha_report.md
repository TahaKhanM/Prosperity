# Round 2 Post-Builder Alpha Report

Date: 2026-04-19

Scope: second-wave Round 2 alpha research after the first builder loop failed
to beat the named baseline on the current explicit local surface.

Key references:

- [round2_postbuilder_feedback_audit.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_postbuilder_feedback_audit.md)
- [round2_validation_surface_audit.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_validation_surface_audit.md)
- [round2_alpha_registry.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_alpha_registry.md)
- [round2_postbuilder_behavior_summary.csv](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_postbuilder_behavior_summary.csv)

## Short Read

The first-wave research mostly got the Round 2 signal picture right.
What it underweighted was:

- how much the local baseline already saturates simple Pepper carry
- how much Pepper monetization depends on stateful carry management rather than
  only a better fair model
- how incomplete the current local surface is for quote-intensive or MAF-like
  ideas

This means the main open problem is now closer to `missing monetization shell`
plus `validation-surface mismatch` than to `missing raw predictor`.

## What The First Wave Got Right

### Pepper

- Pepper is still the main Round 2 product.
- the moving-fair residual stack is real
- `z20`, fair residuals, and reversion around a drifting fair remain the core
  predictor family

### Ash

- Ash remains a stable anchored-fair product
- Ash still looks execution-limited, not signal-limited
- Ash complexity should remain narrow and execution-focused

## What The First Wave Missed Or Underweighted

### 1. The baseline is a Pepper monetization shell, not just a bad fair model

The local baseline does not win because it has a mysterious better predictor.
It wins because it:

- stays very close to the long Pepper limit
- recycles only in selected states
- uses late, not early, Pepper recycle behavior
- appears to protect harvested gains before refilling

That is a monetization family, not just a fair-value family.

### 2. The current local objective is too narrow

On the explicit local `-1/0/1` surface:

- Pepper carry is already close to saturated
- the `>10%` threshold is not a realistic local discriminator anymore
- quote-quality or extra-flow-sensitive ideas can be misranked

This does not mean the local surface is useless.
It means it should stop being the only ranking objective.

### 3. Pepper ideas were still too “same trade, different thresholds”

The failed branch mostly stayed inside this family:

- dynamic fair
- residual / z-score Pepper entries
- lighter or heavier soft-cap behavior

That is still the same basic trade if it does not preserve the high-carry
baseline shell.

### 4. Ash remaining EV is mostly execution-state mapping

Ash is not the main route to a breakout, but it still contains small transfer
shaped execution overlays:

- medium/wide-spread taker suppression
- passive-inside state placement

These are narrow, real, and easy to underweight if all attention stays on
Pepper.

## Most Promising Remaining Alphas

### High priority

1. `R2-PEPPER-regime-conditioned-carry-shell`
   - reason: likely the most important missed family
   - not redundant with `v01` / `v02`, which mostly rewrote fair logic

2. `R2-PEPPER-harvest-refill-guard`
   - reason: preserves realized recycle gains and looks distinct from broad
     soft-cap behavior

3. `R2-PEPPER-late-cap-streak-recycle`
   - reason: gives Pepper a way to monetize rich states without abandoning the
     main carry trade

### Medium priority

4. `R2-PEPPER-flow-conditioned-target`
   - reason: candidate used flow too lightly; baseline-like monetization seems
     to move target inventory with state

5. `R2-PEPPER-quote-side-noquote-gate`
   - reason: likely part of the remaining EV, but ranking is blocked by surface
     mismatch

6. `R2-ASH-medium-spread-taker-suppression`
   - reason: small but transfer-shaped Ash donor family

### Lower priority but still live

7. `R2-ASH-passive-inside-placement`
8. `R2-MAF-extra-flow-convexity`
9. `R2-PEPPER-spike-fade`

## What Should Be Downgraded

### Downgrade hard

- broad early Pepper soft-cap flattening
- generic “replace baseline Pepper with a better fair model”
- another pure Pepper threshold sweep inside the same residual family

### Keep only as helpers

- Ash quote-state overlay
- Pepper spike fade

### Reject cleanly

- exact Pepper session hardcoding
- standalone OFI in either product

## Is The Main Problem Missing Alpha Or Missing Monetization?

Mostly missing monetization.

More precise read:

- the underlying Pepper predictor stack still looks valid
- the current builder branch failed to realize it in a shell that can outscore
  the local baseline
- the default local surface then made that problem look more like a raw alpha
  failure than it actually is

So the blocker is not `Pepper has no alpha`.
The blocker is `the next distinct edge is in shell design, quote discipline, and
Round 2-specific ranking, not in another generic Pepper fair rewrite`.

## Analyzer / Tooling Read

No analyzer changes were necessary for this pass.

Reason:

- the existing analyzer already answered the signal and carryover questions
- the post-builder question was mainly about monetization and validation
  surface
- the needed evidence came from existing run diagnostics and strategy-builder
  artifacts

## Final Read

The next builder cycle should start from:

- Pepper shell design
- not another Pepper fair-model rewrite

And the next research cycle should start from:

- validation-surface redesign for Round 2-specific ideas
- not another broad alpha rediscovery pass

## 2026-04-19 Fresh-Alpha Follow-Up

Fresh artifact analysis after the builder loop added two genuinely orthogonal
Pepper ideas:

1. `R2-PEPPER-opening-wide-spread-take-gate`
   - evidence: early opening Pepper aggressive buys with `target_long=45` and
     spread `12+` were consistently negative over `20` ticks
   - implementation result:
     [round2_pepper_opening_wide_gate_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_opening_wide_gate_v01.py)
     lost `-2321.0`
   - read: the donor bucket is real, but it is too entangled with baseline
     carry accumulation to monetize as a standalone local branch

2. `R2-PEPPER-gap-state-guard`
   - evidence: Pepper empty-book windows are a real drawdown pocket in local
     artifacts
   - implementation result:
     [round2_pepper_gap_state_guard_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_gap_state_guard_v01.py)
     reached `-23.0`, while the properly narrowed
     [round2_pepper_gap_state_guard_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_gap_state_guard_v02.py)
     matched baseline exactly
   - read: this looks more like a robustness / hosted-transfer family than an
     additive local final-PnL family

Implication:

- the local strategy frontier is now exhausted enough that more local-only
  threshold or state retunes are lower EV than improving the Round 2 ranking
  surface itself
