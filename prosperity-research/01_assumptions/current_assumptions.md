# Prosperity 4 Round 2 Current Assumptions

Date: 2026-04-19

Scope: authoritative Round 2 facts for the current Prosperity checkout. Official
Prosperity written docs outrank repo tooling, narrative hints, and any older
public repo material. Local-tool notes below are verified against this checkout
and must not be promoted into live-mechanics truth.

Official rule sources used:
- `Prosperity Context/Unrefined Context/Official Prosperity Context.md`
- `Prosperity Context/Unrefined Context/Official Prosperity Context Round 1.md`
- `Prosperity Context/Unrefined Context/Prosperity Round 2.md`

Local verification sources used:
- `prosperity_rust_backtester/README.md`
- `prosperity_rust_backtester/src/cli.rs`
- `prosperity_rust_backtester/src/runner.rs`
- `prosperity_rust_backtester/src/pytrader.rs`
- `imc-prosperity-4-backtester/README.md`
- `imc-prosperity-4-backtester/prosperity4bt/data.py`
- `imc-prosperity-4-backtester/prosperity4bt/runner.py`
- `imc-prosperity-4-visualizer/src/utils/algorithm.tsx`
- `prosperity_rust_backtester/scripts/manual_round/README.md`

## 1. Official Facts

- Algorithmic Round 2 trades the same two official products as Round 1:
  `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`.
- Official position limits in Round 2 are still `80` for
  `ASH_COATED_OSMIUM` and `80` for `INTARIAN_PEPPER_ROOT`.
- Official qualitative framing remains: `INTARIAN_PEPPER_ROOT` is the steadier
  product, while `ASH_COATED_OSMIUM` is more volatile and may hide a pattern.
  This is a clue, not a disclosed generator.
- `bid()` matters only in Algorithmic Round 2. It is the Market Access Fee
  bid, not an order-placement function. Officially, it may exist in any
  submission but is ignored outside Round 2.
- Round 2 Market Access Fee facts:
  accepted bids receive `25%` more quotes; only the top `50%` of bids are
  accepted; accepted participants pay their own bid once; rejected
  participants pay nothing.
- Official testing caveat for Round 2: during testing, the MAF is ignored and
  participants interact with a slightly randomized `80%` quote set with no
  extra market access. Testing PnL therefore does not prove the true best
  `bid()`.
- The `50,000` XIRECs `Research` / `Scale` / `Speed` allocation is the
  separate Round 2 manual challenge. It is not part of algo exchange logic, it
  is not part of `run()`, and it is not what `bid()` controls.
- Stale or non-transferable by rule:
  tutorial products such as `EMERALDS` and `TOMATOES` are not live Round 2
  products; treating the manual budget task as algo logic is wrong by official
  round design; treating `bid()` as relevant outside Round 2 is wrong by the
  official interface rules.

## 2. Local Tool Behavior

- In this checkout, the Rust backtester `latest` dataset alias now resolves to
  `datasets/round2/` because `round2/` is populated. Older repo-context notes
  saying `latest -> round1` are stale.
- The Rust workspace docs still refer to `traders/latest_trader.py`, but that
  file does not exist in this checkout. Use an explicit trader path.
- Current Rust local limit enforcement is not authoritative for Round 2:
  `prosperity_rust_backtester/src/runner.rs` does not list
  `ASH_COATED_OSMIUM` or `INTARIAN_PEPPER_ROOT` in `position_limit(...)`, so
  both currently fall through to the Rust default limit of `100`.
- Current Python backtester limit enforcement does include the official Round 2
  products: `prosperity4bt/data.py` sets `ASH_COATED_OSMIUM: 80` and
  `INTARIAN_PEPPER_ROOT: 80`. Unknown products fall back to `50`.
- Local-tool implication: the two backtesters disagree on fallback behavior,
  and the Rust engine currently disagrees with official Round 2 limits for ASH
  and Pepper. Official written limits of `80` outrank both.
- Repo-local code evidence shows neither backtester currently calls
  `Trader.bid()`: both runners invoke `trader.run(state)` only. Local
  backtests therefore do not model MAF acceptance, fee payment, or the extra
  `25%` quote set.
- The visualizer's official-payload parser reconstructs prices, trades, and
  PnL from `activitiesLog`, but it synthesizes empty `orders`, empty
  `traderData`, empty observations, and `conversions = 0`. Missing detail in
  that view is a parser limitation, not an official exchange fact.
- Repo-local manual tooling explicitly keeps the Round 2 budget-allocation task
  separate from trader code and backtester behavior. That local separation is
  aligned with the official manual/algo split.
- Stale or non-transferable by rule:
  do not treat any local backtester default, dataset alias, README example, or
  visualizer omission as a live Round 2 rule.

## 3. Inferred Assumptions / Known Unknowns

- Inferred: Round 2 has two separate problems, and they should stay separate in
  research and prompts:
  core ASH / Pepper trader quality under the base quote stream, and MAF game
  theory for `bid()`. This checkout can only validate the first one locally.
- Inferred: because official Round 2 testing ignores MAF and the local
  backtesters do not call `bid()`, any locally tuned "optimal" bid is
  non-authoritative.
- Known unknown: the official docs disclose the MAF mechanism but not the live
  Round 2 bid distribution or median acceptance threshold. The true clearing
  cutoff is unknown before final comparison.
- Known unknown: the official docs do not disclose the exact hidden generator
  for ASH or Pepper, only the qualitative framing that Pepper is steadier and
  ASH may hide a pattern.
- Known unknown: the marginal value of the extra `25%` quote access for a given
  trader is not settled by the official docs and is not measurable in this
  checkout because local backtests do not model it.
- Borrowed ideas excluded as authority: public repos, older Prosperity rounds,
  and tutorial notes may still inspire implementation ideas, but they are
  stale by rule for live Round 2 products, position limits, and `bid()`
  mechanics.
- Non-transferable by rule: Round 1 auction reasoning and Round 2 manual budget
  optimizers do not answer Round 2 algorithmic mechanics.
