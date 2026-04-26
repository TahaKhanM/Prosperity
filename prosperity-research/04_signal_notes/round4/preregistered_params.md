# Pre-registered parameters for R4 alpha probes

This file LOCKS the parameter values for each candidate alpha BEFORE the
backtest runs. Pre-registration is the rule that keeps us out of the v12
overfit trap (one-day BT tune that blew up out-of-sample). v15 won by being
robust across hyperparameters — we keep that discipline.

Process:
1. For each alpha, write the value, the reason (theoretical or from data
   summary statistics, NOT from a BT sweep), and the equally-defensible
   range I would accept if a stability check forced a perturbation.
2. Run the backtest with the locked value.
3. If the BT sweep prefers a value OUTSIDE the equally-defensible range,
   STOP and investigate before adopting (probable overfit).

Last updated: 2026-04-26 (Phase 1 + Phase 5 complete; Phase 2 / 3 in flight).

## R4-VFE-M01 — Copy Mark 67 buy on VE

Value:    `LEAN_PER_QTY_M67 = 0.10` lean per unit of Mark 67 buy quantity.
Reason:   Per-Mark 67 buy print (mean qty 9), Δmid_{t+1} = +2.0 across 3
          days (t > 13). One unit lean → +1 tick fair-value bias.
          Setting LEAN_PER_QTY = 0.10 makes a 9-lot print add ~+0.9 tick
          bias, ~half the observed +2.0 — conservative.
Range:    [0.05, 0.20] equally defensible. Below 0.05 the signal is wasted;
          above 0.20 a single 15-lot print would saturate the lean clamp.
Decay:    `DECAY_PER_TICK = 0.985` (half-life ≈ 46 ticks). Aligns with
          the Phase 1 conditional-return horizon (h=1 robust, h=20 still
          positive but smaller).
Range:    [0.97, 0.995] (HL 23–139 ticks).
Clamp:    `LEAN_CLAMP_VFE = 3.0` ticks of fair-value bias.
Range:    [2.0, 5.0].

## R4-VFE-M02 — Copy Mark 49 sell on VE

Value:    `LEAN_PER_QTY_M49 = 0.10` lean per unit of Mark 49 sell qty,
          NEGATIVE direction (we go short / lean fair down).
Reason:   Mark 49 sell mean qty 10, Δmid_{t+1} = +1.9 across 3 days
          (Mark 49 sells = price goes UP, so we should LEAN LONG VE
          when Mark 49 sells, NOT fade). Re-check the sign carefully:
          per Phase 1 sub-agent, "Mark 49 sell h=1: +1.88/+1.76/+2.07"
          means after Mark 49 SELLS, mid moves UP. So copying = lean +VE.
          NOTE: The per-product table says Mark 49 sell PnL/unit = −1.229
          (informed seller — they GAVE AWAY value), so going LONG after
          they sell IS the right side. Sign confirmed.
Range:    [0.05, 0.15].
Decay:    Same as M01.

## R4-VFE-M03 — Copy Mark 22 sell on VE

Value:    `LEAN_PER_QTY_M22 = 0.05` (half of M01/M02 because day-3 t = +3.1).
Reason:   Mark 22 sell mean qty 7, Δmid_{t+1} = +1.5 days 1-2, +1.25 day 3.
          Day-3 weakening warrants a smaller lean; if we used the same
          0.10 we'd over-weight a fading signal.
Range:    [0.025, 0.10].

## R4-HYD-M01 — Fade Mark 22 buy on HYDROGEL

Value:    `LEAN_PER_QTY_M22_HYD = 0.20` (NEGATIVE direction).
Reason:   Mark 22 buys 3-9× per day on HYD. h=1 Δmid = −3.17/−3.88/−2.25.
          A 4-lot print with 0.20 weight gives 0.8-tick bias DOWN,
          conservative vs the observed −3 ticks.
          Capacity is small (3-9 prints/day × 4 qty = ~30 lots/day total).
Range:    [0.10, 0.40].
Decay:    DECAY_PER_TICK = 0.985 (HL ~46 ticks; signal dies after the
          1-5 tick window per Phase 1).
Clamp:    1.5 ticks (small capacity, no need for big clamp).

## R4-VFE-F01 — Bump VFE wall_vol_thr 20 → 22

Value:    `WALL_VOL_THR_VFE = 22` (was 20 in v15).
Reason:   Phase 1 found bv1 modes at qty 21/22/23 with ~480 occurrences
          each. The threshold-20 includes ~3 % more "thin" levels; a
          22-threshold filters the noise floor while still capturing the
          modal levels.
Range:    [21, 25] equally defensible. Anything below 20 starts including
          retail-sized quotes; above 25 we lose the mode at 21.
Falsifier: B1 PnL drops > 5 %.

## R4-V5300-B07 / V5400-B07 / V5500-B07 — Re-tune AC1 fade K

Value:    `AC1_FADE_K_5300 = 0.21` (was 0.12).
          `AC1_FADE_K_5400 = 0.25` (was 0.15).
          `AC1_FADE_K_5500 = 0.24` (was 0.15).
Reason:   v15's K is exactly the absolute value of the empirical AC1
          (R3 fits). R4 measurements show AC1 = −0.214 / −0.249 / −0.242,
          so K should be the same magnitude (Phase 1 sub-agent claim).
          Optimal K under the linear fade model = |AC1| (the regression
          coefficient that maximally explains next-tick mid change).
Range:    K within ±15 % of the measured |AC1|. So 0.18-0.24 (V_5300),
          0.21-0.29 (V_5400), 0.20-0.28 (V_5500).
Falsifier: per-strike BT std(mid − fair) does NOT drop ≥ 3 % vs v15.

## R4-V5000-C02 — imb2 skew on VEV_5000

Value:    `IMB2_K_5000 = +3.0` ticks per unit imb2.
Reason:   Median across 3 days of measured β = (3.05 + 3.59 + 3.15) / 3 = 3.26.
          Round down for conservatism + cap at SKEW_CAP_VEV.
Range:    [2.0, 4.0].
Cap:      `SKEW_CAP_VEV = 1.0` tick (analogous to VFE V_SKEW_CAP).

## R4-V5100-C01 — Microprice + wall blend on VEV_5100

Value:    `MICRO_W_5100 = 0.30` (fair = 0.30·micro + 0.70·wall).
Reason:   Phase 1 sub-agent: microprice β = +0.264 with t > +21 across days.
          Wall β = +0.58, t = +25-27. The information overlap is large but
          micro adds a marginal predictive bump. 0.30 weight is the lower
          bound of useful blends; 0.50 risks over-weighting micro on
          unbalanced books.
Range:    [0.15, 0.50].

## R4-V5200-F01 — Vol-cluster MM widening

Value:    `VOL_WIDEN_THR_5200 = pct(rolling_vol_100, 0.90)` → widen quote
          edge by +2 ticks when last-100-tick rolling vol exceeds the 90th
          percentile of the day-1 distribution.
Reason:   Phase 1 sub-agent: rolling-vol AC1 0.51/0.45/0.39 across days.
          Widen-on-burst is a defensive move that limits adverse-selection
          loss, not a directional alpha. Threshold 90th pct = ~10 % of
          ticks fire it; >95th pct fires too rarely.
Range:    [85th, 95th]. Below 85th it widens too often; above 95th too rare.

## R4-V5200-D02 — Day-3 IV residual upward bias

Value:    Bias-up V_5200 fair by +0.05 vol points when (TTE_days - timestamp/1e6) ≤ 4.5.
Reason:   Phase 1 sub-agent: d3 mean residual +0.085, std 0.024, ~6σ.
          A +0.05 bias is conservative (50-60 % of the observed bias);
          if Phase 2A confirms via the rolling-mid-IV approach this should
          be deprecated in favour of the more general per-strike rolling IV.
Range:    [0.0, 0.10]. Could be 0 if Phase 2 says rolling-IV is better.
Status:   Deprecate in favour of R4-PHASE5-G1 if Phase 2 confirms.

## R4-V5300-D02 / R4-V5400-D02 — Fade Mark 14 buy on V_5300/V_5400

Value:    `LEAN_PER_QTY_M14_V53XX = -0.05` (NEGATIVE — fade).
Reason:   Sample size n=30 (V_5300) / n=13 (V_5400). t=−2.5/−3.3.
          Conservative weighting at half the M-on-VFE values.
Range:    [-0.10, 0.0].
Capacity: Note that V_5300 and V_5400 have positions limit 300 each
          but daily Mark 14 traffic is only 13-30 prints — capacity small.

## R4-V5300-C03 — IV residual EMA(20) → EMA(2)

Value:    `IV_RES_EMA_HL = 2 ticks` (was 20 in v15).
Reason:   Phase 1: true HL is 0.2-0.5 ticks. EMA(2) ≈ smoothing param
          1 - exp(-ln 2 / 2) ≈ 0.29 vs current EMA(20) ≈ 0.034.
Range:    [1, 5] ticks. EMA(20) is too slow.
Falsifier: D1 hit rate does NOT improve ≥ 1.5 %.

## R4-V5500-D03 — Widen V_5500 quotes after motion

Value:    Widen quote edge +2 ticks if any |Δmid| > 0 in past 10 ticks.
Reason:   Phase 1: |ret| AC1 = 0.37 on day 3. After a non-zero move,
          P(another non-zero move next 10 ticks) is elevated → widen
          to avoid getting picked off.
Range:    [+1, +3] ticks of widening; window [5, 20] ticks.

## R4-V5500-F04 — Stale-book guard

Value:    Pull quotes after 300 ticks of unchanged mid.
Reason:   Phase 1: longest run unchanged d3 = 909 ticks. Quoting in a
          dead book invites adverse selection from the rare informed flip.
Range:    [200, 500] ticks. Below 200 it triggers too often; above 500
          we sit through the 909 outlier.

## R4-PHASE5-G1 — Per-strike rolling mid-IV fair

Value:    `ROLLING_IV_HL = 60 ticks` (rolling-mean half-life of mid-IV).
Reason:   CMU Physics' working setup was a short window. 60 ticks ≈ 6
          seconds of game time; enough to smooth quote-bouncing noise,
          short enough to track the smile. v15's static bias dict
          assumes infinite-window stability → broken on R4.
Range:    [20, 200] ticks.
Falsifier: per-strike residual MAE on R4 day-3 must drop vs v15
          static-bias TTE-fit.

## R4-PHASE5-G2 — Microprice fair on HYDROGEL

Value:    `MICRO_W_HYD = 0.20` blended into v15's anchor+wall+EMA.
Reason:   Phase 1 sub-agent showed microprice β = +2.72 t = +30 on HYD
          (a per-tick predictor), but wall-mid β = +0.85 t = +36
          dominates. 0.20 micro weight is conservative.
Range:    [0.10, 0.40].

## R4-PHASE5-G3 — Mark14-Mark38 aggressor-sign cumulant

Value:    `AGGR_SIGN_DECAY = 0.99` (HL ~70 ticks).
          `AGGR_SIGN_K_HYD = 1.0` ticks per unit cumulant.
Reason:   This is a higher-frequency variant of the per-Mark lean. By
          accumulating sign over a window, it fires on streaks, not
          single prints. v15's lean is single-print only.
Range:    DECAY [0.97, 0.995]; K [0.5, 2.0].
Falsifier: Granger F-stat on 5-tick-fwd HYD return must clear p < 0.05
          on day-3 holdout.

## R4-CP-Mark14-HYD / R4-CP-Mark38-HYD (the headline counterparty alphas)

Combined into a single per-(Mark, product) lean parameter set:

Value:    `LEAN_PER_QTY_M14_HYD = 0.20` (positive on Mark 14 buy / Mark 38 sell).
          `LEAN_PER_QTY_M38_HYD = 0.20` (negative on Mark 38 buy / Mark 14 sell —
                                          symmetric, halved noise).
Reason:   Phase 3 confirmed per-trade Sharpe 1.78-1.95, h500 PnL ~+8/-8/unit
          for Mark 14 buy / Mark 38 buy with 0.37-0.38 day concentration (robust).
          A 4-lot print with 0.20 weight gives ~+0.8 tick fair-value bias —
          conservative vs the +8 horizon move.
Range:    [0.10, 0.40].
Decay:    DECAY_PER_TICK = 0.985 (HL 46 ticks; matches the multi-hundred-tick
          horizon over which mid drifts).
Clamp:    LEAN_CLAMP_HYD = 5.0 ticks.

## R4-XPROD-VEV5200 — vega-coupling cross-strike spillover

Value:    `XPROD_K_4000 = 1.00` ticks per unit Mark print on VEV_5200.
          `XPROD_K_4500 = 0.70`.
          `XPROD_K_5000 = 0.30`.
          `XPROD_K_5100 = 0.20`.
Reason:   Phase 3 measured: Mark 22 sell VEV_5200 → VEV_4000 mid +5.087 within
          5 ticks (lift 216 % of unconditional SD). Mark 14 buy mirror.
          Decomposition: a 5-lot Mark print → +5 tick mid move → 1.0 tick lean
          per print-unit on K=4000 captures 100% of the move at qty=5; we use
          0.10 per qty (so 5-lot print → 0.50 ticks lean); conservative.
          Per-strike scaling from cross-product CSV magnitudes (V_4000 +5.09,
          V_4500 +3.78, V_5000 +1.43, V_5100 +1.01).
Range:    Magnitudes ±30 % of measured.
Decay:    XPROD_DECAY = 0.95 (HL ~14 ticks; spillover empirically resolves in
          5-100 ticks).
Clamp:    XPROD_LEAN_CLAMP = 5.0 ticks per strike.
Trigger:  ONLY when Mark 14 BUYS VEV_5200 OR Mark 22 SELLS VEV_5200 (the
          dyad's print on the source). Other Marks on VEV_5200 do NOT trigger
          (Mark 38 prints rare; Mark 01 trades VEV_5200 are noise).
Falsifier: in live combined.log, the next-5-tick conditional Δmid on V_4000
          drops < 1.5 → suspend.

## R4-CHAIN-01 — sticky-strike Δ adjustment (0.7× hedge ratio)

Value:    `HEDGE_RATIO = 0.70` (multiply BS Δ by 0.70 when computing portfolio
          delta for hedging).
Reason:   Phase 2A measured BS Δ vs realised 100-tick β across 30 (day, K)
          cells: median |Δ−β| = 0.06-0.32 with t = 16-51 per cell. β is
          systematically 70 % of Δ_BS (sticky-strike vs sticky-delta in the
          R4 dataset). v15 doesn't currently hedge at all (relies on smile-MM
          + accumulation block); when we add hedging in `r4_combined_v01_probe.py`
          it should use 0.70× ratio not 1.00× to avoid over-hedge bleed.
Range:    [0.60, 0.85].
Falsifier: rolling 100-tick β / Δ_BS > 0.95 over any 5,000-tick segment of
          R4 day 1 → revert to 1.00× ratio.

## R4-CHAIN-02 — Day-3 convexity refit

Value:    `SMILE_A2_BASE = 7.62` (was 7.21 in v15).
          `SMILE_A2_DRIFT_PER_DAY = 1.62` (was 0.815 in v15).
Reason:   Phase 2A measured a2 = 7.62 / 8.53 / 14.11 across TTE 7/6/5.
          Linear fit slope = (14.11 - 7.62) / 2 = 3.25 per day, but the
          convexity SPIKES at TTE = 5 — a 5σ jump from TTE = 6's 8.53.
          Conservative: use a piecewise-linear with slope 0.91/day for
          TTE > 5 and 5.58/day for TTE ≤ 5 (matches the data exactly).
          Simpler: a single drift of 1.62/day matches better than v15's
          0.815/day on R4.
Range:    [1.0, 3.0] for the drift; base [7.0, 8.5].
Falsifier: live a2 fitted on first 1,000 R4 day-1 ticks < 12 → revert to
          v15 baseline (7.21, 0.815).

## R4-CHAIN-03 — Deep-ITM parity guard (defensive)

Value:    Alarm when `V_4000 + V_4500 − 2·VE + 8500` leaves ±8 shells.
Reason:   Phase 2A measured: under no-arb, this expression is exactly 0
          if both vouchers are ITM. Mid sits at 0 ± 1.6 across 30k ticks;
          ±8 shells = ~5σ. Tradeable round-trip cost ~23 shells, so this
          is an ALARM (don't auto-trade), not a position.
Range:    [±5, ±10] shells.
Falsifier: > 1 % of live ticks outside ±5 shells → an upstream leg is
          mispriced; investigate before auto-trading.
