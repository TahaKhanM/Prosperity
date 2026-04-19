# Round 2 Post-Builder Feedback Audit

Date: 2026-04-19

Scope: audit what the strategy-builder Round 2 loop actually tested, what the
results prove, what they do not prove, and which conclusions should now be
considered stale.

Key evidence:

- [round2_strategy_build_plan.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/round2_strategy_build_plan.md)
- [round2_validation_surface.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/round2_validation_surface.md)
- [round2_baseline_snapshot.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/round2_baseline_snapshot.md)
- [current_candidate_note.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/current_candidate_note.md)
- [current_diagnosis_packet.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/current_diagnosis_packet.md)
- [round2_blocker_report.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/round2_blocker_report.md)
- [round2_postbuilder_behavior_summary.csv](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_postbuilder_behavior_summary.csv)
- [baseline.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round%202/baseline.py)
- [round2_pepper_dynamic_fair_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_dynamic_fair_v01.py)
- [round2_pepper_dynamic_fair_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_dynamic_fair_v02.py)

## What The Builder Tested

The implementation loop was narrower than “test all Round 2 alpha families.”
It tested one specific branch:

- fixed baseline: [baseline.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round%202/baseline.py)
- changed sleeve: Pepper only
- unchanged sleeve: Ash only
- candidate family: dynamic-fair Pepper residual mean reversion plus inventory
  retuning
- validation surface: explicit non-carry Rust day runs for day `-1`, `0`, and
  `1`, aggregated

That makes the observed delta highly attributable:

- the loop did test whether a Pepper dynamic-fair replacement sleeve can beat
  the local baseline
- the loop did not test whether a different Pepper monetization shell, an Ash
  execution overlay, or a MAF-sensitive strategy would rank better

## Headline Attribution

| Variant | Total PnL | Baseline PnL | Delta | Pepper-only? | Main change from previous |
| --- | ---: | ---: | ---: | --- | --- |
| `v01` | `300930.5` | `310101.5` | `-9171.0` | yes | first dynamic-fair Pepper rewrite with softer carry |
| `v02` | `306097.5` | `310101.5` | `-4004.0` | yes | moved Pepper inventory back toward the baseline carry shell |

Interpretation:

- `v02` recovered `5167.0` of the `v01` loss without changing Ash.
- the entire remaining gap is still in Pepper.
- the strongest effect of the retune was not “better signal,” but “closer
  Pepper inventory shape.”

## Per-Day Monetization Read

The clearest evidence is in the variant/day comparison table:
[round2_postbuilder_behavior_summary.csv](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_postbuilder_behavior_summary.csv)

Condensed read:

- `v01` and `v02` both traded more aggressive Pepper quantity than baseline on
  all three days.
- `v02` often improved local aggressive or passive `edge_h5_avg` versus
  baseline, but still lost PnL because it held less Pepper inventory.
- the baseline keeps Pepper near the official `80` limit for about `94%` of
  each day; `v02` drops that to roughly `89% / 81% / 79%` on day `-1/0/1`.

Most revealing row:

| Variant | Day | Delta | Aggressive edge h5 | Passive edge h5 | Pepper avg abs pos | Pepper near-limit |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `v01` | `0` | `-4188.0` | `2.3064` vs `1.3688` | `7.2831` vs `7.2448` | `67.3959` vs `77.4326` | `45.07%` vs `94.58%` |
| `v02` | `0` | `-866.0` | `1.9419` vs `1.3688` | `7.4550` vs `7.2448` | `74.7199` vs `77.4326` | `81.04%` vs `94.58%` |

This is not the signature of a pure alpha collapse.
It is the signature of a local surface that rewards carrying closer to the long
limit more than it rewards cleaner Pepper selection.

## Failure-Mode Classification

| Question | Classification | Confidence | Why |
| --- | --- | --- | --- |
| Was this mainly an alpha failure? | no | medium-high | Pepper structural signals remain strong in the analyzer and `v02` recovered most of `v01` simply by restoring carry shape |
| Was this mainly a monetization failure? | yes | high | the winning local baseline monetizes Pepper by staying near max long and recycling selectively |
| Was there an inventory-shape mismatch? | yes | high | candidate inventory moved materially below baseline on all three days |
| Was the current validation surface part of the blocker? | yes | medium-high | the surface is base-stream only, ignores `bid()`, and is heavily carry-saturated |
| Has the local baseline saturated the obvious Pepper carry trade? | yes, locally | high | remaining official-limit carry headroom is too small to explain a real `>10%` local win |
| Was there a hidden execution-effect miss? | likely | medium | baseline Pepper is a state machine with late recycle, refill guard, and carry-completion logic; the candidate mostly replaced fair logic instead of preserving those monetization details |

## What The Builder Actually Proved

1. A Pepper dynamic-fair replacement sleeve does not beat the named baseline on
   the explicit local `-1/0/1` non-carry surface.
2. The local score is dominated by Pepper carry shape more than by the
   candidate’s selection logic.
3. Early broad Pepper soft-cap behavior is locally anti-score.
4. Ash was not the cause of the current failure.

## What The Builder Did Not Prove

1. It did not falsify the Pepper residual mean-reversion thesis.
2. It did not prove that Round 2 has no remaining alpha.
3. It did not prove that a quote-quality or state-gated Pepper shell cannot
   beat the baseline.
4. It did not test MAF or extra-flow value at all.
5. It did not prove hosted ranking, because the local surface uses fixed raw
   days with optimistic matching and no extra market access.

## Mistaken Conclusions To Avoid

Do not conclude:

- “Pepper dynamic fair is false.”
  The better conclusion is: it is not a superior local monetization shell when
  it gives up too much carry.

- “More Pepper signal complexity is the next obvious move.”
  Current evidence says the next frontier is monetization and state logic, not
  another fair-model rewrite.

- “Ash is irrelevant.”
  Ash is not the main source of a `>10%` local breakout, but it still contains
  small execution overlays that may transfer better than another Pepper
  threshold sweep.

- “The current local surface is the right final ranking objective.”
  It is useful for attribution and safety, but incomplete for Round 2-specific
  ranking.

## Audit Verdict

The builder loop mostly established a local `Pepper monetization and
inventory-shape mismatch against a carry-saturated baseline`, not a broad
`Pepper alpha failure`.
