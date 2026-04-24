# Voucher analysis — Round 3 — 2026-04-24

Invoked the derivatives-voucher-analyst skill. This file intentionally avoids
Black-Scholes and avoids any parameter (vol, drift, rate) that would have to
be estimated from data we do not have.

## Assumed mapping (from the briefing)

Each voucher is a call-style claim on `VELVET_FRUIT_EXTRACT` (VFE) paying
`max(S_T - K, 0)` at one shared expiry, five trading rounds out.

This is the minimum-commitment interpretation. If the actual mechanism turns
out to be a put, a physical-delivery pack, or a non-linear payoff (digital,
barrier, etc.), every inequality below inverts or degenerates and the trader
must be re-derived.

## Identities that hold independent of Round 3 data

Let `S = mid(VFE)` and `V_K = mid(voucher@K)`. For a European call under
non-negative rates with no dividends:

1. **Lower intrinsic bound:** `V_K >= max(S - K, 0)`.
2. **Upper bound:** `V_K <= S` (the voucher cannot be worth more than the underlying).
3. **Strike monotonicity:** `K1 < K2  =>  V_{K1} >= V_{K2}`.
4. **Convexity in strike:** `V_{K1} - 2 V_{K2} + V_{K3} >= 0` for equally spaced `K1 < K2 < K3`.
5. **Put-call parity** cannot be used because no put / forward is observed.

These are *identities*, not statistical bets. A voucher trade that violates
any of them is a locally-bounded arbitrage opportunity, subject to execution
risk and the exchange's worst-case position-limit rejection.

## Parity-gate design (safe, identity-only)

The candidate trader uses exactly the identities above:

- **Deep-ITM buy gate.** Buy voucher K if best-ask(K) <= max(mid(S) - K, 0) - `slack_buy`, with `slack_buy >= max_bid_ask_spread(VFE)/2 + voucher_spread/2`.
- **Capped upside sell gate.** Sell voucher K if best-bid(K) >= mid(S) + `slack_sell`, because pricing above the underlying is inadmissible.
- **Strike-monotonicity sell gate.** Sell voucher K1 and buy voucher K2 when best-bid(K1) > best-ask(K2) + `slack_mono` for `K1 > K2`. Same-notional offsetting trade.
- **Convexity trade.** Deferred. Requires three simultaneously executable quotes plus tight slack; too brittle to trust without Round 3 data.

All gates are intentionally one-sided identities; violating them is a true
mispricing under any reasonable payoff mapping.

## Things deliberately NOT done

- No volatility surface fit.
- No Black-Scholes delta hedge.
- No implied-forward estimation.
- No time-value model.
- No per-strike fair-value quoting (vouchers are quoted on incoming flow only, via the gates above).

## Discovery-mode behaviour at first Round 3 tick

On the first `run()` call where a voucher symbol appears in `order_depths`,
the trader:

1. Records the symbol and parses the strike out of the trailing integer in
   the symbol string (after the last underscore).
2. If the strike cannot be parsed, the voucher is permanently no-op'd for
   that submission (traderData flag).
3. Holds the symbol in a per-voucher cache with its first-seen timestamp.
4. Refuses to take any position on a voucher whose strike is outside
   `[4000, 6500]` until the outer bound is verified on data.

## Unknowns that would break the design

- If the voucher does not settle at `max(S - K, 0)` but instead pays a fixed
  amount or requires a separate conversion, every identity above breaks.
- If position limits for vouchers are lower than the strike-count the trader
  tries to arb across simultaneously, the worst-case aggregate rejection
  will cancel every voucher order in that tick.
- If voucher timestamps are not aligned with VFE timestamps, `mid(S)` is
  stale relative to `V_K` and the parity gate produces false positives.
