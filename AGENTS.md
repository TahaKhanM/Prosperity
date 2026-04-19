# Prosperity 4 agent guidance

Read `00_PROSPERITY_CONTEXT_OVERVIEW.md` first.

Then read the relevant task file:
- algorithm work -> `10_ALGO_TRADING_CONTEXT.md`
- manual challenge work -> `20_MANUAL_TRADING_CONTEXT.md`
- repo/tooling/prompting/backtester work -> `30_REPO_AND_TOOLING_CONTEXT.md`

## Non-negotiable rules

- Official Prosperity written docs outrank narrative hints and uplink summaries.
- Do not mix tutorial products with live Round 1 / Round 2 products.
- Round 2 `bid()` matters only for Round 2 market-access bidding.
- Use `traderData` for persistent trader state; do not rely on mutable globals
  or class state.
- Preserve submission compatibility: prefer returning
  `(orders, conversions, traderData)`.
- Treat local backtester behavior as local evidence, not hosted truth, when the
  documented tooling files call out mismatches.
- For documented repo work, use the Rust backtester by default, pass explicit
  trader and dataset paths, and do not assume conversions are simulated.
- Keep changes localized and attributable. Prefer one dominant change per
  iteration and state the next validation step.

## Repo reality note

This context pack was generated from uploaded docs. The actual repo checkout is
not verified in this sandbox. If a real checkout is present in a future session,
prefer the code over any stale doc claim.
