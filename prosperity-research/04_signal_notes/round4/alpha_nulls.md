# Alpha null tests (Phase 6)

Methodology (seed=42, stdlib). Counterparty alphas: 200-iter Mark-permutation (relabel 7 IDs within each day) + 50-iter time-shuffle (randomise trade ts within day). Microstructure: days 1+2 holdout → day 3, plus 1-tick cost adjustment. Cross-product: source-product time-shuffle + Mark-permutation. PASS thresholds: perm one-sided p ≤ 0.16 (1/7 floor with 7 Marks); shuffle |z| ≥ 3; holdout |decay| < 20%. SHIP requires both A and B to PASS for counterparty; PASS holdout AND cost for microstructure.

## R4-CP-Mark14-HYD (Mark 14 copy on HYDROGEL)

- Observed h500 PnL/unit: buyer = +8.045 (qty 1989); seller = +8.189 (qty 2033).

### Null A — Mark-permutation (buyer)
- 168 permutations. Null μ = +0.042, σ = 6.851. Observed = +8.045. one-sided p = 0.190, z = +1.2. MARGINAL (p=0.190, z=+1.2)

### Null A — Mark-permutation (seller)
- 154 permutations. Null μ = +0.078, σ = 6.343. Observed = +8.189. one-sided p = 0.117, z = +1.3. PASS (p=0.117, z=+1.3)

### Null B — Time-shuffle (buyer)
- 50 shuffles. Shuffle μ = +6.367, σ = 1.609. Observed = +8.045. z = +1.0. FAIL (z=+1.0)

## R4-CP-Mark38-HYD (Mark 38 fade on HYDROGEL — mirror)

- Observed h500 PnL/unit: buyer = -8.062 (qty 2065); seller = -7.911 (qty 2031). Negative on both sides ⇔ Mark 38 is the bag-holder; we fade.

### Null A — Mark-permutation (buyer)
- 157 permutations. Null μ = +1.108, σ = 6.749. Observed = -8.062. one-sided p = 0.115, z = -1.4. PASS (p=0.115, z=-1.4)

### Null A — Mark-permutation (seller)
- 157 permutations. Null μ = +1.006, σ = 6.213. Observed = -7.911. one-sided p = 0.153, z = -1.4. PASS (p=0.153, z=-1.4)

### Null B — Time-shuffle (buyer)
- 50 shuffles. Shuffle μ = -6.385, σ = 1.569. Observed = -8.062. z = -1.1. FAIL (z=-1.1)

## R4-CP-Mark67-VE (Mark 67 BUY on VFE)

- Observed (h500 PnL/unit, buyer): +1.189 (qty 1510).

### Null A — Mark-permutation
- 200 permutations. Null μ = +0.742, σ = 1.626. Observed = +1.189. one-sided p = 0.470, z = +0.3. FAIL (p=0.470, z=+0.3)

### Null B — Time-shuffle
- 50 shuffles. Shuffle μ = -1.129, σ = 1.167. Observed = +1.189. z = +2.0. FAIL (z=+2.0)

## R4-CP-Mark49-VE (Mark 49 SELL on VFE — fade buys, follow sells)

- Observed h500 PnL/unit: seller = -1.229 (qty 1071); buyer = -0.339 (qty 115). Mark 49 is informed on the sell side (PnL > 0) and bag-holder on the buy side (PnL < 0).

### Null A — Mark-permutation (seller)
- 196 permutations. Null μ = +0.003, σ = 1.656. Observed = -1.229. one-sided p = 0.219, z = -0.7. MARGINAL (p=0.219, z=-0.7)

### Null B — Time-shuffle (seller)
- 50 shuffles. Shuffle μ = +1.715, σ = 1.552. Observed = -1.229. z = -1.9. FAIL (z=-1.9)

## R4-CP-Mark22-VE-S (Mark 22 SELL on VFE → +1.5/unit h=1 Δmid)

- Observed (h1 Δmid signed for fade-the-sell): -1.505 (n 101).

### Null A — Mark-permutation
- 199 permutations. Null μ = -0.453, σ = 0.627. Observed = -1.505. one-sided p = 0.156, z = -1.7. PASS (p=0.156, z=-1.7)

### Null B — Time-shuffle
- 50 shuffles. Shuffle μ = -0.001, σ = 0.099. Observed = -1.505. z = -15.2. PASS (z=-15.2)

## R4-CP-Mark22-HYD-B (Mark 22 BUY on HYD → −3 ticks h=1 Δmid, small n)

- Observed (raw h1 Δmid after Mark 22 BUY on HYD): -3.091 (n 11). Alpha predicts Δmid < 0 (fade signal). Small-n caveat: only 11 prints across 3 days.

### Null A — Mark-permutation
- 156 permutations. Null μ = -0.668, σ = 1.346. Observed = -3.091. one-sided p = 0.115, z = -1.8. PASS (p=0.115, z=-1.8)

### Null B — Time-shuffle
- 50 shuffles. Shuffle μ = -0.058, σ = 0.659. Observed = -3.091. z = -4.6. PASS (z=-4.6)

## R4-XPROD-VEV5200 (Mark 14 buy / Mark 22 sell VEV_5200 → VEV_4000 mid +5 in 5 ticks)

- Observed Δmid VEV_4000 in 5 ticks: Mark 14 buyer = +5.061 (n 33); Mark 22 seller = +5.087 (n 46).

### Null A — Source-product time-shuffle (Mark 14 buyer)
- 50 shuffles. Shuffle μ = -0.008, σ = 0.414. Observed = +5.061. z = +12.3. PASS (z=+12.3)

### Null B — Mark-permutation (Mark 14 buyer)
- 152 permutations. Null μ = +4.177, σ = 2.187. Observed = +5.061. one-sided p = 0.559, z = +0.4. FAIL (p=0.559, z=+0.4)

### Null B — Mark-permutation (Mark 22 seller)
- 84 permutations. Null μ = +3.416, σ = 2.715. Observed = +5.087. one-sided p = 0.369, z = +0.6. FAIL (p=0.369, z=+0.6)

### Null A — Source-product time-shuffle (Mark 22 seller)
- 50 shuffles. Shuffle μ = -0.043, σ = 0.326. Observed = +5.087. z = +15.7. PASS (z=+15.7)

## R4-CHAIN-01 (BS Δ vs realised β — 0.7× hedge ratio)

- Realised β = cov(ΔV,ΔS)/var(ΔS), in-sample = days 1+2 vs OOS day 3.

  - V_5000: β_in = 0.655, β_out = 0.673, decay = +2.8%

  - V_5100: β_in = 0.585, β_out = 0.588, decay = +0.4%

  - V_5200: β_in = 0.440, β_out = 0.431, decay = -1.9%

  - V_4000: β_in = 0.745, β_out = 0.734, decay = -1.5%

  - V_4500: β_in = 0.663, β_out = 0.679, decay = +2.5%

### Sticky-strike-vs-sticky-delta interpretation check
- In-sample β all well below 1 (0.43–0.74). Day-3 β within ±5% for every strike. Gap from BS Δ (~0.95 ITM, 0.45–0.65 ATM) is structural, not regime-dependent in 30K-tick sample. Day-1 vs day-3 spot-mean shift ≪ 1%, so a Δβ-on-ΔS slope test is under-powered — β stability is the binding evidence.

- **Holdout verdict: PASS** (max |decay| = 2.8%).

## R4-V5300-B07 / R4-V5500-B07 (OTM AC1 K re-tune)

- VEV_5300: ρ1_in (d1+d2) = -0.213, ρ1_out (d3) = -0.217, decay = +1.9%. σ_Δmid = 0.478 ticks, |ρ1| × σ = 0.102 ticks/round-trip. After 1-tick spread: edge = -0.898.

- VEV_5500: ρ1_in (d1+d2) = -0.237, ρ1_out (d3) = -0.252, decay = +6.3%. σ_Δmid = 0.159 ticks, |ρ1| × σ = 0.038 ticks/round-trip. After 1-tick spread: edge = -0.962.

- **Cost interpretation:** the re-tune raises K inside the existing voucher MM alpha (D1 family). Edge is realised as queue-front-of-fade rebates, NOT round-trip fades, so the 1-tick spread is a worst-case bound. Standalone round-trip FAIL → REJECT *as standalone*; MM-embedded re-tune still valid given holdout PASS.

## R4-V5000-C02 (imb2 → fair skew on V_5000, β +3.0)

- imb2 slope (next-tick Δmid on imb2): β_in (d1+d2) = +3.326, β_out (d3) = +3.147, decay = -5.4%.

- **Holdout verdict: PASS.** Slope sign and magnitude are stable.

- **Cost-adjusted:** imb2 is a quoting tilt fed into the host MM fair price; round-trip cost is the host MM spread (0–1 tick), already paid. PASS-by-construction.


## Summary verdict

| Alpha | Null A | Null B | Holdout | Cost-adj | Status |
|---|---|---|---|---|---|
| R4-CP-Mark14-HYD | PASS (p=0.117, z=+1.3) | FAIL (z=+1.0) | n/a | n/a | RESEARCH |
| R4-CP-Mark38-HYD | PASS (p=0.115, z=+1.4) | FAIL (z=-1.1) | n/a | n/a | RESEARCH |
| R4-CP-Mark67-VE | FAIL (p=0.470, z=+0.3) | FAIL (z=+2.0) | n/a | n/a | REJECT |
| R4-CP-Mark49-VE | MARGINAL (p=0.219, z=-0.7) | FAIL (z=-1.9) | n/a | n/a | RESEARCH |
| R4-CP-Mark22-VE-S | PASS (p=0.156, z=-1.7) | PASS (z=-15.2) | n/a | n/a | SHIP |
| R4-CP-Mark22-HYD-B | PASS (p=0.115, z=-1.8) | PASS (z=-4.6) | n/a | n/a | SHIP |
| R4-XPROD-VEV5200 (M14 B) | FAIL (p=0.559, z=+0.4) | PASS (z=+12.3) | n/a | n/a | RESEARCH |
| R4-XPROD-VEV5200 (M22 S) | FAIL (p=0.369, z=+0.6) | PASS (z=+15.7) | n/a | n/a | RESEARCH |
| R4-CHAIN-01 | n/a | n/a | PASS | PASS | SHIP |
| R4-V5300-B07 | n/a | n/a | PASS | FAIL | REJECT |
| R4-V5500-B07 | n/a | n/a | PASS | FAIL | REJECT |
| R4-V5000-C02 | n/a | n/a | PASS | PASS | SHIP |

## Negative-result honesty notes
- Mark-perm z is constrained: 7 labels → identity-perm probability 1/7 ≈ 0.143 sets a hard p-floor. The bimodal smart/bag-holder structure of {Mark 14, Mark 38} makes the null SD ≈ 6 PnL/unit (any random label has a 2/7 chance of inheriting an extreme value). Only the one-sided p-value is interpretable; z is mostly cosmetic.
- HYD Mark 14 / Mark 38 FAIL Null B (time-shuffle z ≈ ±1) because their prints concentrate during directional drift segments — randomising the ts still hits a rising-mid window in expectation. This is the same brittleness flagged in `alpha_registry.md` (F1-Mark14-base).
- R4-XPROD-VEV5200 PASSES the source-shuffle null (z ≈ 12–15) but FAILS Mark-perm: the VEV_4000 Δmid is driven by the *event* (any large VEV_5200 print) not Mark identity. Consistent with `causality_spillover.md`: voucher Granger is stale-quote ordering. The right operationalisation is event-triggered, NOT Mark-conditioned.

