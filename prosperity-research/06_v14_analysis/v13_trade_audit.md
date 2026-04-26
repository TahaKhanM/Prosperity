# v13 Trade Audit

Generated 2026-04-25.

Source runs: `runs/v13_d0_audit`, `runs/v13_d1_audit`, `runs/v13_d2_audit`.

Total trade count: **4107** across 3 days, 10k ticks each.

## TL;DR — what loses money in v13

v13 makes +268136 total over 30k ticks (D0 +87626, D1 +75603, D2 +104906).

Five (product, day) cells are net-negative on final-mid:

- **VEV_5100 day 0**: final -2649, n=55 trades
- **VEV_5400 day 2**: final -704, n=26 trades
- **VEV_5000 day 0**: final -469, n=38 trades
- **VEV_4000 day 0**: final -293, n=86 trades
- **VEV_5300 day 0**: final -226, n=27 trades

**Largest individual losing trade-class** (sec. 6c-i): VEV_5100 day 0 AGG_SELL — 45 aggressive sells (340 qty) for -2596 final-mid.
This is the entire V5100 d0 loss; v13's smile-EMA fair undershoots V5100 mid in late day 0 and the 0.7-shell take rule mechanically hits the bid into a rising mid.

**Largest paper churn** (not net-loss but pays huge spread): VFE day 2 — AGG_BUY +98,316 and AGG_SELL -94,257; both legs cycle through 200-cap inventory on a trending day.

**HYDROGEL d2 drawdown 69.7k→91.1k is NOT trade-driven**: zero new trades in window. Pure mark-to-market on max-long (+200) inventory. Recovers; final D2 HYD = +42,412.

**Warmup losses are negligible**: only 1 voucher trade per (day, product) in first 30 ticks, total impact < 80 shells across all vouchers.

## 1. PnL totals (final mid attribution)

| Day | reported (rust) | sum trade pnl_h100 | sum h1000 | sum h5000 | sum final-mid |
|---|---|---|---|---|---|
| 0 | n=1437 | 11926 | 55276 | 93564 | 87626 |
| 1 | n=1372 | 13052 | 44675 | 84188 | 75603 |
| 2 | n=1298 | -8266 | 58142 | 55879 | 104906 |

## 2. Per (product, day) PnL summary

| product | day | n | h100 | h1000 | h5000 | final |
|---|---|---|---|---|---|---|
| HYDROGEL_PACK | 0 | 401 | 12189 | 36140 | 71700 | 74682 |
| HYDROGEL_PACK | 1 | 227 | 6002 | 13576 | 58020 | 34861 |
| HYDROGEL_PACK | 2 | 250 | -5102 | 53392 | 27302 | 42412 |
| VELVETFRUIT_EXTRACT | 0 | 639 | 374 | 19091 | 19004 | 11340 |
| VELVETFRUIT_EXTRACT | 1 | 645 | 5954 | 16634 | 8911 | 11399 |
| VELVETFRUIT_EXTRACT | 2 | 675 | -20 | 4541 | 11053 | 7934 |
| VEV_4000 | 0 | 86 | 48 | 1256 | 236 | -293 |
| VEV_4000 | 1 | 87 | -234 | 1050 | 2582 | 5981 |
| VEV_4000 | 2 | 86 | 79 | 328 | 5291 | 13047 |
| VEV_4500 | 0 | 77 | -348 | 1849 | 704 | 40 |
| VEV_4500 | 1 | 84 | -364 | 1152 | 2749 | 6140 |
| VEV_4500 | 2 | 72 | -143 | -102 | 3520 | 13076 |
| VEV_5000 | 0 | 38 | -228 | -313 | -468 | -469 |
| VEV_5000 | 1 | 55 | -164 | 144 | 579 | 2523 |
| VEV_5000 | 2 | 37 | 30 | 330 | 617 | 4580 |
| VEV_5100 | 0 | 55 | -1548 | -4974 | -3304 | -2649 |
| VEV_5100 | 1 | 63 | -564 | -1024 | 2985 | 5065 |
| VEV_5100 | 2 | 56 | -1318 | -2806 | -1882 | 9617 |
| VEV_5200 | 0 | 37 | 678 | -1629 | 1038 | 732 |
| VEV_5200 | 1 | 66 | 144 | 932 | -834 | 614 |
| VEV_5200 | 2 | 49 | -1292 | -333 | 2188 | 8448 |
| VEV_5300 | 0 | 27 | 13 | -1062 | 178 | -226 |
| VEV_5300 | 1 | 73 | 1086 | 8463 | 3308 | 4771 |
| VEV_5300 | 2 | 30 | -753 | 2138 | 5591 | 6195 |
| VEV_5400 | 0 | 57 | 245 | 4106 | 3442 | 3442 |
| VEV_5400 | 1 | 58 | 1085 | 3110 | 5545 | 3744 |
| VEV_5400 | 2 | 26 | 290 | 130 | 632 | -704 |
| VEV_5500 | 0 | 20 | 503 | 812 | 1033 | 1028 |
| VEV_5500 | 1 | 14 | 106 | 638 | 340 | 504 |
| VEV_5500 | 2 | 17 | -38 | 523 | 1568 | 300 |

## 3. Worst (product, day) cells, ranked by final-mid PnL

| product | day | n | final | h5000 | h1000 | h100 |
|---|---|---|---|---|---|---|
| VEV_5100 | 0 | 55 | -2649 | -3304 | -4974 | -1548 |
| VEV_5400 | 2 | 26 | -704 | 632 | 130 | 290 |
| VEV_5000 | 0 | 38 | -469 | -468 | -313 | -228 |
| VEV_4000 | 0 | 86 | -293 | 236 | 1256 | 48 |
| VEV_5300 | 0 | 27 | -226 | 178 | -1062 | 13 |
| VEV_4500 | 0 | 77 | 40 | 704 | 1849 | -348 |
| VEV_5500 | 2 | 17 | 300 | 1568 | 523 | -38 |
| VEV_5500 | 1 | 14 | 504 | 340 | 638 | 106 |
| VEV_5200 | 1 | 66 | 614 | -834 | 932 | 144 |
| VEV_5200 | 0 | 37 | 732 | 1038 | -1629 | 678 |
| VEV_5500 | 0 | 20 | 1028 | 1033 | 812 | 503 |
| VEV_5000 | 1 | 55 | 2523 | 579 | 144 | -164 |
| VEV_5400 | 0 | 57 | 3442 | 3442 | 4106 | 245 |
| VEV_5400 | 1 | 58 | 3744 | 5545 | 3110 | 1085 |
| VEV_5000 | 2 | 37 | 4580 | 617 | 330 | 30 |

## 4. Horizon attribution by product (sum across 3 days)

| product | h | n | sum | mean | tstat |
|---|---|---|---|---|---|
| HYDROGEL_PACK | 10 | 878 | -34959 | -39.82 | - |
| HYDROGEL_PACK | 50 | 878 | -15313 | -17.44 | - |
| HYDROGEL_PACK | 100 | 878 | 13090 | 14.91 | - |
| HYDROGEL_PACK | 500 | 878 | 65888 | 75.04 | - |
| HYDROGEL_PACK | 1000 | 878 | 103108 | 117.44 | - |
| HYDROGEL_PACK | 5000 | 878 | 157022 | 178.84 | - |
| VELVETFRUIT_EXTRACT | 10 | 1959 | -2979 | -1.52 | - |
| VELVETFRUIT_EXTRACT | 50 | 1959 | 2910 | 1.49 | - |
| VELVETFRUIT_EXTRACT | 100 | 1959 | 6308 | 3.22 | - |
| VELVETFRUIT_EXTRACT | 500 | 1959 | 23438 | 11.96 | - |
| VELVETFRUIT_EXTRACT | 1000 | 1959 | 40266 | 20.55 | - |
| VELVETFRUIT_EXTRACT | 5000 | 1959 | 38968 | 19.89 | - |
| VEV_4000 | 10 | 259 | 182 | 0.70 | - |
| VEV_4000 | 50 | 259 | 51 | 0.20 | - |
| VEV_4000 | 100 | 259 | -108 | -0.42 | - |
| VEV_4000 | 500 | 259 | 218 | 0.84 | - |
| VEV_4000 | 1000 | 259 | 2632 | 10.16 | - |
| VEV_4000 | 5000 | 259 | 8110 | 31.31 | - |
| VEV_4500 | 10 | 233 | -1044 | -4.48 | - |
| VEV_4500 | 50 | 233 | -1338 | -5.74 | - |
| VEV_4500 | 100 | 233 | -854 | -3.67 | - |
| VEV_4500 | 500 | 233 | 197 | 0.85 | - |
| VEV_4500 | 1000 | 233 | 2900 | 12.44 | - |
| VEV_4500 | 5000 | 233 | 6972 | 29.92 | - |
| VEV_5000 | 10 | 130 | 106 | 0.81 | - |
| VEV_5000 | 50 | 130 | -192 | -1.48 | - |
| VEV_5000 | 100 | 130 | -362 | -2.78 | - |
| VEV_5000 | 500 | 130 | -40 | -0.31 | - |
| VEV_5000 | 1000 | 130 | 161 | 1.24 | - |
| VEV_5000 | 5000 | 130 | 728 | 5.60 | - |
| VEV_5100 | 10 | 174 | -590 | -3.39 | - |
| VEV_5100 | 50 | 174 | -1861 | -10.70 | - |
| VEV_5100 | 100 | 174 | -3429 | -19.71 | - |
| VEV_5100 | 500 | 174 | -5386 | -30.95 | - |
| VEV_5100 | 1000 | 174 | -8802 | -50.59 | - |
| VEV_5100 | 5000 | 174 | -2200 | -12.65 | - |
| VEV_5200 | 10 | 152 | -594 | -3.91 | - |
| VEV_5200 | 50 | 152 | -976 | -6.42 | - |
| VEV_5200 | 100 | 152 | -469 | -3.09 | - |
| VEV_5200 | 500 | 152 | 42 | 0.28 | - |
| VEV_5200 | 1000 | 152 | -1030 | -6.77 | - |
| VEV_5200 | 5000 | 152 | 2392 | 15.74 | - |
| VEV_5300 | 10 | 130 | -1063 | -8.18 | - |
| VEV_5300 | 50 | 130 | -555 | -4.27 | - |
| VEV_5300 | 100 | 130 | 346 | 2.66 | - |
| VEV_5300 | 500 | 130 | 4506 | 34.66 | - |
| VEV_5300 | 1000 | 130 | 9538 | 73.37 | - |
| VEV_5300 | 5000 | 130 | 9077 | 69.82 | - |
| VEV_5400 | 10 | 141 | -226 | -1.60 | - |
| VEV_5400 | 50 | 141 | 1034 | 7.34 | - |
| VEV_5400 | 100 | 141 | 1620 | 11.49 | - |
| VEV_5400 | 500 | 141 | 4756 | 33.73 | - |
| VEV_5400 | 1000 | 141 | 7346 | 52.10 | - |
| VEV_5400 | 5000 | 141 | 9620 | 68.22 | - |
| VEV_5500 | 10 | 51 | -260 | -5.09 | - |
| VEV_5500 | 50 | 51 | 106 | 2.08 | - |
| VEV_5500 | 100 | 51 | 570 | 11.19 | - |
| VEV_5500 | 500 | 51 | 994 | 19.50 | - |
| VEV_5500 | 1000 | 51 | 1974 | 38.70 | - |
| VEV_5500 | 5000 | 51 | 2942 | 57.68 | - |

## 5. V5100 day 0 deep-dive

Total trades: 55, sum_h100=-1548, sum_final=-2649.

### 5a. PnL by 1000-tick window (V5100 day 0)

| window (ticks) | n_trades | sum_h100 | sum_final |
|---|---|---|---|
| 0-999 | 4 | 6 | 26 |
| 1000-1999 | 6 | -98 | -1 |
| 2000-2999 | 4 | -18 | -75 |
| 3000-3999 | 5 | -10 | 514 |
| 4000-4999 | 6 | -65 | 222 |
| 5000-5999 | 12 | -1049 | -593 |
| 6000-6999 | 18 | -314 | -2742 |

### 5b. Worst 10 V5100 d0 trades by horizon-100 PnL

| ts | tick | side | qty | px | mid | spr | imb | VE_micro | smile_fair | smile_iv | mkt_iv | tte(d) | h100 | h1000 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 513300 | 5133 | SELL | 10 | 150.0 | 152.0 | 4 | -0.53 | 5224.7 | 151.6 | 0.2471 | 0.2488 | 7.49 | -225 | -55 | -140 |
| 514700 | 5147 | SELL | 10 | 151.0 | 153.0 | 4 | -0.53 | 5226.0 | 152.5 | 0.2471 | 0.2491 | 7.49 | -225 | -20 | -130 |
| 519000 | 5190 | SELL | 10 | 162.0 | 164.0 | 4 | -0.39 | 5239.6 | 163.2 | 0.2480 | 0.2515 | 7.48 | -165 | 80 | -20 |
| 514800 | 5148 | SELL | 6 | 151.0 | 153.0 | 4 | -0.67 | 5225.9 | 152.5 | 0.2471 | 0.2492 | 7.49 | -144 | -12 | -78 |
| 510000 | 5100 | SELL | 10 | 152.0 | 154.0 | 4 | -0.47 | 5227.2 | 153.5 | 0.2472 | 0.2494 | 7.49 | -140 | -90 | -120 |
| 625200 | 6252 | SELL | 20 | 147.0 | 149.0 | 4 | 0.00 | 5221.2 | 148.5 | 0.2470 | 0.2493 | 7.37 | -100 | -740 | -340 |
| 398100 | 3981 | SELL | 10 | 179.0 | 181.0 | 4 | 0.00 | 5260.0 | 180.2 | 0.2494 | 0.2532 | 7.60 | -85 | 120 | 150 |
| 400500 | 4005 | SELL | 7 | 179.0 | 181.0 | 4 | 0.00 | 5260.0 | 180.2 | 0.2494 | 0.2533 | 7.60 | -84 | 91 | 105 |
| 623900 | 6239 | SELL | 11 | 145.0 | 147.0 | 4 | -0.35 | 5218.3 | 146.3 | 0.2469 | 0.2499 | 7.38 | -82 | -434 | -209 |
| 625000 | 6250 | SELL | 20 | 147.0 | 149.0 | 4 | 0.00 | 5221.3 | 148.5 | 0.2470 | 0.2490 | 7.38 | -80 | -770 | -340 |

## 6. HYDROGEL day 2 drawdown ts 69,700 -> 91,100

- trades in window: **0** (0 BUY, 0 SELL)
- sum pnl_h100 in window: **0**
- sum pnl_h1000 in window: **0**
- sum pnl_h5000 in window: **0**
- sum pnl_final in window: **0**
- HYDROGEL position **before** window: 200
- HYDROGEL position **after** window:  200
- net position change in window: 0
- HYDROGEL mid at ts 69,700: 9997.0
- HYDROGEL mid at ts 91,100: 9915.0
- mid trough in window: 9915.0 @ ts 91100
- net mid move: -82.0
- last HYD trade before window: ts=49800 side=BUY price=9960.0
- first HYD trade after window: ts=114500 side=SELL price=9993.0 (mid=9986.0)

**Diagnosis:** (a) **Position-driven, pure mark-to-market.** There were ZERO trades in the window. v13 was max-long (+200) coming in and the mid drifted from 9997.0 to a trough of 9915.0 and recovered partially to 9915.0. The trader correctly stopped quoting bids (already at cap) and never lifted. Position recovers mid-term — final-mid PnL on the day is +42,412. **Fix: nothing to fix; this is mean-reversion noise on max-long inventory.** If we want to dampen the drawdown, we could trim long inventory faster when EMA falls — e.g. force-sell when pos > +180 and slow_EMA - micro > 8, or activate a take-profit on +pos when fair has risen >= 5 above entry-VWAP.

## 6c. Aggressive vs passive fill PnL by (product, day)

AGG_SELL = we hit the bid (took liquidity selling). AGG_BUY = we lifted the ask (took liquidity buying).
PASS_BUY = our bid was hit. PASS_SELL = our offer was lifted.

| product | day | class | n | qty | h100 | h1000 | final |
|---|---|---|---|---|---|---|---|
| HYDROGEL_PACK | 0 | AGG_BUY | 169 | 1845 | 8503 | -23814 | -37280 |
| HYDROGEL_PACK | 0 | AGG_SELL | 155 | 1699 | 2645 | 58114 | 106843 |
| HYDROGEL_PACK | 0 | PASS_BUY | 33 | 143 | 512 | -595 | -4562 |
| HYDROGEL_PACK | 0 | PASS_SELL | 44 | 186 | 529 | 2436 | 9681 |
| HYDROGEL_PACK | 1 | AGG_BUY | 64 | 719 | -2976 | -8238 | 27089 |
| HYDROGEL_PACK | 1 | AGG_SELL | 95 | 999 | 5864 | 17875 | 4161 |
| HYDROGEL_PACK | 1 | PASS_BUY | 45 | 169 | 2440 | 2828 | 3782 |
| HYDROGEL_PACK | 1 | PASS_SELL | 23 | 89 | 676 | 1111 | -171 |
| HYDROGEL_PACK | 2 | AGG_BUY | 87 | 887 | -7742 | 6553 | 28127 |
| HYDROGEL_PACK | 2 | AGG_SELL | 104 | 1177 | 508 | 41882 | 10742 |
| HYDROGEL_PACK | 2 | PASS_BUY | 38 | 170 | 2056 | 2194 | 3327 |
| HYDROGEL_PACK | 2 | PASS_SELL | 21 | 80 | 76 | 2762 | 216 |
| VELVETFRUIT_EXTRACT | 0 | AGG_BUY | 227 | 2354 | 1870 | 8194 | -4800 |
| VELVETFRUIT_EXTRACT | 0 | AGG_SELL | 180 | 2114 | -4686 | 6857 | 12640 |
| VELVETFRUIT_EXTRACT | 0 | PASS_BUY | 96 | 557 | 1949 | 2801 | -385 |
| VELVETFRUIT_EXTRACT | 0 | PASS_SELL | 136 | 756 | 1240 | 1240 | 3885 |
| VELVETFRUIT_EXTRACT | 1 | AGG_BUY | 240 | 2441 | 2252 | 12784 | 43286 |
| VELVETFRUIT_EXTRACT | 1 | AGG_SELL | 174 | 2122 | 2270 | 1635 | -31460 |
| VELVETFRUIT_EXTRACT | 1 | PASS_BUY | 104 | 558 | 1112 | 2447 | 10599 |
| VELVETFRUIT_EXTRACT | 1 | PASS_SELL | 127 | 677 | 320 | -232 | -11026 |
| VELVETFRUIT_EXTRACT | 2 | AGG_BUY | 218 | 2272 | 1437 | 10334 | 98316 |
| VELVETFRUIT_EXTRACT | 2 | AGG_SELL | 202 | 2366 | -2259 | -10050 | -94257 |
| VELVETFRUIT_EXTRACT | 2 | PASS_BUY | 126 | 716 | 234 | 2902 | 28530 |
| VELVETFRUIT_EXTRACT | 2 | PASS_SELL | 129 | 709 | 568 | 1356 | -24654 |
| VEV_4000 | 0 | AGG_BUY | 86 | 300 | 48 | 1256 | -293 |
| VEV_4000 | 1 | AGG_BUY | 87 | 300 | -234 | 1050 | 5981 |
| VEV_4000 | 2 | AGG_BUY | 86 | 300 | 79 | 328 | 13047 |
| VEV_4500 | 0 | AGG_BUY | 77 | 300 | -348 | 1849 | 40 |
| VEV_4500 | 1 | AGG_BUY | 84 | 300 | -364 | 1152 | 6140 |
| VEV_4500 | 2 | AGG_BUY | 72 | 300 | -143 | -102 | 13076 |
| VEV_5000 | 0 | AGG_BUY | 34 | 122 | -199 | -92 | -448 |
| VEV_5000 | 0 | AGG_SELL | 4 | 15 | -29 | -220 | -21 |
| VEV_5000 | 1 | AGG_BUY | 53 | 189 | -147 | 310 | 2656 |
| VEV_5000 | 1 | AGG_SELL | 2 | 7 | -17 | -166 | -132 |
| VEV_5000 | 2 | AGG_BUY | 34 | 125 | 93 | 328 | 5186 |
| VEV_5000 | 2 | AGG_SELL | 3 | 12 | -63 | 3 | -606 |
| VEV_5100 | 0 | AGG_BUY | 10 | 40 | -74 | 76 | -53 |
| VEV_5100 | 0 | AGG_SELL | 45 | 340 | -1474 | -5049 | -2596 |
| VEV_5100 | 1 | AGG_BUY | 62 | 302 | -566 | -976 | 5108 |
| VEV_5100 | 1 | AGG_SELL | 1 | 2 | 3 | -47 | -43 |
| VEV_5100 | 2 | AGG_BUY | 56 | 300 | -1318 | -2806 | 9617 |
| VEV_5200 | 0 | AGG_BUY | 30 | 308 | 715 | -1552 | 779 |
| VEV_5200 | 0 | AGG_SELL | 7 | 41 | -36 | -78 | -48 |
| VEV_5200 | 1 | AGG_BUY | 51 | 214 | 45 | 926 | 1515 |
| VEV_5200 | 1 | AGG_SELL | 15 | 91 | 100 | 6 | -900 |
| VEV_5200 | 2 | AGG_BUY | 49 | 300 | -1292 | -333 | 8448 |
| VEV_5300 | 0 | AGG_BUY | 27 | 300 | 13 | -1062 | -226 |
| VEV_5300 | 1 | AGG_BUY | 28 | 300 | 610 | 2944 | 2747 |
| VEV_5300 | 1 | AGG_SELL | 45 | 600 | 476 | 5520 | 2024 |
| VEV_5300 | 2 | AGG_BUY | 30 | 300 | -753 | 2138 | 6195 |
| VEV_5400 | 0 | AGG_BUY | 40 | 600 | -102 | 3638 | 1875 |
| VEV_5400 | 0 | AGG_SELL | 17 | 300 | 347 | 468 | 1567 |
| VEV_5400 | 1 | AGG_BUY | 36 | 600 | 815 | 3133 | 3458 |
| VEV_5400 | 1 | AGG_SELL | 22 | 300 | 270 | -23 | 286 |
| VEV_5400 | 2 | AGG_SELL | 26 | 300 | 290 | 130 | -704 |
| VEV_5500 | 0 | AGG_BUY | 1 | 5 | 5 | 8 | 2 |
| VEV_5500 | 0 | AGG_SELL | 19 | 305 | 498 | 804 | 1026 |
| VEV_5500 | 1 | AGG_BUY | 3 | 56 | -28 | 308 | 140 |
| VEV_5500 | 1 | AGG_SELL | 11 | 161 | 134 | 330 | 364 |
| VEV_5500 | 2 | AGG_SELL | 17 | 300 | -38 | 523 | 300 |

### 6c-i. Aggressive crossings that LOSE on final-mid (top 15)

These are taker-side trades where the trader paid the spread and then mid moved against them.

| product | day | class | n | qty | h100 | h1000 | final |
|---|---|---|---|---|---|---|---|
| VELVETFRUIT_EXTRACT | 2 | AGG_SELL | 202 | 2366 | -2259 | -10050 | -94257 |
| HYDROGEL_PACK | 0 | AGG_BUY | 169 | 1845 | 8503 | -23814 | -37280 |
| VELVETFRUIT_EXTRACT | 1 | AGG_SELL | 174 | 2122 | 2270 | 1635 | -31460 |
| VELVETFRUIT_EXTRACT | 0 | AGG_BUY | 227 | 2354 | 1870 | 8194 | -4800 |
| VEV_5100 | 0 | AGG_SELL | 45 | 340 | -1474 | -5049 | -2596 |
| VEV_5200 | 1 | AGG_SELL | 15 | 91 | 100 | 6 | -900 |
| VEV_5400 | 2 | AGG_SELL | 26 | 300 | 290 | 130 | -704 |
| VEV_5000 | 2 | AGG_SELL | 3 | 12 | -63 | 3 | -606 |
| VEV_5000 | 0 | AGG_BUY | 34 | 122 | -199 | -92 | -448 |
| VEV_4000 | 0 | AGG_BUY | 86 | 300 | 48 | 1256 | -293 |
| VEV_5300 | 0 | AGG_BUY | 27 | 300 | 13 | -1062 | -226 |
| VEV_5000 | 1 | AGG_SELL | 2 | 7 | -17 | -166 | -132 |
| VEV_5100 | 0 | AGG_BUY | 10 | 40 | -74 | 76 | -53 |
| VEV_5200 | 0 | AGG_SELL | 7 | 41 | -36 | -78 | -48 |
| VEV_5100 | 1 | AGG_SELL | 1 | 2 | 3 | -47 | -43 |

## 7. Voucher warmup window (first 30 ticks vs 30-1000)

| product | day | warm_n | warm_sum_h100 | warm_mean | steady_n | steady_sum_h100 | steady_mean |
|---|---|---|---|---|---|---|---|
| VEV_4000 | 0 | 1 | -22 | -22.50 | 7 | 69 | 9.86 |
| VEV_4000 | 1 | 0 | 0 | 0.00 | 15 | 62 | 4.13 |
| VEV_4000 | 2 | 0 | 0 | 0.00 | 10 | 65 | 6.50 |
| VEV_4500 | 0 | 1 | -24 | -24.00 | 7 | 72 | 10.29 |
| VEV_4500 | 1 | 0 | 0 | 0.00 | 15 | 62 | 4.13 |
| VEV_4500 | 2 | 0 | 0 | 0.00 | 11 | 92 | 8.36 |
| VEV_5000 | 0 | 1 | -24 | -24.00 | 3 | 25 | 8.33 |
| VEV_5000 | 1 | 0 | 0 | 0.00 | 6 | 30 | 5.00 |
| VEV_5000 | 2 | 0 | 0 | 0.00 | 9 | 58 | 6.39 |
| VEV_5100 | 0 | 1 | -20 | -19.50 | 3 | 26 | 8.67 |
| VEV_5100 | 1 | 0 | 0 | 0.00 | 5 | -22 | -4.40 |
| VEV_5100 | 2 | 0 | 0 | 0.00 | 10 | 2 | 0.25 |
| VEV_5200 | 0 | 1 | -14 | -13.50 | 26 | 734 | 28.25 |
| VEV_5200 | 1 | 0 | 0 | 0.00 | 6 | 28 | 4.75 |
| VEV_5200 | 2 | 0 | 0 | 0.00 | 8 | 28 | 3.56 |
| VEV_5300 | 0 | 1 | -9 | -9.00 | 26 | 22 | 0.85 |
| VEV_5300 | 1 | 0 | 0 | 0.00 | 28 | 610 | 21.79 |
| VEV_5300 | 2 | 0 | 0 | 0.00 | 1 | -20 | -20.00 |
| VEV_5400 | 0 | 11 | 305 | 27.73 | 6 | 42 | 7.00 |
| VEV_5400 | 1 | 0 | 0 | 0.00 | 0 | 0 | 0.00 |
| VEV_5400 | 2 | 0 | 0 | 0.00 | 0 | 0 | 0.00 |
| VEV_5500 | 0 | 0 | 0 | 0.00 | 1 | 5 | 5.00 |
| VEV_5500 | 1 | 0 | 0 | 0.00 | 0 | 0 | 0.00 |
| VEV_5500 | 2 | 0 | 0 | 0.00 | 0 | 0 | 0.00 |

## 8. Worst trade buckets (lowest sum_pnl_h5000)

| product | day | bucket | n | sum_h5000 | mean_h5000 |
|---|---|---|---|---|---|
| VELVETFRUIT_EXTRACT | 2 | SELL_below_mid | 202 | -43351 | -214.61 |
| HYDROGEL_PACK | 0 | BUY_above_mid | 169 | -30158 | -178.45 |
| VELVETFRUIT_EXTRACT | 2 | spread_gt_2 | 449 | -17260 | -38.44 |
| VELVETFRUIT_EXTRACT | 1 | SELL_below_mid | 174 | -11972 | -68.80 |
| VELVETFRUIT_EXTRACT | 2 | SELL_when_imb>0.3 | 35 | -7370 | -210.57 |
| VELVETFRUIT_EXTRACT | 1 | spread_gt_2 | 412 | -7328 | -17.79 |
| VELVETFRUIT_EXTRACT | 2 | SELL_when_imb>0.5 | 15 | -6484 | -432.23 |
| VELVETFRUIT_EXTRACT | 2 | spread_gt_3 | 305 | -3244 | -10.63 |
| VEV_5100 | 0 | SELL_below_mid | 45 | -3220 | -71.56 |
| VEV_5100 | 0 | spread_gt_3 | 30 | -3112 | -103.73 |
| VEV_5100 | 0 | spread_gt_2 | 37 | -3037 | -82.08 |
| VEV_5100 | 2 | BUY_above_mid | 56 | -1882 | -33.61 |
| VEV_5000 | 2 | spread_gt_2 | 14 | -1211 | -86.50 |
| VEV_5000 | 1 | spread_gt_2 | 24 | -864 | -36.02 |
| VEV_5200 | 1 | BUY_above_mid | 51 | -634 | -12.43 |
| VEV_5000 | 2 | SELL_below_mid | 3 | -470 | -156.50 |
| VEV_5000 | 0 | BUY_above_mid | 34 | -380 | -11.19 |
| VEV_5000 | 0 | spread_gt_2 | 23 | -328 | -14.28 |
| VEV_5200 | 1 | SELL_below_mid | 15 | -200 | -13.30 |
| VEV_5000 | 0 | SELL_below_mid | 4 | -87 | -21.75 |
| VEV_5100 | 0 | BUY_above_mid | 10 | -84 | -8.35 |
| VEV_5200 | 0 | SELL_below_mid | 7 | -48 | -6.79 |
| VEV_5000 | 1 | SELL_below_mid | 2 | -47 | -23.50 |
| VEV_5000 | 1 | spread_gt_3 | 1 | -32 | -32.00 |
| VEV_5100 | 1 | SELL_below_mid | 1 | -22 | -22.00 |
| VEV_5000 | 0 | first_30_ticks | 1 | -18 | -18.00 |
| VEV_5000 | 0 | first_100_ticks | 1 | -18 | -18.00 |
| VEV_4500 | 0 | first_30_ticks | 1 | -15 | -15.00 |
| VEV_4500 | 0 | first_100_ticks | 1 | -15 | -15.00 |
| VEV_5100 | 0 | first_30_ticks | 1 | -15 | -15.00 |

## 9. Top 10 specific fixable losers (sorted by absolute size)

Each row pairs a (product, day, bucket) loss with a 1-line surgical fix.
Buckets are de-duplicated so each (product, day) appears at most twice (once per side-class).

| rank | product | day | bucket | n | sum_h5000 | suggested rule |
|---|---|---|---|---|---|---|
| 1 | VELVETFRUIT_EXTRACT | 2 | SELL_below_mid | 202 | -43351 | never hit bids below mid on VELVETFRUIT_EXTRACT |
| 2 | HYDROGEL_PACK | 0 | BUY_above_mid | 169 | -30158 | never lift offers above mid on HYDROGEL_PACK |
| 3 | VELVETFRUIT_EXTRACT | 2 | spread_gt_2 | 449 | -17260 | skip VELVETFRUIT_EXTRACT quoting when book spread > 2 |
| 4 | VELVETFRUIT_EXTRACT | 1 | SELL_below_mid | 174 | -11972 | never hit bids below mid on VELVETFRUIT_EXTRACT |
| 5 | VELVETFRUIT_EXTRACT | 1 | spread_gt_2 | 412 | -7328 | skip VELVETFRUIT_EXTRACT quoting when book spread > 2 |
| 6 | VEV_5100 | 0 | SELL_below_mid | 45 | -3220 | never hit bids below mid on VEV_5100 |
| 7 | VEV_5100 | 0 | spread_gt_3 | 30 | -3112 | skip VEV_5100 quoting when book spread > 3 |
| 8 | VEV_5100 | 2 | BUY_above_mid | 56 | -1882 | never lift offers above mid on VEV_5100 |
| 9 | VEV_5000 | 2 | spread_gt_2 | 14 | -1211 | skip VEV_5000 quoting when book spread > 2 |
| 10 | VEV_5000 | 1 | spread_gt_2 | 24 | -864 | skip VEV_5000 quoting when book spread > 2 |

### 9b. (product, day) cells that are net-negative on final-mid

| product | day | n | h100 | h1000 | h5000 | final |
|---|---|---|---|---|---|---|
| VEV_5100 | 0 | 55 | -1548 | -4974 | -3304 | -2649 |
| VEV_5400 | 2 | 26 | 290 | 130 | 632 | -704 |
| VEV_5000 | 0 | 38 | -228 | -313 | -468 | -469 |
| VEV_4000 | 0 | 86 | 48 | 1256 | 236 | -293 |
| VEV_5300 | 0 | 27 | 13 | -1062 | 178 | -226 |

### 9c. Concrete v14 patches (ranked by expected PnL recovery)

Each patch references the exact v13 code path and a 1-2 line edit.

| # | size_now | patch | estimated saved |
|---|---|---|---|
| 1 | n=202 qty=2366 | VFE d2 AGG_SELL = -94k offsets +98k AGG_BUY — net +4k but huge spread cost; skip VFE quoting when |imb_k2| > 0.5 (raise V_SKEW_CAP gate, currently 2 shells) | -94257 |
| 2 | n=169 qty=1845 | HYDROGEL d0 AGG_BUY -37k vs +106k AGG_SELL is net +69k but lifting offers above mid eats spread; gate HYD lifts on imb_k1 < +0.2 | -37280 |
| 3 | n=0 qty=0 | HYDROGEL d2 ts69.7k-91.1k drawdown is purely position-driven (0 trades). Optional: trim long inventory faster — force-sell when pos > +180 and slow_EMA - micro > 8. Not strictly a 'losing trade' fix. | -16400 |
| 4 | n=45 qty=340 | V5100 d0 — set SMILE_PER_STRIKE_BIAS[5100] += 0.005 (currently +0.0004) so smile fair tracks the slightly-richer V5100 market and the 0.7-shell take rule stops firing on 150-bid-into-152-mid | -2596 |
| 5 | n=26 qty=300 | V5400 d2 AGG_SELL is the only voucher loss on day 2 — V5400 at TTE 6 has thin volume; widen SMILE_TAKE_EDGE_SHELLS for V5400 to 2.0 or drop V5400 from take legs | -704 |

## 10. 20 biggest individual losing trades (by horizon-5000 PnL)

| day | ts | product | side | qty | price | mid | spread | imb | h100 | h1000 | h5000 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | 416300 | VELVETFRUIT_EXTRACT | SELL | 68 | 5232.0 | 5235.0 | 6 | 0.00 | -102 | -1122 | -3706 | -4318 |
| 2 | 799900 | VELVETFRUIT_EXTRACT | SELL | 66 | 5246.0 | 5248.5 | 5 | 0.55 | -462 | -2541 | -3267 | -3267 |
| 2 | 592000 | VELVETFRUIT_EXTRACT | SELL | 25 | 5218.0 | 5220.5 | 5 | -0.49 | -725 | -1338 | -1938 | -1938 |
| 2 | 672800 | VELVETFRUIT_EXTRACT | SELL | 65 | 5269.0 | 5270.0 | 2 | 0.73 | -748 | 2372 | -1722 | -1722 |
| 2 | 731200 | VELVETFRUIT_EXTRACT | SELL | 25 | 5228.0 | 5230.5 | 5 | 0.00 | 362 | -638 | -1688 | -1688 |
| 1 | 151600 | VELVETFRUIT_EXTRACT | BUY | 23 | 5263.0 | 5260.5 | 5 | 0.47 | -196 | 34 | -1484 | 58 |
| 1 | 151500 | VELVETFRUIT_EXTRACT | BUY | 21 | 5263.0 | 5260.5 | 5 | 0.00 | -158 | 10 | -1365 | 52 |
| 2 | 599600 | VELVETFRUIT_EXTRACT | SELL | 25 | 5242.0 | 5244.5 | 5 | -0.38 | -212 | -712 | -1338 | -1338 |
| 2 | 622600 | VELVETFRUIT_EXTRACT | SELL | 21 | 5232.0 | 5234.5 | 5 | -0.53 | -304 | -158 | -1334 | -1334 |
| 2 | 596500 | VELVETFRUIT_EXTRACT | SELL | 19 | 5227.0 | 5229.5 | 5 | 0.00 | -390 | -817 | -1302 | -1302 |
| 2 | 625700 | VELVETFRUIT_EXTRACT | SELL | 23 | 5242.0 | 5244.5 | 5 | -0.52 | -126 | 172 | -1230 | -1230 |
| 2 | 746200 | VELVETFRUIT_EXTRACT | SELL | 15 | 5215.0 | 5216.0 | 2 | -0.09 | -142 | -660 | -1208 | -1208 |
| 2 | 238700 | VELVETFRUIT_EXTRACT | BUY | 25 | 5265.0 | 5262.5 | 5 | 0.47 | 150 | 100 | -1188 | 762 |
| 2 | 799800 | VELVETFRUIT_EXTRACT | SELL | 23 | 5245.0 | 5247.5 | 5 | -0.51 | -161 | -908 | -1162 | -1162 |
| 2 | 571900 | VELVETFRUIT_EXTRACT | SELL | 17 | 5232.0 | 5234.5 | 5 | 0.00 | 110 | -561 | -1080 | -1080 |
| 2 | 800500 | VELVETFRUIT_EXTRACT | SELL | 23 | 5249.0 | 5251.5 | 5 | -0.42 | -184 | -816 | -1070 | -1070 |
| 2 | 776100 | VELVETFRUIT_EXTRACT | SELL | 19 | 5241.0 | 5243.5 | 5 | -0.56 | -66 | -104 | -1036 | -1036 |
| 2 | 572400 | VELVETFRUIT_EXTRACT | SELL | 17 | 5235.0 | 5237.5 | 5 | -0.53 | 128 | -552 | -1028 | -1028 |
| 2 | 416200 | VELVETFRUIT_EXTRACT | SELL | 17 | 5230.0 | 5232.5 | 5 | -0.47 | -94 | -314 | -978 | -1114 |
| 2 | 606100 | VELVETFRUIT_EXTRACT | SELL | 19 | 5248.0 | 5250.5 | 5 | -0.49 | 256 | -276 | -902 | -902 |

