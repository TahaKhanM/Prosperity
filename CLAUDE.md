# Prosperity 4 project guidance

Read these files before acting:
- @00_PROSPERITY_CONTEXT_OVERVIEW.md
- For algorithm work: @10_ALGO_TRADING_CONTEXT.md
- For manual challenge work: @20_MANUAL_TRADING_CONTEXT.md
- For repo/tooling/backtester/prompting work: @30_REPO_AND_TOOLING_CONTEXT.md

## Broad rules

- Official written Prosperity docs are the source of truth for rules,
  interfaces, products, and limits.
- Do not mix tutorial products with live Round 1 / Round 2 products.
- Use `traderData` for persistent state. Do not rely on globals or class state.
- Preserve submission compatibility unless the task explicitly targets a local-
  only experiment.
- For documented repo work, prefer the Rust backtester, explicit trader paths,
  explicit datasets, and explicit baselines.
- Keep one dominant change per iteration and say how to validate it.

## Note

This pack was built from uploaded documentation. The actual repo checkout is not
verified in this sandbox. If the repo is present in a future session, prefer the
code over stale documentation.
