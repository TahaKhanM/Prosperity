# Round 3 parity arbs — tradeable edge on the bid/ask side

The baseline scan `parity_scan.py` flagged **11 801 "intrinsic_floor"**
violations on the voucher chain. Every single one is a mid-based
`0.5 seashell` edge — i.e. an artefact of the half-tick mid resolution on a
deep-ITM voucher priced at integer ticks. This report redoes the scan on
the **tradeable side** (best_bid / best_ask) and reports what is actually
takeable in size.

Source: `parity_violations.csv`, `patch_parity_mono.py` output
(`parity_corrected.json`).

## Tradeable parity counts at edge ≥ 1 seashell

| day | intrinsic floor (vs S_bid) | intrinsic floor (vs S_ask) | cap (V_K vs S_ask) | monotonicity (K1<K2, V_{K1}<V_{K2}) | butterfly (K1,K2,K3) |
|---|---|---|---|---|---|
| 0 | **0** | 176 | 0 | 0 | 0 |
| 1 | **0** | 188 | 0 | 0 | 0 |
| 2 | **2** | 218 | 0 | 0 | 0 |

**The only column that is a riskless arb is the first one** (buy voucher at
ask, immediately sell VE at S_bid, hold to expiry). It has 0-2 events in
30 000 ticks.

The 176–218 "floor_vs_S_ask" column uses S_ask — the price at which we
*buy* VE. It cannot hedge our voucher long; it overstates edge by the
full VE spread (typically 1–2 seashells).

## Edge distribution at various thresholds (floor vs S_bid)

| day | edge > 0 | edge > 0.5 | edge > 1 | edge > 2 |
|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 0 |
| 1 | 0 | 0 | 0 | 0 |
| 2 | 2 | 2 | 0 | 0 |

**Verdict.** Tradeable parity arb on Round 3 historical is **non-existent**
(2 trades across 30 000 ticks × 10 strikes = 0.0007 %). Do not build a
trader around it.

## Mid-basis illusion explained

The 11 801 "violations" from the baseline `parity_scan.py` are mid-vs-mid
(mid of S minus K vs mid of V_K). A voucher whose mid sits exactly at
`S_mid − K` has time-value zero but is NOT tradeable below intrinsic
because:
- best_bid is typically mid − 0.5 (exactly at intrinsic)
- best_ask is typically mid + 0.5 (one tick above intrinsic)

To execute the hedge we must pay best_ask (intrinsic + 0.5) and sell VE at
best_bid (S_mid − (VE spread)/2). Net: we lose the VE spread, which is
≥ 1 seashell for VELVETFRUIT_EXTRACT. Arb collapses.

## Butterfly tests

Edge-≥-1 violations on equally-spaced triples (5000, 5100, 5200), (5100,
5200, 5300), (5200, 5300, 5400), (5300, 5400, 5500): **0** on each day. The
chain is convex.

## Strike-monotonicity

Edge-≥-1 violations for K1 < K2 with best_ask(K1) < best_bid(K2) − 1: **0**
per day. The chain is monotone in strike on the tradeable side.

## Implication for live Round 3

- **Do not ship a standalone parity-arb trader.** Historical edge is 0.
- Keep a *defensive* parity guard: if best_ask(K) < best_bid(S) − K − 1,
  take up to book depth. Free money if it ever shows up. Cost to maintain
  a gate this cheap is near zero, and it's a free hedge against pricing
  bugs in the opposing team's voucher logic. See alpha card G1 (parity
  guard, ship-now, ultra-low-priority size).
- The abundance of mid-basis "0.5 edge" flags is a good reminder to always
  evaluate parity identities on bid/ask, never on mid.

## Practical takeaway

The Round 3 voucher chain is **price-consistent** with the identities.
Mispricings of economic substance (vol risk premium, skew mis-fit) will
have to be traded **statistically** via IV residuals, not via static
parity. That is the core of card C1 (IV-residual scalping).
