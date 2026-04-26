# Round 4 Headline Findings

## 1. Smart-bot ranking (total horizon-500 PnL across all products, 3 days)

| Mark | Buy qty | Sell qty | Tot PnL h500 | PnL/unit h500 | Tot PnL h2000 | Products |
|---|---|---|---|---|---|---|
| Mark 14 | 4510 | 4208 | +49777 | +5.710 | +49058 (+5.631) | 7 |
| Mark 01 | 6053 | 1375 | +10334 | +1.391 | +10044 (+1.352) | 7 |
| Mark 67 | 1510 | 0 | +1796 | +1.189 | +1551 (+1.027) | 1 |
| Mark 49 | 115 | 1071 | -1356 | -1.143 | -1328 (-1.120) | 1 |
| Mark 22 | 206 | 5683 | -3058 | -0.519 | -3012 (-0.511) | 12 |
| Mark 55 | 3254 | 3297 | -15798 | -2.411 | -14330 (-2.187) | 1 |
| Mark 38 | 2493 | 2507 | -41696 | -8.339 | -41983 (-8.407) | 7 |

## 2. Volume rank (gross qty)

- Mark 14: buy 4510 / sell 4208 (gross 8718)
- Mark 01: buy 6053 / sell 1375 (gross 7428)
- Mark 55: buy 3254 / sell 3297 (gross 6551)
- Mark 22: buy 206 / sell 5683 (gross 5889)
- Mark 38: buy 2493 / sell 2507 (gross 5000)
- Mark 67: buy 1510 / sell 0 (gross 1510)
- Mark 49: buy 115 / sell 1071 (gross 1186)

## 3. Counterparty-pair graph (top 15 pairs by trade count)

| Buyer | Seller | n_trades | total_qty |
|---|---|---|---|
| Mark 01 | Mark 22 | 1339 | 4636 |
| Mark 14 | Mark 38 | 728 | 2447 |
| Mark 38 | Mark 14 | 714 | 2445 |
| Mark 55 | Mark 14 | 331 | 1763 |
| Mark 14 | Mark 55 | 316 | 1761 |
| Mark 01 | Mark 55 | 260 | 1417 |
| Mark 55 | Mark 01 | 244 | 1375 |
| Mark 67 | Mark 49 | 89 | 963 |
| Mark 14 | Mark 22 | 83 | 302 |
| Mark 67 | Mark 22 | 75 | 546 |
| Mark 38 | Mark 22 | 19 | 48 |
| Mark 22 | Mark 55 | 18 | 92 |
| Mark 22 | Mark 38 | 17 | 60 |
| Mark 55 | Mark 22 | 14 | 62 |
| Mark 49 | Mark 22 | 12 | 89 |

## 4. Temporal concentration

| Mark | Total trades | Peak bucket | Peak n | Peak share | Bucket histogram (0..9) |
|---|---|---|---|---|---|
| Mark 49 | 122 | 8 | 17 | 13.9% | [11, 15, 14, 11, 10, 7, 8, 16, 17, 13] |
| Mark 22 | 1584 | 3 | 196 | 12.4% | [187, 136, 127, 196, 137, 195, 175, 161, 150, 120] |
| Mark 67 | 165 | 9 | 20 | 12.1% | [17, 18, 18, 15, 11, 13, 16, 19, 18, 20] |
| Mark 38 | 1478 | 3 | 178 | 12.0% | [126, 171, 155, 178, 144, 138, 142, 136, 134, 154] |
| Mark 01 | 1843 | 5 | 216 | 11.7% | [212, 166, 150, 214, 167, 216, 197, 189, 179, 153] |
| Mark 14 | 2172 | 3 | 247 | 11.4% | [188, 227, 231, 247, 219, 205, 205, 217, 214, 219] |
| Mark 55 | 1198 | 2 | 131 | 10.9% | [121, 115, 131, 113, 124, 120, 99, 126, 130, 119] |

## 5. Actionable bullets

- **Smart-bot candidate (largest persistent + horizon-500 PnL):** Mark 14 — total PnL ≈ +49777 XIRECS, +5.710 per unit. Copy this Mark's flow.
- **Reverse-smart-bot (most negative horizon-500 PnL → fade-able):** Mark 38 — total PnL ≈ -41696 XIRECS, -8.339 per unit. Take the other side.
- **Best informed buy signal (HYDROGEL/VE only):** Mark 14 buying HYDROGEL_PACK (per-unit h500 PnL +8.045, qty 1989). When they buy, lean long.
- **Best informed sell signal (HYDROGEL/VE only):** Mark 14 selling HYDROGEL_PACK (per-unit h500 PnL +8.189, qty 2033). When they sell, lean short.
- **Caveat on VEV_4000/4500 PnL:** these are deep-ITM with TV≈0 (delta-1 proxies for VE spot), so any per-unit horizon PnL there just reflects VE drift, not options alpha. Read VEV_4000/4500 numbers as a confirmation of the buyer's VE view, not a separate signal.
- **Pair-graph quirk:** Mark 01↔Mark 22 dominate VEV_5300+ (the OTM/deep-OTM vouchers including the stuck-at-0.5 VEV_6000/6500). Their per-unit PnL is ±0.5 — they're each other's de-facto market-maker pair on those strikes. Mark 14↔Mark 38 dominate HYDROGEL/VE/VEV_4000 with symmetric ±~8/unit — Mark 14 is the smart side, Mark 38 is the bag-holder.
- **Mark 67 fact check:** buy qty = 1510, sell qty = 0. Confirmed buy-only.
- **Top counterparty pairs (buyer→seller, n_trades):** Mark 01->Mark 22 (1339), Mark 14->Mark 38 (728), Mark 38->Mark 14 (714), Mark 55->Mark 14 (331), Mark 14->Mark 55 (316). If a single pair dominates a product, it suggests a stable MM↔informed-bot pair.
- **Temporal concentration is weak:** no Mark concentrates >20 % of trades in any hour-bucket; treat as time-of-day noise.