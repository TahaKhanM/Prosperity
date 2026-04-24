# R4 — HYDROGEL 3330-tick rhythm: phase-locked overlay probe

Axis M reported a dominant spectral peak for `HYDROGEL_PACK` at period ≈
3 330 ticks (power 95 494 on an n=1000 downsampled day-0 series) and
quoted a "~19.5 seashell peak-to-peak" amplitude. R4 stress-tests whether
that rhythm is a phase-locked overlay we can graft onto the A1 soft-anchor
market maker, or a spectral-leakage artefact.

All analysis is on the raw per-tick mid (pooled 30 000 rows, 3 days).
Code: `/tmp/r4_analysis.py`, `/tmp/r4_analysis_v2.py`. Cache:
`prosperity-research/03_eda/round3/notebooks/_cache/r4_hydrogel_rhythm.json`,
`r4_hydrogel_rhythm_v2.json`.

Pooled HYDROGEL: n=30 000, mean 9 990.81, std 31.93, per-day std 25.3 /
37.6 / 31.7.

## 1. Pooled `ts mod 3330` bucket table

| scheme | buckets | max \|z\| | n flagged (\|z\|>3) | bucket-mean peak-to-peak |
|---|---|---|---|---|
| width 100 (34 buckets) | 34 | 0.24 | 0 | 0.64 seashells |
| width 30 (111 buckets) | 111 | 0.72 | 0 | 2.90 seashells |

Top-5 |z| coarse buckets (width 100, SE ≈ 1.05 across 900 obs each):

| bucket | phase (ticks) | n | mean | SE | z |
|---|---|---|---|---|---|
| 5 | 500–600 | 903 | 9 990.98 | 1.05 | +0.16 |
| 25 | 2 500–2 600 | 900 | 9 990.97 | 1.07 | +0.15 |
| 17 | 1 700–1 800 | 900 | 9 990.66 | 1.07 | −0.13 |
| 6 | 600–700 | 903 | 9 990.94 | 1.05 | +0.13 |
| 33 | 3 300–3 330 | 270 | 9 990.34 | 1.99 | −0.24 |

Verdict: **no pooled bucket clears |z|=3**. The full bucket swing is
sub-seashell — orders of magnitude below the 32-seashell per-tick σ.

## 2. Per-day phase consistency

Peak location (phase within one 3 330-tick cycle) by two methods — raw
bucket argmax (width 30) and OLS H=1 sine fit:

| day | raw-bucket peak (ticks) | raw-bucket ptp | OLS t-peak (ticks) | OLS A (seashells) | OLS R² |
|---|---|---|---|---|---|
| 0 | 375 (or ~690 smoothed) | 3.27 | 1 091 | 0.158 | 0.0000 |
| 1 | 2 745 (or ~2 550) | 2.80 | 2 978 | 0.148 | 0.0000 |
| 2 | 3 075 (or ~30) | 3.14 | 3 263 | 0.125 | 0.0000 |

Phase disagreement between day 0 and day 1 is ~1 600–2 300 ticks; between
day 0 and day 2 is ~2 200 ticks. The required "±200-tick phase-stability"
gate **fails by an order of magnitude**. The bucket-mean σ is 0.62–0.73
seashells versus a per-day mid σ of 25–38, so the cycle explains ≤ 3 % of
daily variance even when the phase is handed to us day-by-day.

## 3. Harmonic fit (day 0 fit, OOS evaluate)

OLS with `mid = μ + Σₖ (aₛₖ sin(2πkt/3330) + a_cₖ cos(2πkt/3330))`.

| H | day0 R² | day0 RMSE | day0 flat RMSE | day1 OOS R² | day1 OOS RMSE | day2 OOS R² | day2 OOS RMSE |
|---|---|---|---|---|---|---|---|
| 1 | 0.00003 | 25.327 | 25.328 | −0.0009 | 37.627 | −0.0025 | 31.659 |
| 2 | 0.00005 | 25.327 | 25.328 | −0.0009 | 37.627 | −0.0025 | 31.659 |
| 3 | 0.00024 | 25.324 | 25.328 | −0.0009 | 37.627 | −0.0025 | 31.659 |

Day-0 fundamental A = 0.158 (second harmonic 0.010, third 0.109). Adding
harmonics does not shift RMSE past the third decimal. Out-of-sample R² is
**negative** on both days 1 and 2 — the overlay does measurable harm.

### Where did "19.5 seashells peak-to-peak" come from?

The seasonality report computed amplitude as `2·√(power/N)` =
2·√(95 494/1 000) ≈ 19.5. That is **dimensionally wrong** for a real DFT
power. The correct conversion for `power = |Xₖ|²` on a real length-N
signal is `A = 2·|Xₖ|/N = 2·√(power)/N = 0.618 seashells`, peak-to-peak
1.24 — which matches both our OLS amplitude (0.158 at P=3 330 with
leakage; up to ~1.0 with detrending and at the best free period). The
"19.5" figure overstated the true amplitude by ~30×.

## 4. Overlay PnL estimate

Trader modification: `fair = clamp(EMA_200, 9980, 10010) + A·sin(2π(t−φ)/3330)`.

Using the most generous amplitude found (A = 1.0 seashells on the
detrended day-0 best period, not 3 330 proper):

- Average absolute sine deviation over one cycle: `(2/π)·A ≈ 0.64 seashells`.
- A1 generates ~1 000 take-crossings / day at edge ≈ 1 seashell.
- If the overlay adds 0.64 × 80 % = 0.51 seashells of accurate fair-value
  adjustment to each take, and fills average ~5 units per take, the
  marginal edge is ≈ **2 550 seashells / day** in the optimistic ceiling.

Using the actual fitted amplitude at P = 3 330 (A = 0.158):

- Average absolute lift: `(2/π)·0.158·0.8 = 0.081 seashells`.
- Marginal edge: 0.081 × 1 000 × 5 ≈ **400 seashells / day**, i.e. +5 % on
  a 4–8 k/day A1 baseline.

Both numbers live inside the within-day noise band on A1 and, more
damningly, the fitted model has **negative OOS R²** on days 1 and 2. In
practice the overlay will mis-price the fair by up to A on the wrong side
whenever the phase drifts, producing takes at a *worse* effective edge.

## 5. Out-of-sample residual variance

Fit `mid = μ₀ + aₛ sin(2πt/3330) + a_c cos(2πt/3330)` on day 0; apply to
all three days:

| day | per-day-mean std | overlay std | Δ (overlay − mean) |
|---|---|---|---|
| 0 | 25.327 | 25.327 | 0.000 |
| 1 | 37.611 | 37.613 | **+0.002 (worse)** |
| 2 | 31.622 | 31.624 | **+0.002 (worse)** |

The overlay neither helps nor hurts day 0 materially (R² ≈ 3×10⁻⁵) and
makes residual variance *slightly larger* on both OOS days. Residual σ
reduction vs per-day-mean baseline is −0.0 % on every day.

## 6. Free-period scan — is there a better period than 3 330?

OLS period scan 200 → 10 000 ticks, day 0 only:

| rank | period | R² | A |
|---|---|---|---|
| 1 | 7 550 | 0.0008 | 1.02 |
| 2 | 9 650 | 0.0007 | 0.98 |
| 3 | 5 650 | 0.0005 | 0.84 |
| 4 | 7 650 | 0.0004 | 0.72 |
| 5 | 7 000 | 0.0003 | 0.66 |

Best-free-period on each day: day 0 = 7 550, day 1 = 8 900, day 2 = 9 100
— incoherent and all long-period ≈ half-day to whole-day, which is what a
drift / random walk produces. Best R² across all periods on all days is
0.001. **No period has explanatory power.**

## VE 5000-tick companion — drift vs genuine oscillation?

Four models per day; AIC (lower = better):

| day | A: μ only | B: linear | C: sin(5000) | D: linear + sin(5000) | ΔAIC (B−A) | ΔAIC (D−B) |
|---|---|---|---|---|---|---|
| 0 | 52 316.5 | 51 475.5 | 52 319.4 | 51 478.2 | **−840.9** | **+2.6** |
| 1 | 53 641.1 | 53 415.5 | 53 645.1 | 53 419.5 | **−225.6** | **+4.0** |
| 2 | 56 648.0 | 56 502.8 | 56 651.9 | 56 506.7 | **−145.2** | **+3.9** |

Linear trend dominates: B beats A by 146–841 AIC units every day. Adding
a 5 000-tick sinusoid on top of the trend **worsens** AIC by 2.6–4.0
every day — it costs 2 parameters and removes essentially none of the
residual variance. Standalone sinusoid (C) fails the same way: ΔAIC(C−A)
≈ +3 every day.

**Verdict for VE: no genuine 5000-tick oscillation.** The axis-M spectral
peak at 5 000 ticks is a pure drift artefact (half-day harmonic of a
linear up-trend in VE), exactly as axis M itself suggested.

## Summary verdict

| question | answer |
|---|---|
| Does HYDROGEL have a 3 330-tick rhythm with |z|>3 buckets? | No (max |z|=0.72, n flagged=0). |
| Is the phase stable within ±200 ticks across days? | No — ±1 600 to ±2 300 ticks. |
| Does a harmonic fit explain day-0 mid? | R² ≈ 3×10⁻⁵. |
| Does it generalise OOS? | No — negative R² on days 1 & 2. |
| Expected PnL lift on A1? | 0–400 seashells/day in practice; inside noise. |
| Does VE have a genuine 5 000-tick cycle? | No — pure linear trend. |

### Decision

**PARK.** The 3 330-tick "rhythm" is spectral leakage from HYDROGEL's
slow mean-reverting walk; the true amplitude is ~0.6 seashells and the
phase is incoherent across days, so any overlay adds no out-of-sample
lift and can increase mis-pricing. The published "19.5 seashells
peak-to-peak" figure in `seasonality_report.md` should be corrected
(~1.2 peak-to-peak is the right value). A1 (EMA-200 anchor) already
captures the slow drift; no phase overlay is warranted.
