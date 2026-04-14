# Round 1 Signal Ranking

Date: 2026-04-14

Scope: deeper Round 1 research after the `v10` plateau, with emphasis on finding a second robust edge that could help both stressed local validation and official IMC backtester performance.

## Source Status

### Confirmed by official docs

- Round 1 products are `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`.
- Both limits are `80`.
- The continuous-book trader interface remains `Trader.run(self, state)`.
- Narrative hints are clues, not rules.

### Supported by local data

- Ash is anchored and book-driven.
- Pepper follows an extremely repeatable rising session path in the local bundle.
- Pepper’s visible book mostly reveals local residual state around the template.
- Ash default-vs-`none` behavior shows that fill-quality assumptions matter much more for Ash than for Pepper.
- A tighter Ash maker/taker sleeve can improve PnL in default, `worse`, `none`, and queue stress without changing Pepper.

### Supported only by public-repo analogy

- Formula-first fair objects are better than tactical branching without a clean state object.
- Product-specific engines and explicit `alpha / inventory / execution / risk` separation remain the right workflow.
- Counterfactual testing and ablation are the right way to decide whether a strategy family is real.

### Still unproven

- Whether the official backtester preserves the exact Pepper template or only the broader generator family.
- Whether Ash has another robust edge beyond the improved `v22` sleeve.
- Whether a more ambitious Pepper recycle layer can still add real PnL without overfitting.

## Updated Goods Understanding

## `ASH_COATED_OSMIUM`

Current best read:
- anchored fair around `10000`,
- replenishing-maker microstructure,
- strong short-horizon top-of-book information,
- but fragile translation if that information is pushed too directionally.

Key new conclusion:
- Ash was not solved.
- The old `v10` Ash sleeve was too passive and too dependent on default-mode matching.
- The robust improvement came from changing execution, not from inventing a new hidden Ash generator.

## `INTARIAN_PEPPER_ROOT`

Current best read:
- template-plus-residual good,
- with the template still dominating every tested fair object,
- and the main remaining opportunity still in carry-versus-recycle policy.

Key new conclusion:
- Pepper remains the main engine, but it no longer looks like the only path to improvement.
- Recent plateau-breaking gain came from Ash, not Pepper.

## Public-Repo Transfer Map

### Mark Brezina

Transferable:
- treat the trader as `alpha + risk + inventory + execution + portfolio`, not just “a signal”.
- competition-first willingness to exploit repeatable structure.

Not transferable:
- old product analogies and old round-specific assumptions.

Round 1 use:
- motivated the search for a second monetization layer instead of endlessly refining the Pepper curve.

### Timo Diehm

Transferable:
- formula-first fair objects,
- normalized diagnostics,
- `take -> clear -> make`.

Not transferable:
- Prosperity 3 product truths and bot truths.

Round 1 use:
- kept Pepper generator work compact and made the Ash ablation attributable.

### CarterT27

Transferable:
- deeper-liquidity fair proxies,
- explicit per-product engines,
- use simple fair objects where the market type supports it.

Not transferable:
- their round-specific parameter values.

Round 1 use:
- reinforced the view that Ash should remain an anchored-maker engine while Pepper remains product-specific and separate.

## Candidate-Family Comparison

| Family | Core idea | Why it could work | Why it could fail | Outcome |
| --- | --- | --- | --- | --- |
| `v10` reference | Pepper carry plus template-anchored recycle | current best prior ship | still too dependent on old Ash sleeve | benchmark |
| `v11` regularized Pepper control | smoother Pepper generator | more plausible official generalization | loses `none` | control only |
| `v12` Ash directional-execution redesign | add Ash signal state, flow, and directional quote engine | attacks the official/local bottleneck directly | too invasive, default deterioration | rejected |
| `v13` conservative Ash upgrade | same anchored Ash family, more assertive takes and tighter quotes | cleaner fill-quality improvement | may still be too small | strong |
| `v14` assertive Ash maker/taker | push the same `v13` idea further while keeping Pepper unchanged | adds a real second edge and improves all required modes | could still depend too much on local Ash matching | prior ship |
| `v15` Ash safe-regime directional skew | add small Ash quote lean only in normal two-sided states | tests the report’s regime-gated execution idea without rewriting Ash | local uplift too small and slightly worse than `v14` | rejected |
| `v16` Pepper recycle–reacquire | add a recent-recycle reacquire state on top of `v14` | tests the report’s symmetric recycle hypothesis in residual space | local benefit is too small and unstable across days | rejected |
| `v17` Ash book-aware quoting | replace fixed Ash passive offsets with join/undercut logic anchored to the live book | exploits the same anchored Ash edge with cleaner order placement | default-heavy if it does not also free capacity | strong |
| `v18` Ash signal-aware taking | add imbalance/micro-bias asymmetry on top of `v17` | could improve `none` by selecting better aggressive Ash takes | the directional layer may still be too noisy | rejected |
| `v19` Ash wide-spread sizing | scale Ash passive size more aggressively when spread states are richer | monetizes the strongest passive edge states without changing the fair story | can add inventory without freeing enough capacity | strong but inferior to later branch |
| `v20` Ash fair-based clearing | recycle large Ash inventory against current fair instead of the hard anchor | frees capacity earlier and helps both passive and aggressive Ash monetization | could over-trade if the anchored fair is too noisy | strong |
| `v21` Ash execution stack | combine `v20` fair-based clearing with `v19` spread-state sizing | attacks quote quality and capacity release together | may still be too anchored on local spread mix | strong |
| `v22` full-fair Ash clearing | push the same execution stack and clear large Ash inventory directly against current fair | strongest clean Ash monetization yet, still within the same market hypothesis | official Ash may fill less generously than the local bundle | chosen |

## Why `v12` Lost

- It tried to turn Ash into a more explicit directional state machine.
- That changed too much at once:
  - fair object,
  - take logic,
  - passive quoting.
- Result:
  - the Ash signal was real,
  - but the execution translation was too opinionated.

## Why `v13` Worked

- It stayed inside the old Ash market hypothesis.
- It only changed:
  - take aggressiveness,
  - passive quote offsets,
  - and modest Ash inventory usage.
- That was enough to improve all required modes.

## Why `v14` Won

- `v14` is the best balance of:
  - stronger Ash monetization,
  - unchanged Pepper engine,
  - improved default and stress results,
  - and cleaner economic logic than the rejected `v12` branch.
- The gain is entirely Ash:
  - Pepper totals are unchanged,
  - Ash PnL rises in every required mode.

## Why `v15` Lost

- The safe-regime Ash skew was a valid research hypothesis from the deep report.
- But the extra directional lean did not add enough over the simpler `v14` Ash execution upgrade.
- That means the current Ash edge looks more like better translation of anchored value into orders than like a hidden directional regime model.

## Why `v16` Lost

- The report’s recycle–reacquire idea is economically coherent.
- But the local artifact check showed the symmetric rebuy opportunity was not clean enough to justify a broader Pepper state machine yet.
- The small reacquire controller produced only a near-tie and did not beat `v14`.

## Why `v17` Worked

- The local Ash edge was not only about tighter static offsets.
- A cleaner join/undercut engine around the live book improved Ash without changing:
  - the anchored fair object,
  - the Pepper engine,
  - or the basic take thresholds.
- That validated the public-repo pattern of:
  - fair first,
  - then quote around the live book with explicit positive-edge guards.

## Why `v18` Lost

- The Ash imbalance and micro-bias signals are real in the data.
- But pushing them directly into more asymmetric Ash taking still added less than the simpler execution improvements.
- That is more evidence that the missing Ash money is mostly execution and recycling, not a new directional Ash model.

## Why `v20` and `v21` Worked

- `v20` found the next actual Ash bottleneck:
  - inventory was still being cleared against the hard anchor instead of current fair.
- Clearing large inventory against current fair released capacity sooner and improved Ash on all three local days.
- `v21` added spread-state sizing on top of that and improved further, showing that:
  - quote quality,
  - quote size,
  - and capacity release
  all mattered together.

## Why `v22` Won

- `v22` pushed the same logic one step further:
  - when Ash inventory is already large, clear directly against current fair, not a partially anchored hybrid.
- That produced the strongest clean improvement over `v14` in:
  - default,
  - `worse`,
  - `none`,
  - and queue stress.
- The gain is still fully attributable:
  - Pepper is unchanged,
  - all uplift is Ash,
  - and the market hypothesis is still the same anchored-maker Ash story.

## Current Ranking

1. `round1_overhaul_v22.py`
2. `round1_overhaul_v21.py`
3. `round1_overhaul_v20.py`
4. `round1_overhaul_v19.py`
5. `round1_overhaul_v17.py`
6. `round1_overhaul_v14.py`
7. `round1_overhaul_v13.py`
8. `round1_overhaul_v10.py`
9. `round1_overhaul_v16.py`
10. `round1_overhaul_v11.py`
11. `round1_overhaul_v8.py`
12. `round1_overhaul_v15.py`
13. `round1_overhaul_v6.py`
14. `round1_overhaul_v3.py`
15. `round1_candidate_v2.py`
16. `round1_baseline_v1.py`

## Explicit Formula and Policy Objects Now Favored

### Ash fair object

- Base fair remains:
  - `fair_ash = 10000 + 0.65 * clamp(mm10_mid - 10000, -3, 3) + 0.25 * clamp(microprice - mid, -1.5, 1.5) + 0.35 * clamp(-0.45 * ret1, -1.5, 1.5)`

### Ash execution stack in `v22`

- Better take threshold:
  - keep the `v14` style take logic:
  - `take_edge = 2.0` in normal states,
  - `1.5` in shock states,
  - plus extra caution only when Ash is already far from the anchor.
- Better passive placement:
  - quote around the live book using positive-edge join/undercut logic,
  - not just fixed passive offsets from fair.
- Better spread-state sizing:
  - when spread widens to `18+`, increase first and second quote sizes rather than inventing a new signal.
- Better inventory recycling:
  - when Ash inventory is already large, clear directly against current fair rather than waiting for the hard anchor.

### Pepper generator

- Unchanged from `v10`:
  - 81-knot session template,
  - same recycle logic,
  - still the best balanced Pepper engine currently shipped.

## Best Current Hypotheses

1. The official/local gap is no longer best understood as only a Pepper-template problem.
2. Ash fill quality and Ash order translation were a genuine bottleneck.
3. The strongest current Round 1 trader is now a hybrid:
   - competition-specific Pepper carry/recycle,
   - plus a more realistic anchored Ash maker/taker sleeve with cleaner recycling.
4. The returned deep research report did surface real ideas, but the biggest practical unlock after `v14` was still inside Ash execution rather than a new Pepper state machine.
5. The next evidence-backed frontier is more likely official-generalization work on the Pepper generator family than another Ash directional-complexity increase.
