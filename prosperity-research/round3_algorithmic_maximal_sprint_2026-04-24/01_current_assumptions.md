# Round 3 current assumptions — locked 2026-04-24

## Source hierarchy (authority order)

1. Official Prosperity 4 written docs.
2. In-session Round 3 ("Salvinar") briefing provided by the user at sprint start.
3. Repo-local `Prosperity Context/*` documents (only cover Rounds 1-2).
4. Narrative uplink / transcript material.

When the briefing and the official docs conflict, official docs win. Here the
official Prosperity Context pack explicitly does not cover rounds past 2, so
for Round 3 product names, strikes, and voucher-vs-underlying structure, the
user-supplied briefing is the only source. That is a weak source; every
Round-3-specific claim below is tagged `[briefing-only]`.

## Interface and submission facts (HIGH CONFIDENCE — from official docs)

- Trader class with `run(self, state) -> (orders_dict, conversions_int, traderData_str)`.
- `bid(self) -> int` is Round-2-only; harmless to include, ignored in other rounds.
- `OrderDepth.sell_orders` volumes are negative.
- Worst-case aggregate position-limit rejection: if all product-side orders in
  one iteration would breach the position limit, the exchange rejects every
  order for that product in that iteration.
- `traderData` is truncated at 50,000 characters by the hosted framework.
- Hosted runtime is stateless across calls; persistence must go through `traderData`.
- `1,000` testing iterations, `10,000` final-scoring iterations per the official general context.

## Round 3 product facts (LOW CONFIDENCE — briefing-only)

From the in-session briefing the user explicitly asked me to "learn only":

- `HYDROGEL_PACKS` [briefing-only]
- `VELVET_FRUIT_EXTRACT` (VFE) [briefing-only]
- 10 `VELVET_FRUIT_EXTRACT` vouchers, strikes spanning `4000`–`6500` XY, all sharing one expiry nominally five trading rounds away [briefing-only].

**Unknowns flagged `[briefing-only]`:**

- Exact voucher product-name strings in the feed (e.g. `VELVET_FRUIT_EXTRACT_VOUCHER_4000` vs `VFE_VOUCHER_4000` vs some other convention).
- Position limits for `HYDROGEL_PACKS`, `VELVET_FRUIT_EXTRACT`, and each voucher.
- Whether vouchers settle automatically at expiry or require an explicit conversion request.
- Whether voucher and underlying timestamps are aligned tick-for-tick.
- Whether a round counter / ticks-to-expiry is observable from state or must be inferred.
- Whether the venue quotes vouchers as standalone order books (assumed yes; not verified).
- The full list of strikes between 4000 and 6500 (the briefing said ten, but did not list each one).

## BLOCKER: no Round 3 data on disk

- `prosperity_rust_backtester/datasets/round3/` exists but is empty.
- `Data/` at repo root contains `ROUND_1/` and `ROUND_2/` only.
- `Prosperity Context/*` does not cover Round 3 mechanics.

**Consequence:** no hypothesis that claims a Round 3 product-level statistical
edge can be falsified with evidence in this sandbox. Any alpha that requires
price series, spread distributions, voucher order books, or underlying-voucher
correlations will be rejected at the hypothesis stage for lack of evidence,
not because the mechanism is false.

Structural properties that do not depend on Round 3 data — submission-interface
correctness, traderData discipline, worst-case position-limit safety, no-op
behaviour on unknown symbols, voucher parity inequalities (which are identities,
not claims) — remain testable via a dry run on Round 2 data.

## Policy for this sprint

- Do not fabricate Round 3 backtest numbers.
- Do not tune Round 3-specific parameters to any data we do not have.
- Build a defensive Round 3 trader whose sharpest actions are identities
  (deep-ITM voucher arbitrage bounded by intrinsic value), not statistical bets.
- Dry-run on `round2` only to prove the trader compiles, respects the interface,
  does not breach any position limit on any symbol it sees, and degrades to a
  no-op on symbols it was not designed for.
- Final verdict must be SHIP, FLAG, or REJECT. Without Round 3 data, SHIP is
  not defensible.
