# Round 3 seasonality report

Source: axes_results.json, axes I, M, N.

## Axis I — Intra-day seasonality buckets (500-tick buckets)

For every product we pooled `mid[t+1] − mid[t]` across the 3 days and
grouped by `bucket = ts // 50_000` (20 buckets per day). For each bucket we
computed mean return, SE, and z vs the per-product daily mean.

**Result.** Zero buckets exceed |z| > 3 on any product:

| product | bucket_size | mean return (pooled) | σ | n_flagged |
|---|---|---|---|---|
| HYDROGEL_PACK | 500 ticks | 0.00047 | 2.17 | 0 |
| VELVETFRUIT_EXTRACT | 500 ticks | 0.00142 | 1.13 | 0 |
| VEV_4000 | 500 ticks | 0.00140 | 1.42 | 0 |
| VEV_4500 | 500 ticks | 0.00143 | 1.25 | 0 |
| VEV_5000 | 500 ticks | 0.00123 | 0.98 | 0 |
| VEV_5100 | 500 ticks | 0.00092 | 0.85 | 0 |
| VEV_5200 | 500 ticks | 0.00053 | 0.69 | 0 |
| VEV_5300 | 500 ticks | 0.00013 | 0.50 | 0 |
| VEV_5400 | 500 ticks | −0.00010 | 0.27 | 0 |
| VEV_5500 | 500 ticks | −0.00005 | 0.18 | 0 |

No window of the trading day shows a planted directional push.

Note the monotone pattern in mean-return-per-tick: VE 0.00142 → VEV_4000
0.00140 → ... → VEV_5500 −0.00005. That's delta × (VE drift), which is just
the cross-sectional delta exposure, not a time-of-day effect.

## Axis M — Frequency-domain scan (day 0, subsampled ×10)

Spectral peak search on each product's mid series (n=1000 samples, which
corresponds to 10 000 raw ticks = one whole day at 10× downsample):

| product | dominant period (ticks) | power |
|---|---|---|
| HYDROGEL_PACK | 3 330 | 95 494 |
| VELVETFRUIT_EXTRACT | 5 000 | 39 300 |
| VEV_4000 | 5 000 | 39 550 |
| VEV_4500 | 5 000 | 39 526 |
| VEV_5000 | 5 000 | 32 051 |
| VEV_5100 | 5 000 | 24 867 |
| VEV_5200 | 5 000 | 12 454 |
| VEV_5300 | 5 000 | 4 678 |
| VEV_5400 | 5 000 | 678 |
| VEV_5500 | 5 000 | 287 |

The 5 000-tick peak on VE and every voucher is **exactly half the day**. This
is characteristic of a slow up-trend (DFT puts most energy at the longest
half-cycle for a drifting series). It is **not** an injected periodic alpha;
it is the intra-day VE drift showing up in the spectrum.

HYDROGEL's peak at 3 330 ticks (~ 1/3 day) is a real oscillation. Amplitude:
√(power/N) × 2 ≈ √(95 494 / 1000) × 2 ≈ 19.5 seashells peak-to-peak. This is
consistent with the observed HYDROGEL range (9891–10079, ~190 peak-to-peak)
and σ=32, but with a specific rhythm.

**Conclusion on M.** No short-period (≤ 100 ticks) planted seasonality.
The spectrum reflects the drift structure you already see in mid charts.

## Axis N — End-of-day drift

Last-50-tick drift vs the rest-of-day mean:

| product | day 0 | day 1 | day 2 |
|---|---|---|---|
| VELVETFRUIT_EXTRACT | −2.5 | **+19.6** | **+39.3** |
| VEV_4000 | −2.5 | +19.6 | +39.2 |
| VEV_4500 | −2.5 | +19.6 | +39.2 |
| VEV_5000 | −2.7 | +17.5 | +37.3 |
| VEV_5100 | −3.8 | +14.5 | +33.4 |
| VEV_5200 | −2.2 | +9.5 | +24.4 |
| VEV_5300 | −2.4 | +6.4 | +13.2 |
| VEV_5400 | −2.1 | +1.6 | +6.3 |
| VEV_5500 | −0.5 | +0.3 | +1.7 |

Day 0 ends down, days 1 and 2 end up. Magnitude scales with delta — so the
final-tick move is dominated by VE's drift, not a per-product push. At
last-5 ticks the VE drift is even larger on day 2 (+41).

Pattern: VE drifts up over the whole day-2 session, not just at the end.
Log the per-500-tick means (pulled from axes_results) to confirm this is a
continuous drift, not a terminal squeeze:

- day 2 VE mean across session: ~5255.
- day 2 VE last 50 mean: ~5294.
- So the final move is consistent with a broader up-trend.

**Conclusion on N.** There is **no terminal-tick squeeze**. The end-of-day
drift is just the session trend continuing. We can still profit from the
trend (see axis B wall-mid alpha, axis C imbalance alpha) but there is no
standalone "last-5-ticks-buy" trade.

## Summary

| question | answer |
|---|---|
| Do any 500-tick buckets have |z| > 3? | No. |
| Do any products show a short-period (< 100 tick) spectral peak? | No. |
| Does HYDROGEL show a dominant rhythm? | Yes — ~3330-tick oscillation. |
| Do any products squeeze in the last 5 / 10 / 50 ticks? | No — EOD drift is session trend. |

No dedicated seasonality alpha. The signals we do find live in wall-mid,
imbalance, and IV-residual, not in the clock.
