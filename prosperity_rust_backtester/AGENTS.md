# AGENTS.md

## Scope
This file applies to everything under `prosperity_rust_backtester/`.

This is the active Prosperity 4 strategy-development workspace. Prefer this subtree for almost all trader work.

## Primary objective
Help build higher-performing Prosperity 4 traders through:
- correct submission code,
- product-specific strategy reasoning,
- disciplined local backtesting,
- focused iteration on the dominant failure mode,
- evidence-based comparisons between trader variants.

## Key directories
- `traders/latest_trader.py` default active trader entrypoint
- `traders/Round1/active/` named active Round 1 milestone traders
- `traders/Round1/work/` staging area for future Round 1 experiments before promotion
- `trader_archive/Round1/archive/` superseded Round 1 trader variants
- `trader_archive/Round1/probes/` market-mechanics probe traders
- `trader_archive/Round1/research/` research-only parameter sweep or diagnostics traders
- `trader_archive/Tutorial/archive/` archived tutorial-round traders and historical variants
- `datasets/` tutorial and round-organized data
- `runs/` generated backtest artifacts
- `README.md` local workflow documentation
- `Makefile` preferred command surface
- `scripts/` helper scripts used by the local workflow

## Trader file policy
- Treat `traders/latest_trader.py` as the default current working baseline unless the user names another file.
- Keep the root of `traders/` minimal: `latest_trader.py`, a small number of readmes, and structured round/tutorial subdirectories.
- Put named active Round 1 milestone traders under `traders/Round1/active/`.
- Archive superseded Round 1 variants under `trader_archive/Round1/archive/` instead of leaving them in the active namespace.
- Put probe traders under `trader_archive/Round1/probes/`.
- Put research-only sweep or diagnostics traders under `trader_archive/Round1/research/`.
- Use `traders/Round1/work/` for new Round 1 experiments until they are either promoted to top-level milestones or archived.
- Keep old tutorial traders under `trader_archive/Tutorial/archive/`; do not leave large tutorial file piles in `traders/`.
- Do not overwrite a benchmark trader unless explicitly asked.
- Do not edit `__pycache__/` contents.

## Environment and setup
Prefer the documented local command surface from `Makefile`.
Common commands:

```bash
make doctor
make build
make test
make tutorial TRADER=traders/latest_trader.py
make tutorial TRADER=traders/latest_trader.py DAY=-1
make backtest TRADER=traders/latest_trader.py
make tutorial TRADER=traders/latest_trader.py PERSIST=1
make tutorial TRADER=traders/latest_trader.py FLAT=1
make tutorial TRADER=traders/latest_trader.py CARRY=1
```

Direct CLI examples:

```bash
rust_backtester --trader traders/latest_trader.py --dataset tutorial
rust_backtester --trader traders/latest_trader.py --dataset datasets/tutorial
```

## Preferred workflow
For strategy work, follow this order.

### 1. Verify the target trader and dataset
Be explicit about:
- which trader file is being changed,
- which dataset alias or folder is being used,
- whether the comparison target is `latest_trader.py` or another named baseline.

### 2. Use the Prosperity skill for market reasoning
Use the `prosperity-4-strategy-engineer` skill to:
- separate official Prosperity 4 facts from older repo inspiration,
- classify each product by market type,
- define the fair-value hypothesis,
- decide whether the next change should affect taking, making, inventory control, or state.

### 3. Make the smallest high-value change
Prefer one of these classes of change at a time:
- fair-value model adjustment,
- taking threshold adjustment,
- passive quoting adjustment,
- inventory skew or flattening change,
- state serialization cleanup,
- diagnostics/logging improvement.

Avoid mixing multiple major strategy changes into one revision unless explicitly asked.

### 4. Backtest locally
Use `make tutorial` for the tutorial bundle by default.
Use `DAY=-1` or `DAY=-2` only when isolating behavior after the full-bundle result is understood.
Use `PERSIST=1` when artifact inspection is needed.

### 5. Inspect evidence, not just headline PnL
When diagnosing results, look for:
- total PnL and per-day PnL,
- product-level PnL contribution,
- aggressive vs passive performance when inferable from logs and artifacts,
- time spent near position limits,
- repeated adverse fills,
- missed favorable top-of-book interactions,
- whether one product dominates losses.

### 6. Summarize clearly
After a change, report:
- what changed,
- why it should help,
- what command was run or should be run,
- what artifact or metric should improve,
- the next best experiment.

## Verification defaults
For a normal strategy improvement task, verification should include:
1. submission-syntax sanity check,
2. a tutorial-round backtest command,
3. comparison versus the chosen baseline trader,
4. inspection of `runs/<backtest-id>/metrics.json` when available,
5. inspection of persisted artifacts when `PERSIST=1` is used.

If a full run is too expensive for the immediate task, still specify the exact command that should be run next.

## Strategy-specific guardrails
- Do not assume tutorial-round behavior generalizes to later rounds.
- Do not import unsupported libraries into submission code.
- Do not add complexity unless it is tied to a diagnosed issue or a clear market hypothesis.
- Do not treat older Prosperity repos as the source of truth for current rounds.
- Do not sacrifice submission correctness for backtester-specific convenience.

## Workspace hygiene
- `runs/`, `target/`, `__pycache__/`, and similar build or cache artifacts are disposable.
- Preserve milestone traders and research outputs; archive them instead of deleting them unless they are clearly generated clutter.
- When promoting a trader to a primary default, keep `traders/latest_trader.py` as the single clear top-level path and archive the rest outside the active `traders/` namespace.

## Tutorial-round defaults
Use these only as starting hypotheses, not as immutable truths.
- `EMERALDS`: start with anchored/stationary fair value and inventory-aware market making.
- `TOMATOES`: start with a more dynamic fair-value estimate and tighter inventory control.

## Done means
A strategy task in this subtree is done when:
- the intended trader file is updated or a new variant is created,
- the change is narrow enough to attribute performance changes,
- the relevant command to validate it is given or run,
- the likely success or failure signal is identified,
- the next iteration step is obvious.

## Role routing inside this subtree

### Code ownership
- `strategy_engineer` is the only default role allowed to edit files in `traders/`.
- `validator` may run backtests and inspect artifacts, but should not modify trader code except when explicitly asked to add diagnostics to a temporary variant.
- All other roles are analysis-only within this subtree.

### Review guidance
Before accepting a strategy change, verify:
- submission interface correctness,
- no unsupported imports,
- no reliance on globals across `run()` calls,
- position-limit safety,
- separation of taking and making,
- inventory-aware quoting,
- baseline comparison evidence,
- no degradation hidden by one lucky day.

Also follow `code_review.md` in this directory.
