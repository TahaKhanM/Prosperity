"""Lightweight stationarity, autocorrelation, and half-life tests.

Stdlib-only: used to sift every candidate spread / residual series through
a short battery of "is there planted structure here?" tests:

- rho1: lag-1 autocorrelation of returns (negative => mean-reversion candidate)
- hurst: rescaled-range approx Hurst exponent
- ou_half_life: AR(1) half-life (for mean reversion sizing)
- variance_ratio: VR(k) / k ≈ 1 under random walk; &lt; 1 => mean-reverting
- spectral_peak: dominant frequency from a naive DFT (detects seasonality)

All functions take a 1-D list of floats and return simple scalars. Safe to
import from trader code as long as the trader only calls them during
offline research (they are O(n^2) in the worst case).

Not a replacement for a proper ADF test but sufficient to triage signals on
synthetic Prosperity data where alphas are injected at meaningful magnitudes.
"""

from __future__ import annotations

import math
from typing import List, Sequence, Tuple


def _mean(x: Sequence[float]) -> float:
    return sum(x) / len(x) if x else 0.0


def _var(x: Sequence[float]) -> float:
    if len(x) < 2:
        return 0.0
    m = _mean(x)
    return sum((v - m) ** 2 for v in x) / (len(x) - 1)


def returns(series: Sequence[float]) -> List[float]:
    return [series[i] - series[i - 1] for i in range(1, len(series))]


def rho1(series: Sequence[float]) -> float:
    """Lag-1 autocorrelation."""
    if len(series) < 3:
        return float("nan")
    m = _mean(series)
    num = sum((series[i] - m) * (series[i - 1] - m) for i in range(1, len(series)))
    den = sum((v - m) ** 2 for v in series)
    return num / den if den > 0 else float("nan")


def ou_half_life(series: Sequence[float]) -> float:
    """Half-life under AR(1): half_life = -log(2) / log(phi)."""
    diffs = returns(series)
    if len(diffs) < 3:
        return float("nan")
    # regress diffs on lagged level
    lag = [series[i] for i in range(len(diffs))]
    mean_lag = _mean(lag)
    mean_d = _mean(diffs)
    num = sum((lag[i] - mean_lag) * (diffs[i] - mean_d) for i in range(len(diffs)))
    den = sum((lag[i] - mean_lag) ** 2 for i in range(len(diffs)))
    if den <= 0:
        return float("nan")
    lam = num / den  # speed of reversion
    if lam >= 0 or lam <= -1:
        return float("nan")
    return -math.log(2.0) / math.log(1.0 + lam)


def variance_ratio(series: Sequence[float], k: int) -> float:
    r = returns(series)
    if len(r) < k * 2:
        return float("nan")
    v1 = _var(r)
    kblocks = [sum(r[i : i + k]) for i in range(0, len(r) - k + 1)]
    vk = _var(kblocks)
    return (vk / k) / v1 if v1 > 0 else float("nan")


def hurst(series: Sequence[float], min_lag: int = 2, max_lag: int = 50) -> float:
    """Naive R/S Hurst exponent. >0.5 trending, <0.5 mean-reverting."""
    if len(series) < max_lag * 2:
        return float("nan")
    lags = list(range(min_lag, max_lag))
    tau: List[float] = []
    for lag in lags:
        diffs = [series[i + lag] - series[i] for i in range(len(series) - lag)]
        sd = math.sqrt(_var(diffs)) if len(diffs) > 1 else 0.0
        if sd <= 0:
            return float("nan")
        tau.append(sd)
    log_lags = [math.log(l) for l in lags]
    log_tau = [math.log(t) for t in tau]
    n = len(log_lags)
    mean_x = _mean(log_lags)
    mean_y = _mean(log_tau)
    num = sum((log_lags[i] - mean_x) * (log_tau[i] - mean_y) for i in range(n))
    den = sum((log_lags[i] - mean_x) ** 2 for i in range(n))
    return num / den if den > 0 else float("nan")


def spectral_peak(series: Sequence[float]) -> Tuple[int, float]:
    """Return (period_in_samples, power) of the dominant non-DC frequency."""
    n = len(series)
    if n < 8:
        return (0, 0.0)
    m = _mean(series)
    x = [v - m for v in series]
    best_k, best_p = 0, 0.0
    for k in range(1, n // 2):
        theta = 2.0 * math.pi * k / n
        re = sum(x[t] * math.cos(theta * t) for t in range(n))
        im = -sum(x[t] * math.sin(theta * t) for t in range(n))
        power = (re * re + im * im) / n
        if power > best_p:
            best_p = power
            best_k = k
    period = n // best_k if best_k else 0
    return (period, best_p)


def summary(series: Sequence[float]) -> dict:
    return {
        "n": len(series),
        "mean": _mean(series),
        "stdev": math.sqrt(_var(series)) if len(series) > 1 else 0.0,
        "rho1": rho1(series),
        "ou_half_life": ou_half_life(series),
        "variance_ratio_k2": variance_ratio(series, 2),
        "variance_ratio_k5": variance_ratio(series, 5),
        "hurst": hurst(series),
        "spectral_period": spectral_peak(series)[0],
    }


if __name__ == "__main__":
    # quick smoke test on a mean-reverting AR(1): rho=-0.3 should show rho1 negative
    import random

    random.seed(0)
    x = [0.0]
    for _ in range(500):
        x.append(0.0 * x[-1] + -0.3 * (x[-1] - 0.0) + random.gauss(0, 1))
    s = summary(x)
    for k, v in s.items():
        print(f"{k}: {v}")
