# Round 1 Execution Risk Report

Date: 2026-04-14

Path note:
- trader files referenced below were written before the trader cleanup pass
- active trader files now live under `prosperity_rust_backtester/traders/`
- historical Round 1 trader files now live under `prosperity_rust_backtester/trader_archive/Round1/`

Scope:
- baseline: `prosperity_rust_backtester/traders/round1_baseline_v1.py`
- lower-concentration fallback: `prosperity_rust_backtester/traders/round1_candidate_v2.py`
- prior ships:
  - `prosperity_rust_backtester/traders/round1_overhaul_v8.py`
  - `prosperity_rust_backtester/traders/round1_overhaul_v10.py`
- new contenders from this pass:
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

## Bottom Line

- `round1_overhaul_v22.py` is the new current best ship.
- The gain is real because it improves all required modes and the entire improvement still comes from Ash.
- `round1_overhaul_v12.py` is the warning case:
  - Ash signal is real,
  - but an overcomplicated directional translation can still lose money.
- `round1_overhaul_v13.py` validated the Ash bottleneck.
- `round1_overhaul_v17.py` validated book-aware Ash quoting.
- `round1_overhaul_v20.py` validated fair-based Ash inventory clearing as the next bottleneck.

## Score Under Stress

| Strategy | default | `worse` | `none` | `worse + q=0.35` |
| --- | ---: | ---: | ---: | ---: |
| Baseline | `152,305.5` | `156,131.0` | `159,915.5` | n/a |
| Candidate v2 | `239,372.0` | `239,584.0` | `216,731.5` | `227,724.0` |
| Overhaul v8 | `283,576.0` | `283,543.0` | `246,168.0` | `260,683.0` |
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

## Deltas Versus `v10`

| Strategy | default | `worse` | `none` | `worse + q=0.35` |
| --- | ---: | ---: | ---: | ---: |
| `v13 - v10` | `+2,470.0` | `+2,491.0` | `+1,335.0` | `+1,208.0` |
| `v14 - v10` | `+3,205.0` | `+3,183.0` | `+1,814.0` | `+1,839.0` |
| `v22 - v10` | `+4,635.0` | `+4,668.0` | `+2,106.0` | `+2,605.0` |

Interpretation:
- These are not another `+100` to `+200` Pepper refinements.
- The best candidate clears every required mode by a meaningfully larger margin than the `v8 -> v10` steps did.

## Product-Level Risk Read

### Default contribution

| Strategy | `ASH_COATED_OSMIUM` | `INTARIAN_PEPPER_ROOT` |
| --- | ---: | ---: |
| Overhaul v10 | `45,608.0` | `238,158.0` |
| Overhaul v13 | `48,078.0` | `238,158.0` |
| Overhaul v14 | `48,813.0` | `238,158.0` |
| Overhaul v22 | `50,243.0` | `238,158.0` |

### `none` contribution

| Strategy | `ASH_COATED_OSMIUM` | `INTARIAN_PEPPER_ROOT` |
| --- | ---: | ---: |
| Overhaul v10 | `10,262.0` | `235,922.0` |
| Overhaul v13 | `11,597.0` | `235,922.0` |
| Overhaul v14 | `12,076.0` | `235,922.0` |
| Overhaul v22 | `12,368.0` | `235,922.0` |

### `worse + q=0.35` contribution

| Strategy | `ASH_COATED_OSMIUM` | `INTARIAN_PEPPER_ROOT` |
| --- | ---: | ---: |
| Overhaul v10 | `23,316.0` | `237,449.0` |
| Overhaul v14 | `25,155.0` | `237,449.0` |
| Overhaul v22 | `25,921.0` | `237,449.0` |

Interpretation:
- `v22` still improves only Ash.
- Pepper is deliberately unchanged, which keeps the attribution clean.

## Fill-Quality Read

### Default Ash own-trade counts

| Strategy | Ash buy trades | Ash buy qty | Ash sell trades | Ash sell qty |
| --- | ---: | ---: | ---: | ---: |
| Overhaul v10 | `665` | `3,307` | `661` | `3,278` |
| Overhaul v14 | `795` | `4,216` | `764` | `4,167` |

### `none` Ash own-trade counts

| Strategy | Ash buy trades | Ash buy qty | Ash sell trades | Ash sell qty |
| --- | ---: | ---: | ---: | ---: |
| Overhaul v10 | `187` | `1,060` | `173` | `1,026` |
| Overhaul v14 | `306` | `1,806` | `273` | `1,760` |

Interpretation:
- The new Ash sleeve improves robust aggressive monetization, not just optimistic passive matching.
- That is exactly the kind of change that had been missing in the `v10` lineage.

## Candidate Risk Notes

### `round1_overhaul_v12.py`

Why it failed:
- It changed too many Ash components at once.
- It turned a real Ash signal into an over-opinionated directional state machine.
- Default deterioration showed that the fair-to-order translation was wrong even though the research direction was useful.

### `round1_overhaul_v13.py`

Why it worked:
- It kept the Ash generator story unchanged.
- It only tightened take logic, quote offsets, and position use.

Why it lost to `v14`:
- It was still slightly too conservative.

### `round1_overhaul_v14.py`

Why it is better:
- It pushes the `v13` Ash execution improvement further without touching Pepper.
- It improves all required modes.
- It gives the strategy a second edge without inventing a fragile new market story.

Main remaining risks:
1. Pepper is still the dominant driver of total PnL.
2. The local Round 1 sample is still only three days.
3. Ash is improved, but still partially exposed to matching-quality assumptions.
4. The official backtester may still differ in ways the local stress modes do not capture.

### `round1_overhaul_v15.py`

Why it failed:
- It implemented the deep-report idea of a safe-regime Ash directional skew.
- The added directional lean did not beat the simpler `v14` Ash execution layer.
- That is evidence against pushing Ash toward a more directional hidden-pattern story locally.

### `round1_overhaul_v16.py`

Why it failed:
- It implemented the deep-report idea of a symmetric Pepper recycle–reacquire layer.
- The branch only produced a near-tie to `v14` and did not surpass it.
- This suggests the local reacquire opportunity is either too small or too unstable to justify more Pepper state complexity right now.

### `round1_overhaul_v17.py`

Why it worked:
- It replaced fixed Ash passive offsets with explicit positive-edge join/undercut logic around the live book.
- That lifted default, `worse`, and queue stress without changing Pepper.

Why it was not the final winner:
- It did not improve `none`.
- That meant quote placement improved, but Ash capacity release was still a bottleneck.

### `round1_overhaul_v20.py`

Why it worked:
- It switched large-inventory Ash clearing from the hard anchor toward current fair.
- That improved Ash across all three local days and established that recycling capacity was the next real bottleneck.

Why it was not the final winner:
- The hybrid clear reference still left money on the table relative to the fully fair-based `v22` variant.

### `round1_overhaul_v22.py`

Why it is better:
- It combines:
  - book-aware Ash quoting,
  - stronger wide-spread Ash sizing,
  - and fair-based Ash inventory clearing.
- It improves every required mode over `v14`.
- It adds no new Pepper complexity and no new Ash hidden-pattern story.

Main remaining risks:
1. Pepper is still the dominant driver of total PnL.
2. The local Round 1 sample is still only three days.
3. Ash still depends on the competition’s permissive anchored-maker environment.
4. Official matching could still be harsher than local `none` and queue stress capture.

## Execution-Risk Verdict

- **SHIP** `round1_overhaul_v22.py`
- Keep `round1_overhaul_v14.py` as the prior clean control.
- Keep `round1_overhaul_v20.py` as the key intermediate branch that identified Ash fair-based recycling as the dominant new bottleneck.
- Keep `round1_overhaul_v16.py` only as a near-tie research branch for future official-focused Pepper work.
- Keep `round1_candidate_v2.py` as the lower-concentration fallback.
