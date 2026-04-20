# Current Diagnosis Packet

Date: 2026-04-19

Current candidate:
- [round2_pepper_quote_gate_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_quote_gate_v01.py)

Named baseline:
- [baseline.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round%202/baseline.py)

Validation surface:
- explicit non-carry Round 2 day runs on day `-1`, `0`, and `1`
- base comparison metric: summed total PnL across the three days

Supporting comparison evidence:
- full local branch sweep under the baseline shell:
  `quote_gate_sweep_01..12`
- refinement sweep around the winning parameter pocket:
  `quote_gate_refine_01..20`
- stricter benchmark surface for the winning temp branch:
  `default`, `worse`, `queue05`, and `none`

## Headline Result

- baseline total: `310101.5`
- current candidate total: `310426.5`
- delta vs baseline: `+325.0`
- delta vs baseline: `+0.10%`

Per-day deltas:

| Day | Candidate | Baseline | Delta |
| --- | ---: | ---: | ---: |
| `-1` | `102996.5` | `102962.5` | `+34.0` |
| `0` | `102751.0` | `102777.0` | `-26.0` |
| `1` | `104679.0` | `104362.0` | `+317.0` |

Product attribution:

| Product | Candidate | Baseline | Delta |
| --- | ---: | ---: | ---: |
| `ASH_COATED_OSMIUM` | `63652.0` | `63652.0` | `0.0` |
| `INTARIAN_PEPPER_ROOT` | `246774.5` | `246449.5` | `+325.0` |

## Dominant Read

Dominant read:
- the remaining additive local Pepper EV is in late rich-state quote
  participation, not in another fair-model rewrite

What changed mechanically:

- the candidate preserves the baseline carry shell
- it only suppresses passive Pepper rebids once already long and mildly rich
- it leaves taking logic and Ash unchanged

Why it worked:

- unlike the calm-execution branch, it does not globally reduce urgency
- unlike the carry-shell and gap-state branches, it creates a real stateful
  behavior change
- unlike the aggressive quote-gate variants, it does not collapse day `0`
  occupancy enough to lose the branch entirely

## Secondary Evidence

Available stricter local benchmark deltas versus baseline:

| Mode | Delta |
| --- | ---: |
| `default` | `+291.0` |
| `worse` | `+282.0` |
| `queue05` | `+64.0` |
| `none` | `0.0` |

Interpretation:

- the branch is not a pure optimistic-local artefact
- the edge decays as matching becomes harsher, which is consistent with the
  mechanism being a passive quote-quality overlay rather than a new predictor
- the `none` tie says the branch mostly works by removing bad passive re-entry,
  not by creating a stronger aggressive alpha

## Frontier Update

Superseded branches:

- `round2_pepper_gap_state_guard_v02.py` should not be treated as the current
  best branch anymore, especially with the user-reported official `-2.5%`
  result
- the older hard-blocker claim that the local frontier was fully exhausted is
  no longer correct after the quote-side gate branch produced a real positive
  delta

Current live family:

- `R2-PEPPER-quote-side-noquote-gate`

Current family status:

- real
- attributable
- still too small to satisfy the requested `>5%` target

## Next Action

- keep the quote-side gate as the active family
- patch only inside the same late-rich Pepper participation branch
- deprioritize broader calm-execution variants and local-only gap/carry-shell
  retunes until this family is exhausted
