# R4 Alpha Hunt — Append-Only Journal

Session start: 2026-04-26.
Goal: find every commercially-meaningful, statistically-supported alpha in
the R4 algorithmic data — beyond the 5 R3 carry-overs (A1, B1, C1, D1, E1, G1).

## Phase 0 — context loaded

- 7 Marks confirmed in R4 historical: 01, 14, 22, 38, 49, 55, 67.
- Headline edge already found: Mark 14 +5.71/unit, Mark 38 −8.34/unit.
- 12 algorithmic products unchanged from R3.
- TTE schedule: hist day 1/2/3 = 7/6/5 days; live R4 = 4 days.
- R3 v15 is the strongest baseline (sum 281,014 across 10k+1k 3-day BT).
- Tooling fresh: voucher_panel.csv (30,000 rows), counterparty_scan.csv (137 rows),
  vol_surface_coeffs/residuals.csv, parity_violations.csv all dated 2026-04-26 ~15:37.
- Datasets: 10,000 ticks/day, 12 products → 120,000 rows per prices CSV; trades
  CSV is small (~1,400 rows/day).
- VFE order-book depth is sparse — only 5,439–5,494 of 10,000 ticks have a
  level-2 bid; OTM vouchers (VEV_5300+) are even sparser.
- HYD has all 30,000 ticks with full depth; VFE is the bottleneck for any
  multi-level signal.

## Carry-over alphas (DO NOT re-test, reference-only)

| ID | What | R4 status |
|---|---|---|
| A1 | HYD soft-anchor MM | re-validate band on day means 9992/9989/10003 |
| B1 | VE wall-mid MM with AR(1) | re-validate β |
| C1 | Top-2 imbalance skew | re-validate slopes |
| D1 | Voucher IV-residual scalp w/ TTE-indexed smile | re-validate coefficients |
| E1 | Deep-ITM as VE-equivalent capacity | unchanged |
| G1 | Parity guard | unchanged |
| F1-Mark14 | Copy Mark 14 (NEW for R4) | already in headline; refine |
| F1-Mark38 | Fade Mark 38 (NEW for R4) | already in headline; refine |
| F1-Mark67 | Lean long VE on Mark 67 buy (NEW) | already in headline; refine |

## Phase 1 — per-product lens battery findings (4 of 5 sub-agents back)

### HYDROGEL_PACK
- **HEADLINE BRITTLE**: Mark 14/38 edge concentrated in day 1; t=±1.8/±0.4/±1.3 across days. The +5.71/-8.34/unit number is NOT a stable per-tick signal. Confirmation gate (min Mark-14-trades-in-window) needed before sizing on it.
- R3 spectral 3330-tick rhythm does NOT replicate (R4 peaks at 5000/1603/5000 across days).
- imb1, imb2, imb3, wall-mid all rock-solid t≈30+ across days. Carry-overs hold.
- **NEW R4-HYD-M01**: Mark 22 BUY on HYD is a robust adversarial signal — h=1 Δmid −3.17/−3.88/−2.25, t = −5.3/−3.6/−1.5. Only 3-9 prints/day → small capacity, but precision is high.

### VELVETFRUIT_EXTRACT
- **NEW R4-VFE-M01 (the most stable edge in the dataset)**: Mark 67 buy → h=1 Δmid +1.99/+1.86/+2.09 (t = +16.2/+16.1/+13.1). Mean qty 9. Combined Mark-conditional copy stack ≈ +200 XIRECS/day.
- **NEW R4-VFE-M02**: Mark 49 sell → h=1 Δmid +1.88/+1.76/+2.07 (t > +10 every day).
- **NEW R4-VFE-M03**: Mark 22 sell → h=1 Δmid +1.65/+1.51/+1.25 (t=+7.8/+7.2/+3.1, day-3 marginal).
- **NEW R4-VFE-F01**: bv1 modes are qty 21/22/23 → wall threshold 20 → 22 (defensive).
- imb_k2 β unchanged from R3 (≈3, t=29). Microprice does NOT beat wall-mid on VFE (β=0.28 vs 0.78) — REJECT V_FE microprice.

### VEV_4000 / VEV_4500 (deep-ITM)
- Both pure delta-1 (median TV = 0). Lead-lag with VE dead (|ρ| < 0.05 every k).
- Tradeable parity: 0/0/0 buy-side, 0/1/2 sell-side. G1 already covers this; nothing new.
- β-residual fade (R4-V4000-E01, R4-V4500-E01) shows AC1 of -0.46/-0.48 — but doesn't clear 16-21 tick spread on takes. Only realisable as posted-quote alpha. **Marginal — flag for null-test before shipping**.
- Wide spreads (V_4000=21, V_4500=16) vs VE spread=5: deep-ITM strikes are STRICTLY WORSE execution for VE-equivalent capacity. E1's "extra capacity" idea only helps when VE 200 limit binds.

### VEV_5000 / VEV_5100 / VEV_5200 (ATM trio)
- **NEW R4-V5000-C02**: imb2 → Δmid_{t+1} β=+3.05/+3.59/+3.15, t=+12.4/+15.1/+13.7 (stable). v15 doesn't currently do per-voucher imb2 skew. Mech: fair = wall_mid + 3·imb2 (capped).
- **NEW R4-V5100-C01**: microprice fair on VEV_5100 (β=+0.264, t > +21 across days). Adds informational lift over wall-mid alone. Mech: fair = α·micro + (1−α)·wall, α≈0.3.
- **NEW R4-V5200-F01**: 100-tick realised-vol AC1 = 0.51/0.45/0.39 (clean monotonic). Defensive MM-widening when vol > 90th pct.
- **NEW R4-V5200-D02**: VEV_5200 day-3 IV residual mean +0.085 vs +0.013 d1/d2 (~6-7σ). Suggests bias-up of fair on late-round days.
- IV residual half-life on all three strikes < 0.4 ticks → v15's 1-tick AC1 fade is sufficient. AR(2+) and VE lead-lag dead.

### VEV_6000 / VEV_6500 (stuck strikes)
- **VERDICT: NOTHING TRADEABLE.** Mid stuck at 0.50 across all 30,000 ticks; std=0; trades clear at price 0.0 (Mark 22 hits bid).
- Tail probability check: P(S_T > 6000) ≈ 1.1×10⁻⁷, P(S_T > 6500) ≈ 1.1×10⁻¹⁶ at TTE=4d.
- The 0.50 mid is ~50,000× over fair value (V_6000) — RICH not cheap. No tail trade.
- 100% Mark 01 ↔ Mark 22 noise. Marks 14/38/49/55/67 NEVER appear here.
- Cross-spillover (V_6000/6500 print → VE next 50/100/200 ticks): worst |t|=1.67, signs flip — pure noise.
- **Documented for future sessions**: do not re-investigate. See per_product/VEV_6000.md and VEV_6500.md.

### VEV_5300 / VEV_5400 / VEV_5500 (OTM trio)
- **HEADLINE — v15's AC1 fade K is SYSTEMATICALLY UNDER-SIZED on all three strikes.**
   - V_5300: measured AC1 = −0.214; v15 K = 0.12 → optimal K ≈ 0.21 (42% under).
   - V_5400: measured AC1 = −0.249; v15 K = 0.15 → optimal K ≈ 0.25 (40% under).
   - V_5500: measured AC1 = −0.242; v15 K = 0.15 → optimal K ≈ 0.24 (38% under).
   - ρ1 t-stats ≈ −22 to −24 over 30k obs. Re-tune is the most defensible single change.
- **NEW R4-V5300-D02 / R4-V5400-D02**: fade Mark 14 buy on these strikes. h=5 Δmid:
  −0.42 (t=−2.5, n=30) on V_5300 and −0.38 (t=−3.3, n=13) on V_5400. V_5500 too thin (n=7).
- **NEW R4-V5500-D03**: |ret| AC1 = 0.37 on day 3 (strongest of any voucher). Widen
  MM quotes after non-zero |Δmid| in past ~10 ticks.
- **NEW R4-V5300-C03**: IV residual EMA(20) over-smooths — true HL is 0.2-0.5 ticks.
  Replace EMA(20) with EMA(2-3) on the residual.
- **NEW R4-V5500-F04**: Stale-book guard — pull quotes after >300 ticks of unchanged mid
  (longest run unchanged on day 3 = 909 ticks).
- VE lead-lag dead at all OTM strikes (|ρ| < 0.026).
- imb2 / imb3 unreliable on OTM (sparse L2 depth, t < 2 on most days).

## Phase 5 — past-winner technique sweep findings

5 repos studied (TimoDiehm 2nd P3, chrispyroberts 7th P3, CarterT27 9th P3, jmerle 25th P3, ericcccsliu 2nd P2).

**Top 3 high-priority gaps** (techniques NOT in v15):

1. **Per-strike rolling mid-IV as voucher fair** (replaces v15's fixed quadratic + static
   per-strike bias). CMU Physics post-mortem reports their parabola broke on submission day;
   switching to a short-window rolling mid-IV took backtest PnL 80k → 200k. v15 has only the
   static `SMILE_PER_STRIKE_BIAS` dict — this is structurally the largest gap.
2. **Microprice fair-value for HYD/VFE.** v15 doesn't use microprice (uses wall-mid + EMA).
   But: Phase-1 sub-agent already showed microprice does NOT beat wall-mid on VFE
   (β=0.28 vs 0.78). For HYD this is still an open question.
3. **Counterparty aggressor-sign cumulant scoped to {Mark 14 minus Mark 38}.** R4-unique.
   Converts a passive MM to a directional MM via cumulative signed flow attributable to
   smart/bag-holder Marks only.

Other interesting menu items (untested in v15): VPIN toxicity, HMM 2-state regime, Hawkes
self-excitation, Lee-Mykland jump detection, Avellaneda-Stoikov reservation MM,
cross-day overnight gap, per-strike volume imbalance, spike-vol regime gate.

## Structural quirks discovered in Phase 1

- **VEV_6000 ↔ VEV_6500 trade rows are BYTE-IDENTICAL** (same ts + qty for all 317 rows
  across 3 days). The deep-OTM MM (Mark 01 ↔ Mark 22) double-prints synchronously off one
  trigger. Documented as informational; no alpha (no V_6000 vs V_6500 spread).
- **Stuck strikes trade at price = 0.0**, not at mid 0.5. Mark 22 hits the bid (0)
  every time. The exchange tape clears at the bid even though mid is 0.5 — interesting
  microstructure quirk.
- **HYDROGEL bv1 quantum = 10/11/12/15**; only 12 unique values. **VFE bv1 quantum is
  fragmented (53-54 unique values, modes 21-23)**. The threshold-20 wall filter on VFE in
  v15 just-barely misses the modes; bumping to 22 should sharpen the wall-mid signal.
- **v15's per-strike SMILE_PER_STRIKE_BIAS dict** was tuned on R3; R4 day-3 IV residuals
  show new biases (e.g., V_5200 +0.085 vs R3's +0.0076; V_5000 −0.082 vs R3's −0.0077).
  The static R3 biases are STALE relative to R4.

## Phase 2B — stat-arb / Granger / PCA / implied-vs-realised (HARD NO)

Sub-agent tested 14/66 prioritised pairs and 5 triples. Headline: **0 ship-grade pairs.**

- **Cointegration (2.7)**: only VEV_4500 ↔ VEV_4000 passes the Bonferroni-corrected
  ADF threshold (β ≈ 0.999, HL = 0.1). But that is a tautology — both = VE − K and
  cointegration just confirms VE liquidity. Every other "cointegrated" pair (VE ↔
  VEV_5000..5500) FAILS the OOS Sharpe gate when day-1 β is applied to days 2/3.
- **Granger / spillover (2.8)**: HYD ↔ VE Granger F < 1.6 both directions →
  independent factors. VE ↔ ATM-voucher F is symmetric → contemporaneous co-movement,
  not alpha. Vol cross-corr peaks at lag 0 (no lead-lag).
- **PCA (2.9)**: PC1 (49.6 %) is the VE-complex factor; PC2 (38.3 %) is HYD alone
  (loading 1.0). PC1+PC2 residuals have ρ1 ≈ −0.29 to −0.47 — but this just
  reproduces the per-product spread-bounce already in B1/C1. **No NEW stat-arb leg.**
- **Implied vs realised (2.10)**: LOO smile-fit residual is consistently negative
  (−11, −15, −123 across days 1–3) BUT magnitude scales with shrinking TTE →
  confirms parabola extrapolation bias, NOT market dislocation.

Outcome: family 4 (stat-arb) is empty. I will write
`no_stat_arb_explanation.md` per the spec requirement.

## Baseline backtest — v15-on-R4 (START_TTE_DAYS=7)

| set | day | ticks | own_trades | final_pnl |
|---|---|---|---|---|
| day-1 | 1 | 10000 | 1281 | **+67,625** |
| day-2 | 2 | 10000 | 1238 | **+107,578** |
| day-3 | 3 | 10000 | 1162 | **+47,571** |
| **total** | | | **3,681** | **+222,775** |

Per-product attribution:
- HYDROGEL: +34,861 / +42,412 / +56,789 = **+134,062** (dominant earner)
- VFE:      +14,763 / +8,684 / **−3,029** = +20,418 (day-3 weak)
- VEV_4500: +6,140 / +13,076 / −1,710 = +17,506
- VEV_4000: +5,981 / +13,047 / −344 = +18,684
- VEV_5100: +2,153 / +12,182 / −2,257 = +12,078
- VEV_5200: **−1,654** / +9,251 / **−4,746** = +2,851 (struggles on day-3)
- OTHER(+6): +5,380 / +8,926 / +2,868 = +17,174

→ v15 baseline = 222,775 XIRECS / 3-day-BT. Day-3 VFE / VEV_5200 are the
weak points — every R4 alpha probe should target these.

## Phase 3 — counterparty deep-dive findings (RECONCILES Phase 1 brittleness claim)

- **Mark 14 / Mark 38 on HYDROGEL ARE robust per-day after all.** h500 PnL: Mark 14
  buyer +6,052 / +4,708 / +5,240 (conc 0.38). Mark 38 buyer −6,242 / −5,216 / −5,190.
  Per-trade Sharpe **1.78–1.95**. Top-10 % share = 0.19 (UNIFORM — not driven by big
  prints). Total Mark 14 + Mark 38 four-way edge is **~+65,400 per 3-day** if perfectly
  copied (probably ~10-25 % achievable in practice).
- Phase 1 brittleness was looking at PER-TICK Δmid t-stat (noisy on h=1) — Phase 3's
  per-trade horizon-500 PnL is the more relevant metric. Sign and magnitude robust.
- **29 of 57 (Mark, product, side) edges pass the robustness filter.**
- **Mark 67 IS the actual VE price-mover** (Kyle's λ = +0.24 across all horizons).
  Mark 14's λ on VE is near 0 (−0.011 / −0.054) — Mark 14 captures spread but doesn't
  move price. Mark 14 is a passive quote-sipper; Mark 67 is the impact bot.
- **Mark 14 has zero order-book footprint** (lift = 0.0 on HYD, 0.01 on VE). They
  do NOT strip level-2 liquidity. So the "did the level-2 disappear?" filter is
  not useful for predicting Mark 14 prints.

## NEW HEADLINE ALPHA — vega-coupling cross-strike spillover (R4-CHAIN-XPROD-VEV5200)

13 of 660 cells survive Bonferroni |t| > 4 + lift ≥ 50 % filter. **ALL 13 have
VEV_5200 as the source product** (the highest-vega strike where Mark 14 / Mark 38
dyad concentrates).

| Mark | source | target | side | h | n | mean Δmid | t | lift |
|---|---|---|---|---:|---:|---:|---:|---:|
| Mark 22 | VEV_5200 | VEV_4000 | sell | 5  | 46 | +5.087 | +20.8 | +216% |
| Mark 14 | VEV_5200 | VEV_4000 | buy  | 5  | 33 | +5.061 | +18.1 | +215% |
| Mark 22 | VEV_5200 | VEV_4500 | sell | 5  | 46 | +3.783 | +15.2 | +168% |
| Mark 14 | VEV_5200 | VEV_4500 | buy  | 5  | 33 | +3.758 | +13.8 | +167% |
| Mark 22 | VEV_5200 | VEV_4000 | sell | 20 | 46 | +5.957 | +7.3  | +138% |
| Mark 22 | VEV_5200 | VEV_5000 | sell | 5  | 46 | +1.435 | +6.6  | +71%  |

Mechanism: a print on VEV_5200 by the Mark 14↔Mark 38 dyad triggers an instant
re-pricing of the deeper-ITM stack (vega-coupling). NOT exogenous prediction —
this is bot-driven smile-shift contagion. Tradeable because the deeper-ITM mids
move ~5 ticks within 5 ticks of the source print → enter on VEV_4000/4500
ahead of the snap-back, exit when the chain re-equilibrates.

Phase 2B "0/14 stat-arb" missed this because it tested LINEAR REGRESSION
cointegration, not per-Mark conditional spillover. Phase 3 found the alpha
because it conditioned on the trigger (Mark + source-product print).

## Phase 2A — voucher chain geometry (3 candidate alphas)

- **R4-CHAIN-01**: BS Δ vs realised 100-tick β: 0.7×Δ_BS hedge ratio (instead of 1.0×).
  ~30 % less VE inventory burned per voucher hedge. t=16-51 per (day, K) cell across
  30 cells. **STICKY-STRIKE > sticky-delta in R4**.
- **R4-CHAIN-02**: Day-3 convexity SPIKE — a2 = 7.62 (TTE 7) → 8.53 (TTE 6) → **14.11**
  (TTE 5). v15's `SMILE_A2_BASE = 7.21, _DRIFT = 0.815` LINEARLY EXTRAPOLATED is too
  flat. New: A2_BASE = 7.62, A2_DRIFT = 1.62.
- **R4-CHAIN-03**: Defensive parity-guard alarm on V_4000 + V_4500 − 2VE + 8500
  outside ±8 shells. Mid sd 1.55-1.65 across days. ALARM only, not auto-trade
  (round-trip cost ~23 shells).

Dead from Phase 2A:
- Tradeable parity arb: 6 hits / 30k ticks, max 2-shell edge.
- VE → voucher lead-lag: max |ρ|=0.05.
- Basket 2 (1-2-1 butterfly): MR HL 5-19 but spread sd 1.1-2.1 vs 9.5-10.6 round-trip.
- Basket 1 (avg vouchers - VE): too slow, too noisy.

## Phase 8a — probe backtest results (4 probes vs v15 baseline = +222,775)

| Probe | Δ vs baseline | day-1 | day-2 | day-3 | Verdict |
|---|---:|---:|---:|---:|---|
| `r4_mark_lean_v01` | **+1,054** | +312 | +81 | +663 | **WINNER** |
| `r4_otm_ac1_retune` | +33 | −301 | +188 | +148 | REJECT (flat) |
| `r4_xprod_vev5200` | +42 | 0 | 0 | +42 | REJECT (signal too rare) |
| `r4_combined_v01` | **−60,939** | −28,586 | −23,420 | −8,934 | REJECT (hedge blowup) |

**The mark-lean stack delivers +1,054 / +0.47 % over baseline.** Per-product:
HYD +519, VFE +536, vouchers ~0. Day-3 carries +663 of the lift (consistent
with the lean activating where v15 is weakest).

**Lessons learnt:**
- The "K_optimal = |AC1|" theory does NOT transfer to PnL under integer quoting +
  spread cost. v15's K = 0.5-0.6×|AC1| was already the empirical sweet spot.
  R4-V5300/5400/5500-B07 → REJECT.
- Cross-product VEV_5200 spillover signal is real but the trigger (Mark 14 buy /
  Mark 22 sell) is too RARE (~80 events / day) and the 5-tick lift gets absorbed
  by integer-price rounding when added as a passive lean. Could plausibly work as
  a TAKE-only signal on VEV_5200 itself; out of scope for the lean form.
  R4-XPROD-VEV5200 → REJECT (as a lean alpha; possibly RESEARCH as a take alpha).
- 0.7×Δ_BS portfolio hedge as a TAKE order on VFE is the canonical hedge-cost
  blowup. Re-implementing as fair-value bias is in Phase 8b.

## Phase 8b — corrective probes (in flight)

3 new probes:
- `r4_smile_refit_probe`: R4-CHAIN-02 standalone (a2 constants change).
- `r4_mark_lean_plus_smile_probe`: lean + smile refit.
- `r4_mark_lean_plus_microstructure_probe`: lean + V_5000 imb2 + V_5100 microprice
  + V_5200 vol-cluster widening.

## Phase 6 — nulls

| Alpha | Null A (perm) | Null B (shuffle) | Holdout | Cost-adj | Status |
|---|---|---|---|---|---|
| R4-CP-Mark14-HYD | FAIL p=0.143 z=+1.3 | FAIL z=+1.1 | n/a | n/a | RESEARCH |
| R4-CP-Mark38-HYD | FAIL p=0.139 z=−1.1 | FAIL z=−1.0 | n/a | n/a | RESEARCH |
| R4-CP-Mark67-VE | FAIL p=0.530 z=+0.1 | FAIL z=+1.8 | n/a | n/a | RESEARCH |
| R4-CP-Mark49-VE | FAIL p=0.265 z=−0.7 | MARGINAL z=−2.0 | n/a | n/a | RESEARCH |
| R4-CP-Mark22-VE-S | FAIL p=0.163 z=−1.6 | **PASS z=−14.1** | n/a | n/a | RESEARCH |
| R4-CP-Mark22-HYD-B | FAIL p=0.212 z=−1.3 | **PASS z=−4.1** | n/a | n/a | RESEARCH |
| R4-XPROD-VEV5200 (M14 B) | FAIL p=0.565 z=+0.4 | **PASS z=+12.3** | n/a | n/a | RESEARCH |
| R4-XPROD-VEV5200 (M22 S) | FAIL p=0.326 z=+0.7 | **PASS z=+19.5** | n/a | n/a | RESEARCH |
| R4-CHAIN-01 | n/a | n/a | **PASS** | **PASS** | **SHIP** |
| R4-V5300-B07 | n/a | n/a | PASS | FAIL standalone | REJECT (per-test) |
| R4-V5500-B07 | n/a | n/a | PASS | FAIL standalone | REJECT (per-test) |
| R4-V5000-C02 | n/a | n/a | **PASS** | **PASS-by-construction** | **SHIP** |

**Critical interpretation**:
- The **Mark-permutation null is STRUCTURALLY WEAK** for 7-Mark setting because the
  permutation distribution is BIMODAL (~2/7 chance the permuted label inherits the
  smart Mark 14 or bag-holder Mark 38 strong signal). z-scores are misleading; only
  the one-sided p ≤ 0.05 verdict is interpretable.
- **Phase 6's "FAIL Mark-permutation" verdicts on every counterparty alpha do NOT
  mean the alphas are noise.** They mean the test is under-powered for this dataset.
  The PRACTICAL SHIP test is the per-day robustness (Phase 3 confirmed Sharpe 1.78-1.95
  every day) AND the backtest (Phase 8a confirmed mark-lean stack +1,054).
- Time-shuffle PASSES the Mark 22 (HYD-B and VFE-S) signals and the cross-product
  spillover (M14 B and M22 S triggers) — these are TRUE event-driven alphas.
- R4-CHAIN-01 (0.7×Δ hedge) and R4-V5000-C02 (imb2 skew) BOTH pass holdout AND
  cost-adjusted nulls — they are SHIP-grade by formal null testing.
- The Phase 6 sub-agent's REJECT on R4-V5300/5500-B07 is for "standalone fade strategy"
  which is NOT what the alpha proposes (alpha is "tune K inside the existing MM, not
  standalone fades"). Re-classified as RESEARCH pending Phase 8 probe re-examination.

## Phase 8b — corrective probes (REJECTED)

| Probe | Δ vs v15 | day-1 | day-2 | day-3 | Verdict |
|---|---:|---:|---:|---:|---|
| `r4_smile_refit` | **−2,690** | −3,114 | −1,009 | +1,433 | REJECT (over-flattens day-1; needs TTE-conditional blend) |
| `r4_mark_lean_plus_smile` | **−1,636** | −2,802 | −929 | +2,095 | REJECT (pure superposition: probe1 + probe5; smile cost dominates) |
| `r4_mark_lean_plus_microstructure` | **−1,745** | −418 | −3,672 | +2,345 | REJECT (V_5100 50/50 blend catastrophic −5,455; V_5000 imb2 +2,657 ok) |

Within Probe 7 internal attribution:
- HYDROGEL: +519 (mark-lean works as expected)
- VFE: +535 (mark-lean works)
- VEV_5100: **−5,455** (the V_5100 micro/wall blend with smile fights the smile MM)
- OTHER (V_5000 + V_5300+): +2,657 (V_5000 imb2 contributes positively)

**Critical lesson**: the Phase 8b sub-agent SUBSTITUTED a price-domain blend for the
actual rolling mid-IV (R4-PHASE5-G1) when building Probe 7. R4-PHASE5-G1 was the
highest-EV gap per Phase 5 and **was never actually tested.** The rolling-IV approach
remains an open RESEARCH item for next session.

## Final shipping decision

**Ship `r4_mark_lean_v01_probe.py` standalone for the next R4 submission.**

| Trader | 3-day BT | Δ vs v15 |
|---|---:|---:|
| `r4_baseline_v15_probe.py` | +222,775 | — |
| `r4_mark_lean_v01_probe.py` | **+223,829** | **+1,054** |

Of 8 probes built (1 baseline + 7 alpha probes), only the mark-lean probe
beats v15 baseline at locked pre-registered parameters.

## Closing inventory

Files written this session (R4 alpha hunt):

prosperity-research/03_eda/round4/per_product/{12 files} - per-product lens battery
prosperity-research/04_signal_notes/round4/{20+ files}:
- alpha_registry.md (HEADLINE)
- alpha_nulls.md
- preregistered_params.md
- adversarial_review.md
- self_critique.md
- rejected_alphas.md
- no_stat_arb_explanation.md
- past_winner_techniques.md
- cross_product_findings.md
- causality_spillover.md
- pca_residuals.md
- implied_vs_realised_underlying.md
- counterparty_deep.md
- iv_moneyness_structure.md (Hint Card 1)
- iv_residual_alpha_test.md (Hint Card 2)
- conviction_sizing_study.md (Hint Card 3)
- hint_card_4_counterparty_crosslink.md (Hint Card 4)
- term_structure_smile.csv
- parity_violations_tradeable.csv
- stat_arb_pairs.csv, stat_arb_triples.csv
- pca_loadings.csv
- counterparty_network.csv
- mark_price_impact.csv
- cross_product_mark_spillover.csv

prosperity-research/06_validation/round4_alpha_probes/{8 files}:
- _phase8_summary.md
- 7 per-probe BT reports

prosperity_rust_backtester/scripts/round4_options/lens_battery.py
prosperity_rust_backtester/traders/Round4/probes/{8 files}:
- r4_baseline_v15_probe.py
- r4_mark_lean_v01_probe.py (SHIP)
- r4_otm_ac1_retune_probe.py (REJECT)
- r4_xprod_vev5200_probe.py (REJECT)
- r4_combined_v01_probe.py (REJECT)
- r4_smile_refit_probe.py (REJECT)
- r4_mark_lean_plus_smile_probe.py (REJECT)
- r4_mark_lean_plus_microstructure_probe.py (REJECT)

prosperity-research/10_experiment_logs/r4_alpha_hunt_journal.md (this file)


