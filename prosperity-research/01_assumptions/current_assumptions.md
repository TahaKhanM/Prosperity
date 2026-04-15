# Prosperity 4 Round 1 Current Assumptions

Date: 2026-04-14

Scope: Round 1 continuous-book trader work only. This memo separates official facts, local empirical findings, public-repo-inspired design ideas, generator hypotheses, and speculative improvement ideas.

## Official Facts

- Round 1 algorithmic products are `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`.
- Both official position limits are `80`.
- The required submission interface is a Python `Trader` with `run(self, state)`.
- `run()` must return `(result, conversions, traderData)`.
- `sell_orders` volumes are negative in `OrderDepth`.
- Worst-case side exposure above the limit causes that side’s orders to be rejected for the iteration.
- `traderData` is the intended persistence channel; globals and class fields are not safe.
- `bid()` is Round 2 only and ignored in Round 1.
- The Exchange Auction exists but is a separate side task, not a change to the continuous-book trader interface.

Primary official files:
- `Prosperity Context/Official Prosperity Context.md`
- `Prosperity Context/Official Prosperity Context Round 1.md`

## Soft Hints, Not Rules

- The official narrative says Pepper is steady and Ash is more volatile, possibly patterned.
- The prompt cards are soft clues only.
- They are useful for forming hypotheses, not for asserting the hidden generator.

## Public-Repo-Inspired Design Ideas

These are architecture and workflow ideas only, never current Round 1 truth.

- Mark Brezina:
  - transferable: `alpha / risk / inventory / execution / portfolio` decomposition, competition-first exploitation when evidence is strong.
  - not transferable: tutorial-to-live product analogies as current Round 1 fact.
- Timo Diehm:
  - transferable: formula-first fair objects, normalized diagnostics, `take -> clear -> make`.
  - not transferable: Prosperity 3 bot truths, product truths, trader-ID assumptions.
- CarterT27:
  - transferable: using deeper-liquidity levels to simplify fair estimation and keeping per-product engines separate.
  - not transferable: their Round 1 product labels or parameter values.

## Local Empirical Findings

- `ASH_COATED_OSMIUM` is still best modeled locally as an anchored replenishing-maker market around `10000`.
- Ash has short-horizon imbalance alpha and mean-reverting microstructure, but not a stable time-of-session template.
- `INTARIAN_PEPPER_ROOT` still looks locally like a near-deterministic rising session fair.
- Pepper one-sided books remain short refresh artifacts, not durable states.
- Pepper trades tend to precede later quote adjustments, consistent with lagged quote updates.

## What `v8` Gets Right

- It correctly treats Pepper as a competition-specific template-owning carry product.
- It uses a finer Pepper phase curve than `v6`.
- It keeps the Ash sleeve simple and robust.
- It wins without getting longer earlier or harder.

## What `v8` Might Still Be Missing

- It still uses a coarse recycle controller once Pepper is already full.
- It mostly waits for broad overheat states instead of explicitly monetizing moderate overheat windows around the template.
- It still blends generator and execution logic more than necessary.

## What `v9` Proved Fragile

- A better Ash fair formula does not automatically translate into a better Ash execution policy.
- More directional Ash logic can look fine in default mode and still fail badly in `none` and queue-stress modes.
- Ash remains open, but it needs safer execution translation than the rejected `v9` sleeve.

## What `v22` Newly Suggests

- The official/local performance plateau is likely not only a Pepper-generator issue.
- A meaningful part of the local/official mismatch appears to come from Ash fill quality and Ash inventory recycling.
- Ash does have more robust edge available than `v10` and `v14` captured, but it is realized through:
  - book-aware passive quoting,
  - wider spread-state sizing,
  - and clearing large inventory against current anchored fair instead of waiting for the hard `10000` anchor.
- The winning Ash upgrade still does **not** require a new hidden Ash generator story.
- It requires a better translation from anchored fair into:
  - quote placement,
  - quote size,
  - and capacity-releasing clears.

## Updated Generator Hypotheses

### `ASH_COATED_OSMIUM`

- Best current hypothesis:
  - anchored fair with replenishing makers,
  - short-horizon imbalance-sensitive lean,
  - mild spike-fade behavior.
- Still unproven:
  - a deeper periodic generator or exploitable inventory cycle built into the bots.

### `INTARIAN_PEPPER_ROOT`

- Best current hypothesis:
  - session-template latent fair,
  - revealed through lagged discrete quote updates,
  - with moderate residual overheat/discount states around that path.
- Still unproven:
  - whether the official backtester matches the local 81-knot path closely, or only preserves a broader generator family.

## Known / Unknown / Likely Next Bottlenecks

### Knowns

- Pepper’s template still dominates every other fair object tested locally.
- Moderate Pepper overheat states, roughly `residual in [4, 6.5)`, have positive recycle economics over the next `50` to `100` ticks.
- A tighter Ash maker/taker sleeve can beat the old `v10` Ash logic in default, `worse`, `none`, and queue stress.
- The incremental `v14` gain comes entirely from Ash; Pepper stays unchanged.

### Unknowns

- Whether the official backtester preserves the exact local Pepper curve or only the same broader generator shape.
- Whether more aggressive Pepper recycle would generalize or simply overfit the local bundle.
- Whether the improved Ash sleeve generalizes officially, or whether official Ash matching is materially harsher still.

### Likely next bottlenecks

- template overfitting versus generator regularization,
- carry versus recycle policy quality in Pepper,
- and whether there is still another robust Ash improvement beyond the new `v22` sleeve.

## Current Working Interpretation

- `round1_overhaul_v22.py` is the new best current ship from this pass.
- It keeps the proven Pepper generator and recycle engine unchanged.
- It improves the Round 1 trader through a cleaner Ash monetization layer:
  - book-aware passive quote placement,
  - stronger spread-state sizing,
  - and fair-based inventory clearing when Ash inventory is already large.
- `round1_overhaul_v14.py` remains the prior clean control for the modern Ash/Pepper split.
- `round1_overhaul_v11.py` remains the regularized-generator Pepper control:
  - same recycle layer,
  - smoother 61-knot Pepper template,
  - useful for generalization thinking,
  - but not the best local ship.

## Guardrail

Use this safe Round 1 foundation:
- keep submission syntax strict,
- trade only `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`,
- enforce `80`-limit worst-case safety,
- keep `traderData` compact,
- exploit competition-specific structure only when it is repeatable and survives stress validation,
- prefer broader generator improvements over ever tighter pure curve fit.
