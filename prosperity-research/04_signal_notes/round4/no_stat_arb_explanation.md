# No tradeable stat-arb pair on R4 — documented absence

This file documents the negative result from Phase 2B's pairwise / triple
cointegration sweep. A documented absence is itself a useful artefact for
the next session — uncharacterised absence is not.

## Tests run (from prosperity-research/04_signal_notes/round4/stat_arb_pairs.csv)

14 of 66 prioritised pairs tested:
- HYDROGEL ↔ VE
- VE ↔ each of {VEV_4000, 4500, 5000, 5100, 5200, 5300, 5400, 5500} (8 pairs)
- VEV_4000 ↔ VEV_4500 (deep-ITM)
- VEV_5000 ↔ VEV_5100 (adjacent ATM)
- VEV_5400 ↔ VEV_5500 (adjacent OTM)
- HYDROGEL ↔ VEV_5200 (cross-asset)
- (Stuck strikes excluded since std=0.)

For each pair:
1. OLS Y = α + β·X per day separately AND pooled (3 + 1 = 4 fits).
2. ADF-style unit-root test on residual: ρ̂ from Δε̂_t = γ·ε̂_{t-1} + ε; t-stat.
3. OU half-life of ε̂; in-sample Sharpe of trading the spread.
4. β-stability OOS check: fit β on day 1, apply on days 2/3.

Triples tested: 5 (each (VE, K1, K2) with strikes bracketing VE spot).

## Bonferroni threshold applied

14 pairs × 1 ADF test each = 14 tests. Bonferroni-corrected significance:
0.05 / 14 ≈ 0.0036 → t > 2.7 (one-sided). For triples additional 5 tests
→ overall threshold t > 3.4.

## Verdict

| Result | Count |
|---|---|
| Cointegrated by Bonferroni-corrected ADF | 1 of 14 pairs (+ 5/5 triples, but trivial) |
| ALSO survives β-stability OOS (|Δβ|/β < 0.30) | 1 of 14 pairs |
| ALSO survives half-life ≤ 5,000 ticks gate | 1 of 14 pairs (= VEV_4000 ↔ VEV_4500) |
| ALSO has positive day-2 + day-3 OOS Sharpe | **0 of 14 pairs** |

The single cointegrated pair (VEV_4000 ↔ VEV_4500) is a TAUTOLOGY:
both = VE − K with K constant, so any joint regression returns β ≈ 1.0
and residual ≈ K_4500 − K_4000 = 500 ± 1.6 noise. The "cointegration" just
confirms that VE is the latent factor. There is no edge to trade.

The 5 triples (long VE, short two-strike spread) all have HL ≤ 5 ticks —
that is degenerate replication (the synthetic VE is exact within a scalar),
NOT a curvature mean-reversion. Spread variance is dwarfed by execution
cost (spread × 3 legs >> mean reversion).

## Why the cross-product alpha is NOT in stat-arb

The R4 alpha hunt DID find a cross-product alpha in Phase 3 — the
**vega-coupling spillover from VEV_5200 to VEV_4000 / 4500 / 5000 / 5100**.
But this is a PER-MARK CONDITIONAL signal, not a stat-arb one. The
cointegration tests above are unconditional (treat the whole tick stream
as one population); they cannot detect "when Mark 14 prints, X happens"
because the conditioning event is sparse (33 / 30,000 ticks for Mark 14
buy on VEV_5200).

The same finding via Phase 2B's tests: HYD ↔ VE Granger F < 1.6 both
directions → independent factors. VE ↔ ATM-voucher F is large but
SYMMETRIC → contemporaneous co-movement, not lead-lag alpha.

## What was tested and rejected (a triage list for next session)

These should NOT be re-investigated unless new evidence emerges:

- VE ↔ VEV_K linear cointegration for K ∈ {5000..5500}: cointegrated
  in-sample (R² 0.71-0.82) but OOS Sharpe negative (residual variance >
  mean reversion).
- 1-2-1 butterfly basket V_5200+V_5300−V_5100−V_5400: mean-reverts
  beautifully (HL 5-19) but spread sd 1.1-2.1 vs 9.5-10.6-shell round-trip.
- Average-voucher-vs-VE basket: too slow (HL 115+) and noisy (sd 7-9).
- VEV_4000+VEV_4500 − 2·VE + 8500 identity: mid-perfect (sd 1.55-1.65)
  but bid-ask round-trip ~23 shells. Repurposed as the R4-CHAIN-03
  defensive parity-guard alarm.

## What might still be findable (open questions)

- **Conditional cointegration**: the per-Mark conditional spillover (Phase 3)
  IS a form of conditional cointegration. Future sessions could test
  whether the residual after subtracting the Mark-conditional drift is
  still stationary (and whether the residual has additional alpha).
- **Higher-frequency stat-arb**: we tested at the 100ms tick level. Going
  finer (sub-tick) is not possible with this dataset. Going coarser
  (10-tick or 100-tick aggregation) might reveal stat-arb with longer
  half-lives that we missed — but most have HL > 5,000 = half a day
  → not tradeable in 10,000-tick rounds.
- **Vol-stat-arb**: we tested PRICE cointegration. Could add VOL-of-X vs
  VOL-of-Y cointegration. Phase 2B's volatility-spillover analysis
  showed peak cross-corr at lag 0 — no lead-lag — but that doesn't rule
  out a cointegrated VOL pair.
- **Live arb on hosted execution**: the historical mid is not the same as
  the live tradeable price. If the hosted exchange has slightly different
  order book dynamics, parity violations might surface that aren't in hist.
  Run parity_scan.py on every live combined.log.

## Bottom line

There is no FREE-LUNCH stat-arb pair on R4 historical data tradeable in
≤ 10,000 ticks at unit-shell costs. Every "promising" spread has been
characterised, rejected, and documented above.

The cross-product alpha lives in the per-Mark conditional spillover layer
(see `counterparty_deep.md` and `cross_product_mark_spillover.csv`),
NOT in the unconditional regression-cointegration layer.
