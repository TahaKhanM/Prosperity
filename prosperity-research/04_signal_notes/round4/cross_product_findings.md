# Cross-product / voucher chain findings (Phase 2A)

Inputs: `voucher_panel.csv` (30,000 ticks), level-2 books in
`prosperity_rust_backtester/datasets/round4/prices_round_4_day_{1,2,3}.csv`.

## 2.1 Term-structure smile (TTE drift)

Re-fit per tick with `iv ∈ (1e-5, 2.0)` (drops stuck deep-ITM/OTM IVs that
clamp at the bisection bound). Bucket: day 1 → TTE=7, day 2 → 6,
day 3 → 5.

| TTE_d | a0 (ATM IV) | a1 (skew) | a2 (cvx) | σ_a0 | σ_a1 | σ_a2 |
|-------|-------------|-----------|----------|------|------|------|
| 7 | 0.2441 | −0.131 | 7.62 | 0.0063 | 0.152 | 0.75 |
| 6 | 0.2466 | −0.228 | 8.53 | 0.0067 | 0.201 | 1.03 |
| 5 | 0.2403 | −0.025 | 14.11 | 0.0101 | 0.154 | 1.21 |

Linear extrapolation: TTE=4 → (0.2398, −0.022, 16.58); TTE=3 →
(0.2379, +0.031, 19.82). ATM IV flat at ~0.24; skew non-monotonic;
**convexity rises sharply once TTE ≤ 5** (5σ jump from 8.5 to 14.1).
The published `vol_surface_coeffs.csv` for day 3 is **corrupted** by
K=6500 IVs pinned at 2.5; use the v2 fit above.

Stability test (freeze TTE=5 day-3 clean smile, apply on day 1 / TTE=7),
median |residual|: K=4500 0.10, K=5000 0.02, K=5100..5500 0.01–0.014,
K=6000 0.087, K=6500 0.272. Wings drift; ATM stable within 1.5 vol-pts.

CSV: `term_structure_smile.csv`.

## 2.2 Tradeable parity

Mid-based 11,849 violations collapse to **6 total** intrinsic-floor
breaches on best-ask (K∈{4000,4500} on day 2/3, all 1–2-shell edge).
Zero tradeable cap, zero monotonicity, zero butterfly. Parity is clean
on the executable side.

CSV: `parity_violations_tradeable.csv`.

## 2.3 Implied delta vs empirical 100-tick beta

Per tick: BS Δ from per-tick smile vs rolling 100-tick cov(ΔV,ΔS)/var(ΔS).
All 30 (day, K∈{4000..5400}) cells flag (med |Δ−β| > 0.05, |t|>25 with
n_eff = n/50 to discount overlap). Day-averaged numbers:

| K | med Δ | med β | |Δ−β| | t-range |
|---|-------|-------|------|---------|
| 4000 | 0.99 | 0.74 | 0.25 | 25–29 |
| 4500 | 0.99 | 0.67 | 0.32 | 40–45 |
| 5000 | 0.94 | 0.66 | 0.28 | 45–49 |
| 5100 | 0.84 | 0.59 | 0.25 | 48–49 |
| 5200 | 0.63 | 0.43 | 0.19 | 44–51 |
| 5300 | 0.37 | 0.26 | 0.11 | 30–37 |
| 5400 | 0.17 | 0.11 | 0.06 | 16–33 |

Smile-derived Δ systematically ~30 % above realised β (peak gap at
K=4500–5000). A trader hedging straight off BS Δ is persistently
over-hedged on direction. Likely sticky-strike vs sticky-delta: when S
moves the smile co-moves, lowering effective Δ. Microstructure noise is
a partial confound but the cross-strike monotonicity and 3-day stability
argue for a real adjustment.

## 2.4 VE → vouchers lead-lag

Same-tick r = 0.55–0.77 (peak K=5000/5100). Of the 600 (strike, day,
lag∈[−20..+20]\{0}) cells, 10 cross |t|>3 and the largest is r=−0.050
(day 1, K=4000, lag=−1). Day-3 lag=−2 cluster (K=4000/4500/5000/5200,
r≈−0.03..−0.04) is the most consistent pattern but well below any
tradeable threshold. **Confirms R3: no usable lead-lag.**

## 2.5 HYDROGEL ↔ VE

Same-tick r ∈ {+0.012, −0.005, −0.003}. Lagged: one cell |t|>3 (day 2
lag=−17, r=+0.031); noise.

**Conditional drawdown** (HYD drops >30 / 100 ticks → VE next 200):
- Day 1: n=849, mean=+0.62, t=+1.31
- Day 2: n=791, mean=+1.29, t=+4.45
- Day 3: n=908, mean=+3.64, t=+7.58

HYD-rally mirror: mean=+4.80/+3.10/−2.71, t=+9.6/+8.4/−7.4. **Both** large
HYD moves predict VE drift days 1/2; sign flips between drawdown/rally on
day 3. This is HYD-volatility predicting VE drift, not directional
spillover — likely an omitted-common-factor (basket-rebalance bot, volume
spike). Marginally usable; day-3 sign instability is a kill-risk.

## 2.6 Baskets

| Basket | mean (d1/d2/d3) | sd | half-life | t_mr | tradeable? |
|--------|-----------------|----|-----------|------|------------|
| 1: avg V_K − VE | −4990/−4996/−4990 | 7.4/8.3/9.4 | 115/149/161 | −5/−5/−5 | slow + noisy |
| 2: V_5200+V_5300 − V_5100−V_5400 | −38.6/−42.5/−48.8 | 1.1/2.1/1.4 | 5/19/9 | −27/−14/−20 | round-trip ~10 > 4σ |
| 3a: (V_4000+V_4500)/2 − VE | −4250 | 0.78–0.82 | n/a | −99 to −101 | identity |
| 3b: V_4000+V_4500 − 2 VE + 8500 | 0.03/0.01/0.00 | 1.55/1.54/1.65 | ~0 | −99 to −101 | mid-perfect; 3 hits/30k on tradeable |

Basket 3b is the cleanest deep-ITM identity (V_4000+V_4500−2 VE+8500 ≡ 0
at expiry once both vouchers ITM). Mid sits at 0 ± 1.6 but bid-ask round
trip is ~23 shells — **not directly executable**. Useful as a defensive
parity-guard alarm (alert outside ±5σ ≈ ±8 shells).

Basket 2 (1-2-1 fly) is genuinely mean-reverting but spread sd 1–2 cannot
beat the 9.5–10.6-shell round-trip. Basket 1 too slow + noisy.

## Candidate alphas (from this phase)

- **R4-CHAIN-01: Smile-Δ vs realised-β gap (sticky-strike correction)** —
  hedge V_K with `~0.7 × Δ_BS(S,K,T,σ_smile)` VE units rather than 1.0×.
  | mag = 0.06–0.32 Δ-points per strike → ~30 % less VE inventory burned
  per voucher hedge | t = 16–51 per (day, K) on per-tick mismatch
  | days = 1,2,3 | falsifier: if rolling 100-tick β > 0.95×Δ_BS for any
  5,000-tick segment of R4 day 1, kill it.

- **R4-CHAIN-02: Day-3 convexity spike (vol-surface deformation)** —
  use a2 = 14.1 (TTE=5), 16.6 (TTE=4 extrap), 19.8 (TTE=3 extrap) in the
  live smile, not the TTE=6 baseline 8.5. | mag = 5σ jump in a2 between
  TTE=6 and TTE=5; mispricing of wing strikes scales with a2 × m²
  | t = 5+ on coefficient | days = 3 | falsifier: if live a2 fitted on
  first 1,000 R4 day-1 ticks < 12, revert to TTE=6 surface.

- **R4-CHAIN-03: Deep-ITM parity guard (defensive)** — alarm when
  V_4000 + V_4500 − 2 VE + 8500 leaves ±8 shells. Near-zero base PnL,
  bounded loss per unit. | t for mean=0: |t|<2 on all days | days = 1,2,3
  | falsifier: > 1 % of live ticks outside ±5 shells means a leg is
  catastrophically mispriced; leg the trade.

- **R4-CHAIN-04: HYD-volatility → VE drift (weak)** — HYD drawdown >30
  / 100 ticks ⇒ VE +0.6/+1.3/+3.6 next 200 ticks (d1/d2/d3); HYD rally
  >30 ⇒ +4.8/+3.1/−2.7. | t = 1.3/4.5/7.6 (drawdown), 9.6/8.4/−7.4
  (rally) | days = 2,3 (day 1 weak) | falsifier: cross-day sign
  inconsistency on day 3 means risk-off only; deactivate if R4 day 1
  rally-event mean has wrong sign vs day-3.

## Dead alphas

- VE-voucher lead-lag (Section 2.4): all |r|<0.05.
- HYD-VE same-tick / short-lag (Section 2.5): |r|<0.03.
- Basket 2 1-2-1 butterfly: round-trip ~10 > 4σ deviation.
- Tradeable parity arb: 6 hits / 30K ticks, max edge 2 shells.
