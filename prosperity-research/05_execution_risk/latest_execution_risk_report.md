# Round 1 Execution Risk Report

Date: 2026-04-14

Scope:
- baseline: `prosperity_rust_backtester/traders/round1_baseline_v1.py`
- lower-concentration fallback: `prosperity_rust_backtester/traders/round1_candidate_v2.py`
- prior ships:
  - `prosperity_rust_backtester/traders/round1_overhaul_v1.py`
  - `prosperity_rust_backtester/traders/round1_overhaul_v2.py`
- new redesigns:
  - `prosperity_rust_backtester/traders/round1_overhaul_v3.py`
  - `prosperity_rust_backtester/traders/round1_overhaul_v4.py`

## Bottom Line

- `round1_overhaul_v3.py` is the strongest local design under all tested fill settings.
- It is not an inventory-risk reduction versus `round1_overhaul_v1.py`.
- It is a more explicit competition-specific Pepper template exploit:
  - better score,
  - still strong under `worse`, `none`, and queue stress,
  - but even more committed to holding near-max-long Pepper.
- `round1_overhaul_v4.py` is strategically useful only as a falsification test.
  - It shows that slower Pepper acquisition with more reserve capacity gives up score in every tested mode.

## Score Under Fill Stress

| Strategy | default | `worse` | `none` | `worse + q=0.35` |
| --- | ---: | ---: | ---: | ---: |
| Baseline | `152,305.5` | `156,131.0` | `159,915.5` | n/a |
| Candidate v2 | `239,372.0` | `239,584.0` | `216,731.5` | `227,724.0` |
| Overhaul v1 | `276,821.0` | `276,835.0` | `241,552.0` | `254,590.0` |
| Overhaul v2 | `276,828.0` | `276,842.0` | `241,564.0` | `254,602.0` |
| Overhaul v3 | `282,373.0` | `282,340.0` | `245,303.0` | `259,507.0` |
| Overhaul v4 | `281,652.0` | `281,619.0` | `242,893.0` | `257,793.0` |

Interpretation:
- `v3` beats `v1` by `+5,552.0 / +5,505.0 / +3,751.0 / +4,917.0`.
- `v3` beats `candidate_v2` by `+43,001.0 / +42,756.0 / +28,571.5 / +31,783.0`.
- The edge survives stricter matching assumptions, so the redesign is not just harvesting optimistic passive fills.

## Inventory Concentration

### Pepper default-mode inventory

| Strategy | Avg abs pos | Time `|pos| >= 60` | Time `|pos| >= 70` | Max abs pos |
| --- | ---: | ---: | ---: | ---: |
| Candidate v2 | `58.66` | `45.58%` | `20.23%` | `80` |
| Overhaul v1 | `77.72` | `99.70%` | `99.64%` | `80` |
| Overhaul v2 | `77.71` | `99.65%` | `99.58%` | `80` |
| Overhaul v3 | `78.96` | `99.94%` | `99.94%` | `80` |
| Overhaul v4 | `77.65` | `97.68%` | `96.99%` | `80` |

### Pepper first large-position timestamps by day

| Strategy | First `|pos| >= 60` | First `|pos| >= 78` |
| --- | --- | --- |
| Candidate v2 | `[53100, 86600, 36900]` | n/a in the prior report set |
| Overhaul v1 | `[1900, 3900, 3200]` | n/a in the prior report set |
| Overhaul v3 | `[900, 200, 600]` | `[1000, 300, 900]` |
| Overhaul v4 | `[24500, 22600, 22500]` | `[38700, 35100, 28400]` |

Interpretation:
- `v3` is more concentrated than `v1`, not less.
- It reaches high Pepper size almost immediately and then stays there.
- `v4` proves that a slower-build reserve-capacity variant is feasible, but the bundle rewards it less.

## Trade Mix And Fill Realism

### Aggregate default-mode own-trade counts

| Strategy | Total trades | Take | Make |
| --- | ---: | ---: | ---: |
| Candidate v2 | `2355` | `1090` | `1265` |
| Overhaul v1 | `1421` | `400` | `1021` |
| Overhaul v2 | `1427` | `406` | `1021` |
| Overhaul v3 | `2079` | `1029` | `1050` |
| Overhaul v4 | `2083` | `1006` | `1077` |

Interpretation:
- `v1` looked like a very pure carry posture:
  - buy the Pepper long once,
  - keep it,
  - rely on mark-to-market drift.
- `v3` is different:
  - it still carries near-max-long Pepper,
  - but it also trades around the template fair more actively.
- This matters because the redesign is not only "reach the same max-long state earlier."
- It is "use a stronger generator hypothesis to both acquire and recycle around the position."

## Product-Level Risk Read

### Default-mode contribution

| Strategy | `ASH_COATED_OSMIUM` | `INTARIAN_PEPPER_ROOT` | Pepper share |
| --- | ---: | ---: | ---: |
| Candidate v2 | `38,318.0` | `201,054.0` | `84.0%` |
| Overhaul v1 | `45,608.0` | `231,213.0` | `83.5%` |
| Overhaul v3 | `45,608.0` | `236,765.0` | `83.8%` |
| Overhaul v4 | `45,608.0` | `236,044.0` | `83.8%` |

### `none`-mode contribution

| Strategy | `ASH_COATED_OSMIUM` | `INTARIAN_PEPPER_ROOT` | Pepper share |
| --- | ---: | ---: | ---: |
| Candidate v2 | `10,627.0` | `206,104.5` | `95.1%` |
| Overhaul v1 | `10,262.0` | `231,290.0` | `95.8%` |
| Overhaul v3 | `10,262.0` | `235,041.0` | `95.8%` |
| Overhaul v4 | `10,262.0` | `232,631.0` | `95.8%` |

Interpretation:
- Ash is steady and healthy, but it is not where the redesign wins.
- All meaningful uplift from `v3` is Pepper.
- The new ship decision therefore turns on whether the stronger Pepper generator story is convincing enough to justify the concentration.

## Generator-Specific Counterfactual

This was the most important execution-risk test in this iteration.

Question:
- If the Pepper edge is real, should a slower-build reserve-capacity version hold up?

Counterfactual:
- `round1_overhaul_v4.py` preserved the same template story but forced materially slower inventory build and more reserve capacity.

Result:
- `v4` still beat `v1` and `candidate_v2`.
- `v4` still lost to `v3` in every tested mode.

Risk implication:
- The local evidence supports faster template-aware ownership of Pepper.
- It does not reduce concentration risk.
- It does increase confidence that `v3` is exploiting a real bundle pattern instead of just a lucky threshold in `v1`.

## Main Remaining Risks

1. The entire redesign remains highly dependent on the Pepper session-template story persisting outside the local three-day bundle.
2. `v3` has almost no spare long capacity once the session starts.
3. If live Pepper stalls, gaps down, or becomes materially less monotone, `v3` will likely underperform `candidate_v2` faster than `v1` did.
4. The improved score does not come from diversification. It comes from stronger exploitation of the same product that already dominated the prior ship.

## Execution-Risk Verdict

- `round1_overhaul_v3.py` passes fill-stress validation.
- `round1_overhaul_v3.py` does not pass any "reduced concentration" test, because that is not what it is.
- The correct description is:
  - more explainable than `v1`,
  - more locally profitable than `v1`,
  - still a high-conviction competition-specific Pepper carry-and-recycle strategy.

Decision framing:
- If the objective is the strongest locally validated exploit of the observed Round 1 generator, prefer `v3`.
- If the objective is lower single-story dependence, keep `candidate_v2` as the operational fallback.
