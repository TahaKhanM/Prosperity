# Round 3 product classification — 2026-04-24

Uses the product-classifier skill. Every classification here is
`[briefing-only, unverified]` because no Round 3 data exists on disk.

Behaviour families considered: anchored-mean, drifting-mean, regime-switching,
trending, mean-reverting, depth-asymmetric, imbalance-persistent, liquidity-shock-prone,
derivative-linked, calendar-anchored (expiry-aware), cross-product-linked,
bounded-by-identity.

## HYDROGEL_PACKS

- Family: **unknown** (no data).
- Falsifier: the product name carries no structural prior strong enough to
  bias a behaviour family. Treat as generic stable/volatile commodity until
  day `-2` of Round 3 data is inspected.
- Confidence: very low.
- Action: default to conservative two-sided market making only once a mid
  price and spread distribution are observable.

## VELVET_FRUIT_EXTRACT (VFE)

- Family: **derivative underlying** (because 10 vouchers reference it)
  combined with whatever its own behaviour is — still unknown.
- Falsifier: if VFE price never moves outside one strike bucket in day `-2`,
  most vouchers are effectively dead and the voucher strategy degenerates to
  a cash-and-carry on whichever strike straddles the mid.
- Confidence: medium on derivative-underlying role, low on own behaviour.

## VELVET_FRUIT_EXTRACT_VOUCHER_<K> for K in {known 10 strikes, 4000–6500}

- Family: **bounded-by-identity** (voucher price is bounded below by
  `max(S - K, 0)` and above by `S` under the standard call-payoff mapping,
  absent exotic settlement rules).
- Falsifier: observe a voucher trade below `max(mid(VFE) - K, 0) - slack` or
  above `mid(VFE) + slack` on day `-2` of Round 3. Such a trade would
  falsify the call-payoff mapping and force a voucher-structure re-derivation.
- Confidence: high on the inequality bounds; very low on the pricing *inside*
  the bounds (time value, expiry-discounting).

## Rejected classifications

- **"Apply Black-Scholes."** Rejected. No observed volatility, no confirmed
  continuous mapping, discrete daily ticks, no confirmed underlying return
  distribution. Refused per the derivatives-voucher-analyst guardrail.
- **"Vouchers are just a parity chain with a 1:1 spread."** Rejected without
  Round 3 data; this is only true for deep-ITM strikes and even then only up
  to time-value and settlement mechanics.
- **"Vouchers are ignorable because expiry is 5 rounds out."** Rejected; deep-ITM
  or deep-OTM mispricings can still be arbitraged inside the intrinsic bounds.
