# Rejected R4 alphas — do NOT re-test without new evidence

A negative result is itself an artefact. This file lists every R4 alpha
that was tested and rejected, with the rejection reason. Future sessions
should consult this BEFORE spending cycles re-deriving these.

## Hard rejects (reproducible negative results)

### Stat-arb / cointegration

- **VE ↔ VEV_K linear cointegration** for K ∈ {5000..5500}: cointegrated
  in-sample (R² 0.71-0.82) but OOS Sharpe NEGATIVE when day-1 β is applied
  to days 2-3. Residual variance >> mean reversion. (Phase 2B)
- **VEV_4000 ↔ VEV_4500 cointegration**: passes ADF but is a tautology
  (both = VE − K). Spread = constant, no edge. (Phase 2B)
- **5 (VE, K1, K2) cointegrating triples**: HL ≤ 5 ticks, degenerate
  replication, no curvature MR. (Phase 2B)
- **1-2-1 butterfly basket V_5200+V_5300−V_5100−V_5400**: mean-reverts
  (HL 5-19) but spread sd 1.1-2.1 vs 9.5-10.6-shell round-trip cost. (Phase 2A)
- **Average-voucher-vs-VE basket**: too slow (HL 115+) and noisy (sd 7-9). (Phase 2A)

### Lead-lag

- **VFE → voucher cross-asset lead-lag**: same-tick corr 0.55-0.77 (peak K=5000),
  all lags |ρ| < 0.05. Confirmed dead at every k = ±1..±20. (Phase 1, Phase 2A)
- **HYDROGEL ↔ VE same-tick correlation**: |ρ| ∈ {0.012, −0.005, −0.003}.
  Lagged: one cell |t| > 3 (day 2 lag=−17, ρ=+0.031); noise. (Phase 2A)
- **Voucher AR(2+) structure beyond ρ1**: ρ2..ρ50 all |ρ| < 0.025 across
  every voucher. The 1-tick AC1 fade in v15 captures the entire AC alpha. (Phase 1)

### Counterparty

- **Mark X → Mark Y next-trade as standalone alpha**: lifts ~3-7× baseline
  but reflect a global "all Marks print near each other" cadence (the
  prosperity bot herd). The off-diagonal max (Mark 49 ↔ Mark 22, lift 6.65)
  has only n=4 hits — noise. (Phase 3.4)
- **Mark 14 bid-vacuum signal**: lift = 0.0 / 0.01 on HYD / VE for level-2
  bid disappearance before Mark 14 buy. Mark 14 does NOT strip liquidity. (Phase 3.6)
- **Counterparty time-of-day gating**: peak hour-bucket share ≤ 14 % for
  every Mark; weak temporal structure. Do NOT gate on hour. (R4 EDA)
- **Mark 14 / Mark 38 Per-tick conditional Δmid t-stat for HYD**: brittle
  per-day (t = ±1.8 / ±0.4 / ±1.3). RECONCILED: the per-trade horizon-500
  PnL IS robust (t ~24 over 30k obs). The per-tick t-stat is noisy due to
  HYD's high microstructure variance; the SIGNED HORIZON h500 PnL is the
  right metric. NOT a true reject — just a metric-choice clarification. (Phase 1 vs Phase 3)

### Microstructure

- **HYDROGEL spectral 3330-tick rhythm**: R3-day-0-only artefact. R4 days
  1/2/3 have no stable peak (Goertzel: 5000 / 1603 / 5000). Reject. (Phase 1)
- **HYDROGEL 1-tick AC1 fade** (carry-over reject): ρ1=−0.124 every R4
  day, but spread cost 8/RT >> revert edge ~0.27/RT. Same outcome as R3. (Phase 1)
- **HYD imb_k3 multivar skew**: signal is too narrow (std 0.016, 95% q=0);
  rarely fires. Already in v15-rejected list. (R3 reject; reconfirmed Phase 1)
- **Microprice fair on VFE**: micro β=0.28 vs wall-mid β=0.78. Wall-mid
  dominates; microprice does NOT add lift. (Phase 1)
- **AR(2+) fade on V_5000/5100/5200/5300/5400/5500**: ρ2..ρ50 all <0.025;
  no longer-horizon AC alpha beyond v15's 1-tick fade. (Phase 1)
- **Vol-cluster MM widening on V_5000 / V_5100**: AC1 of 100-tick rolling
  vol unstable across days (sign flips). Day-2 break is fatal. (Phase 1)
  - V_5200 vol-cluster IS a candidate (AC1 = 0.51/0.45/0.39 stable) — see
    R4-V5200-F01 in registry.
- **per-strike static IV bias dict (v15's R3-tuned values)**: STALE on R4
  day 3. e.g. V_5200 bias should be +0.085 (R3 had +0.0076). The right fix
  is rolling mid-IV (R4-PHASE5-G1), NOT re-tuning the static dict per-day.

### Cross-product / structural

- **Tradeable parity arb on best-ask/best-bid**: 6 hits / 30,000 ticks, max
  edge 2 shells. G1 already covers this defensively. NOT directly tradeable
  for sustained PnL. (Phase 2A)
- **VEV_4000+VEV_4500 − 2·VE + 8500 identity arb**: mid-perfect (sd 1.55-1.65)
  but bid-ask round-trip ~23 shells. Repurposed as R4-CHAIN-03 alarm. (Phase 2A)
- **Implied-vs-realised underlying mismatch**: LOO smile-fit residual is
  consistently negative but magnitude scales with shrinking TTE → confirms
  parabola extrapolation bias, NOT market dislocation. (Phase 2B)
- **PCA residuals**: PC1+PC2 residuals have ρ1 ≈ −0.29 to −0.47 but this
  just reproduces the per-product spread-bounce already in B1/C1. No NEW
  stat-arb leg. (Phase 2B)
- **HYDROGEL ↔ VE Granger causality**: F < 1.6 both directions →
  independent factors. (Phase 2B)
- **VE ↔ ATM-voucher Granger F is large but symmetric** → contemporaneous
  co-movement, not lead-lag alpha. (Phase 2B)
- **Volatility cross-correlation lead-lag**: peak at lag 0 across all
  product pairs; no vol leakage with non-zero lag. (Phase 2B)

### Stuck strikes

- **VEV_6000 / VEV_6500 stuck-strike scalping**: std=0, no microstructure.
- **VEV_6000 / VEV_6500 tail trade (long)**: P(S_T > 6000) ≈ 1.1×10⁻⁷ at
  TTE=4d; mid 0.50 is RICH (~50,000× over fair). EV = −0.50/contract.
  REJECT. (Phase 1)
- **VEV_6000 vs VEV_6500 differential**: trade rows byte-identical (same
  Mark 01 ↔ Mark 22 events fire both strikes synchronously). Nothing to
  spread-trade. (Phase 1)

### Deep-ITM (V_4000 / V_4500)

- **Synthesise short VE via V_4000 / V_4500 ask**: VE spread (5) < V_4000
  spread (21) and < V_4500 spread (16). Deep-ITM is STRICTLY WORSE
  execution for VE-equivalent. E1 is only useful for VE-cap-binding overlay,
  not direct VE expression. (Phase 1)
- **β-residual fade on V_4000 / V_4500**: AC1 −0.46 to −0.49 (strong) BUT
  spread (16-21) > edge (~0.3 ticks). Posted-quote alpha only; reject for
  the take-side trader. (Phase 1)

### Per-strike / chain
- **Mark 14 stand-alone fade on V_5500**: n=7 across 3 days, t=−1.6 at h=5.
  Underpowered. (Phase 1)
- **Mark 55 fade on V_5500**: 0 trades on V_5500 in R4 historical (despite
  R3-era playbook flag). Rule does not apply to R4 data. (Phase 1)

## Soft rejects (failed Bonferroni; keep on watch list)

- **R4-V5300-D02 (Mark 14 V_5300 fade)**: t = −2.5 (n=30); below the
  Bonferroni threshold (~3.5) for the 670-test counterparty grid. Downgraded
  from the candidate list to research-watch.
- **R4-V5400-D02 (Mark 14 V_5400 fade)**: t = −3.3 borderline.
- **R4-CHAIN-04 (HYD-vol → VE drift)**: t = 1.3/4.5/7.6 (drawdown), day-3
  sign-flip on rally side. NOT robust enough for ship.

## What this means for v15

v15 has these REJECTED alphas already coded as "do not enable" — confirmed
to still be the right call on R4. No regression here.
