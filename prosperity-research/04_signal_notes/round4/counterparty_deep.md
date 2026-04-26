# Counterparty deep-dive (Phase 3)

Stdlib-only. PnL = horizon-500 mid-move minus print.

## 3.1 Per-day breakdown — which signals survive?

Top by |total h500|. `conc` = max(|day_i|)/|total|. Robust = same sign all 3 days AND conc ≤ 0.70.

| Mark | product | side | n | day1 | day2 | day3 | total | conc | robust |
|---|---|---|---:|---:|---:|---:|---:|---:|:---:|
| Mark 38 | HYDROGEL_PACK | buyer | 515 | -6242 | -5216 | -5190 | -16649 | 0.37 | Y |
| Mark 14 | HYDROGEL_PACK | seller | 507 | +6208 | +5234 | +5207 | +16648 | 0.37 | Y |
| Mark 38 | HYDROGEL_PACK | seller | 507 | -6088 | -4729 | -5251 | -16068 | 0.38 | Y |
| Mark 14 | HYDROGEL_PACK | buyer | 496 | +6052 | +4708 | +5240 | +16001 | 0.38 | Y |
| Mark 55 | VELVETFRUIT_EXTRACT | seller | 600 | -3036 | -2406 | -2894 | -8336 | 0.36 | Y |
| Mark 55 | VELVETFRUIT_EXTRACT | buyer | 598 | -2461 | -2728 | -2272 | -7462 | 0.37 | Y |
| Mark 38 | VEV_4000 | seller | 233 | -1898 | -1312 | -1506 | -4716 | 0.40 | Y |
| Mark 14 | VEV_4000 | buyer | 232 | +1898 | +1312 | +1494 | +4704 | 0.40 | Y |
| Mark 14 | VELVETFRUIT_EXTRACT | buyer | 316 | +1628 | +1190 | +1420 | +4238 | 0.38 | Y |
| Mark 38 | VEV_4000 | buyer | 209 | -1572 | -1253 | -1388 | -4213 | 0.37 | Y |
| Mark 14 | VEV_4000 | seller | 207 | +1572 | +1253 | +1388 | +4213 | 0.37 | Y |
| Mark 01 | VELVETFRUIT_EXTRACT | buyer | 260 | +1419 | +1249 | +1444 | +4112 | 0.35 | Y |
| Mark 14 | VELVETFRUIT_EXTRACT | seller | 331 | +1174 | +1350 | +1326 | +3850 | 0.35 | Y |
| Mark 01 | VELVETFRUIT_EXTRACT | seller | 244 | +1307 | +1406 | +960 | +3673 | 0.38 | Y |
| Mark 67 | VELVETFRUIT_EXTRACT | buyer | 165 | +754 | +545 | +496 | +1796 | 0.42 | Y |
| Mark 49 | VELVETFRUIT_EXTRACT | seller | 105 | -499 | -388 | -430 | -1316 | 0.38 | Y |
| Mark 22 | VELVETFRUIT_EXTRACT | seller | 101 | -354 | -189 | -48 | -592 | 0.60 | Y |
| Mark 01 | VEV_6000 | buyer | 317 | +172 | +168 | +212 | +552 | 0.38 | Y |

29 / 57 edges robust by day-by-day filter.

## 3.2 Trade-level distribution — Mark 14 / Mark 38 on HYD / VE

| mark | prod | side | n | mean | std | skew | kurt | sharpe | top10%_share | total |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Mark 14 | HYDROGEL_PACK | buyer | 496 | +8.052 | 4.501 | -0.02 | -0.56 | +1.789 | +0.19 | +3994 |
| Mark 14 | HYDROGEL_PACK | seller | 507 | +8.112 | 4.158 | +0.05 | +0.37 | +1.951 | +0.19 | +4113 |
| Mark 14 | VELVETFRUIT_EXTRACT | buyer | 316 | +2.397 | 2.068 | -0.08 | +0.02 | +1.159 | +0.25 | +758 |
| Mark 14 | VELVETFRUIT_EXTRACT | seller | 331 | +2.201 | 2.197 | +0.11 | +0.12 | +1.002 | +0.28 | +728 |
| Mark 38 | HYDROGEL_PACK | buyer | 515 | -7.992 | 4.284 | +0.08 | +0.54 | -1.866 | +0.20 | -4116 |
| Mark 38 | HYDROGEL_PACK | seller | 507 | -7.908 | 4.578 | +0.03 | -0.54 | -1.728 | +0.19 | -4010 |

Top-10 % share near 0.10 = uniform / robust. > 0.40 = brittle.

## 3.3 Network (see counterparty_network.csv)

Counts: {'one_sided': 4, 'isolated_dyad': 4, 'mixed': 10, 'noise': 1}.

**Isolated dyads (MM pairs):**
- Mark 14 <-> Mark 38: n=728, qty=2447, buyer h500/u=+8.461
- Mark 38 <-> Mark 14: n=714, qty=2445, buyer h500/u=-8.532
- Mark 55 <-> Mark 14: n=331, qty=1763, buyer h500/u=-2.184
- Mark 55 <-> Mark 01: n=244, qty=1375, buyer h500/u=-2.671

**One-sided edges (flow signals):**
- Mark 01 -> Mark 22: n=1339, qty=4636, buyer h500/u=+0.550
- Mark 67 -> Mark 49: n=89, qty=963, buyer h500/u=+1.256
- Mark 67 -> Mark 22: n=75, qty=546, buyer h500/u=+1.071
- Mark 14 -> Mark 22: n=83, qty=302, buyer h500/u=+0.409

## 3.4 Conditional next-trade matrix (HYD+VE+VEV_4000, h=500 ticks)

Lift = P(Y prints in next 500 ticks | X just printed) / P(Y prints in any 500-tick window).

| X\Y | M01 | M14 | M22 | M38 | M49 | M55 | M67 |
|---|---|---|---|---|---|---|---|
| M01 | 4.13 | 4.47 | 4.42 | 5.00 | 4.39 | 4.27 | 5.41 |
| M14 | 4.64 | 4.37 | 4.27 | 4.73 | 4.47 | 4.43 | 4.96 |
| M22 | 3.62 | 3.59 | 4.11 | 4.29 | 6.65 | 3.55 | 4.91 |
| M38 | 4.55 | 4.33 | 4.43 | 4.67 | 4.70 | 4.41 | 5.34 |
| M49 | 4.39 | 4.24 | 6.65 | 4.53 | 2.02 | 4.52 | 5.96 |
| M55 | 4.47 | 4.48 | 4.23 | 4.99 | 4.52 | 4.28 | 5.16 |
| M67 | 3.61 | 3.57 | 3.69 | 3.60 | 2.98 | 3.95 | 3.31 |

**Top 4 off-diagonal lifts:**
- Mark 49 -> Mark 22: lift=6.65, P(Y|X)=0.03, n_X=122
- Mark 22 -> Mark 49: lift=6.65, P(Y|X)=0.03, n_X=148
- Mark 49 -> Mark 67: lift=5.96, P(Y|X)=0.03, n_X=122
- Mark 01 -> Mark 67: lift=5.41, P(Y|X)=0.03, n_X=504

## 3.5 Kyle's lambda (full table in mark_price_impact.csv)

lambda_h = E[dmid_signed]/qty (h ticks ahead). HYD prints, n>=30:

| mark | side | n | l_h1 | l_h5 | l_h20 | l_h100 |
|---|---|---:|---:|---:|---:|---:|
| Mark 14 | buy | 496 | +0.058 | +0.037 | +0.151 | +0.351 |
| Mark 14 | sel | 507 | +0.018 | +0.027 | +0.064 | +0.199 |
| Mark 38 | buy | 515 | -0.004 | -0.015 | -0.062 | -0.205 |
| Mark 38 | sel | 507 | -0.035 | -0.017 | -0.100 | -0.242 |

VE highlights (full file): Mark 67 buy +0.24/+0.24/+0.28/+0.26 (price-mover, also +1.19/u h500 PnL = informed). Mark 22 sell -0.24/-0.25/-0.24/-0.09 (paying impact). Mark 14 lambda is near-zero on VE despite +2.20/u h500 PnL = quote-sipper not impact-mover.

## 3.6 Order-book footprint — Mark 14 only, HYD + VE

Level-2 bid drop > 50% in prior 500 ticks before a Mark 14 buy. Lift > 1 = more than chance.

| product | n_prints | n_drops | cond | base | lift |
|---|---:|---:|---:|---:|---:|
| VELVETFRUIT_EXTRACT | 165 | 1 | 0.006 | 0.470 | 0.01 |
| HYDROGEL_PACK | 496 | 0 | 0.000 | 0.007 | 0.00 |

## 3.7 Cross-product spillover (see cross_product_mark_spillover.csv)

Source restricted to liquid (HYD/VE/VEV_4000-5200), n>=20. Cells tested: 660. Bonferroni: |t|>4.0 AND |lift|>=50% of unconditional SD. Surviving: **13**.

Top 6 by |t| (full list in CSV):

| mark | A | B | side | h | n | mean | t | lift |
|---|---|---|---|---:|---:|---:|---:|---:|
| Mark 22 | VEV_5200 | VEV_4000 | s | 5 | 46 | +5.087 | +20.8 | +216% |
| Mark 14 | VEV_5200 | VEV_4000 | b | 5 | 33 | +5.061 | +18.1 | +215% |
| Mark 22 | VEV_5200 | VEV_4500 | s | 5 | 46 | +3.783 | +15.2 | +168% |
| Mark 14 | VEV_5200 | VEV_4500 | b | 5 | 33 | +3.758 | +13.8 | +167% |
| Mark 22 | VEV_5200 | VEV_4000 | s | 20 | 46 | +5.957 | +7.3 | +138% |
| Mark 22 | VEV_5200 | VEV_5000 | s | 5 | 46 | +1.435 | +6.6 | +71% |

All 13 hits cluster on **VEV_5200 source**: Mark 14 buys / Mark 22 sells VEV_5200, and deeper-ITM vouchers (VEV_4000/4500/5000/5100) jump in the next 500-2000 ticks — a **smile-shift co-print** pattern. Treat as lead/lag of vega coupling, not exogenous prediction.

## Candidate alphas (from this phase)

- **R4-CP-Mark38-HYD-B**: Mark 38 buyer HYDROGEL, h500 PnL=-16649, conc=0.37, ~-32.33/trade. Falsifier: any day flips sign.
- **R4-CP-Mark14-HYD-S**: Mark 14 seller HYDROGEL, h500 PnL=+16648, conc=0.37, ~+32.84/trade. Falsifier: any day flips sign.
- **R4-CP-Mark38-HYD-S**: Mark 38 seller HYDROGEL, h500 PnL=-16068, conc=0.38, ~-31.69/trade. Falsifier: any day flips sign.
- **R4-CP-Mark14-HYD-B**: Mark 14 buyer HYDROGEL, h500 PnL=+16001, conc=0.38, ~+32.26/trade. Falsifier: any day flips sign.
- **R4-XPROD-Mark22-VEV-VEV-h5**: Mark 22 seller VEV_5200 -> VEV_4000 mid +5.087 (t=+20.8, lift=+216%, n=46). Falsifier: replicate day-3-only, t>2.5.
- **R4-XPROD-Mark14-VEV-VEV-h5**: Mark 14 buyer VEV_5200 -> VEV_4000 mid +5.061 (t=+18.1, lift=+215%, n=33). Falsifier: replicate day-3-only, t>2.5.
- **R4-XPROD-Mark22-VEV-VEV-h5**: Mark 22 seller VEV_5200 -> VEV_4500 mid +3.783 (t=+15.2, lift=+168%, n=46). Falsifier: replicate day-3-only, t>2.5.

