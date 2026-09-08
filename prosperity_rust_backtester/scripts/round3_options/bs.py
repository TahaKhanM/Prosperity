"""Black-Scholes call pricer and implied-vol solver.

No SciPy dependency: uses a fast rational approximation for the standard
normal CDF and a Newton-Raphson IV solver with a bisection fallback.

Everything is vectorized-friendly (pure Python floats here for portability;
swap in numpy variants where helpful).

Conventions
-----------
- `t` is *time to expiry in years*. Prosperity has discrete rounds; callers
  should convert (e.g. rounds / 365 for a nominal year, or rounds / 252 for
  "trading days"). This module is agnostic — whatever scale the caller uses,
  IV will be in that scale too.
- `r = 0` default. Prosperity has no stated risk-free rate.
- No dividends.
"""

from __future__ import annotations

import math

SQRT2 = math.sqrt(2.0)
SQRT_2PI = math.sqrt(2.0 * math.pi)


def _ncdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / SQRT2))


def _npdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / SQRT_2PI


def bs_call_price(s: float, k: float, t: float, sigma: float, r: float = 0.0) -> float:
    """European call price under Black-Scholes.

    At expiry returns intrinsic; zero volatility uses the discounted strike.
    """
    if t <= 0.0 or sigma <= 0.0:
        return max(s - k * math.exp(-r * max(t, 0.0)), 0.0)
    vsqrt_t = sigma * math.sqrt(t)
    d1 = (math.log(s / k) + (r + 0.5 * sigma * sigma) * t) / vsqrt_t
    d2 = d1 - vsqrt_t
    return s * _ncdf(d1) - k * math.exp(-r * t) * _ncdf(d2)


def bs_call_delta(s: float, k: float, t: float, sigma: float, r: float = 0.0) -> float:
    if t <= 0.0 or sigma <= 0.0:
        return 1.0 if s > k else (0.5 if s == k else 0.0)
    vsqrt_t = sigma * math.sqrt(t)
    d1 = (math.log(s / k) + (r + 0.5 * sigma * sigma) * t) / vsqrt_t
    return _ncdf(d1)


def bs_call_vega(s: float, k: float, t: float, sigma: float, r: float = 0.0) -> float:
    """Vega per unit vol (not per 1%)."""
    if t <= 0.0 or sigma <= 0.0:
        return 0.0
    vsqrt_t = sigma * math.sqrt(t)
    d1 = (math.log(s / k) + (r + 0.5 * sigma * sigma) * t) / vsqrt_t
    return s * _npdf(d1) * math.sqrt(t)


def bs_call_gamma(s: float, k: float, t: float, sigma: float, r: float = 0.0) -> float:
    if t <= 0.0 or sigma <= 0.0:
        return 0.0
    vsqrt_t = sigma * math.sqrt(t)
    d1 = (math.log(s / k) + (r + 0.5 * sigma * sigma) * t) / vsqrt_t
    return _npdf(d1) / (s * vsqrt_t)


def bs_call_theta(s: float, k: float, t: float, sigma: float, r: float = 0.0) -> float:
    if t <= 0.0 or sigma <= 0.0:
        return 0.0
    vsqrt_t = sigma * math.sqrt(t)
    d1 = (math.log(s / k) + (r + 0.5 * sigma * sigma) * t) / vsqrt_t
    d2 = d1 - vsqrt_t
    term1 = -(s * _npdf(d1) * sigma) / (2.0 * math.sqrt(t))
    term2 = -r * k * math.exp(-r * t) * _ncdf(d2)
    return term1 + term2


def implied_vol_call(
    price: float,
    s: float,
    k: float,
    t: float,
    r: float = 0.0,
    tol: float = 1e-7,
    max_iter: int = 60,
    sigma_lo: float = 1e-6,
    sigma_hi: float = 5.0,
) -> float:
    """Implied vol for a European call.

    Returns `nan` when the target price is outside arbitrage bounds
    (i.e., below intrinsic or above S). Newton first, then a bisection
    fallback for pathological inputs.
    """
    intrinsic = max(s - k * math.exp(-r * max(t, 0.0)), 0.0)
    if price < intrinsic - 1e-9 or price > s + 1e-9 or t <= 0.0:
        return float("nan")
    if price <= intrinsic + 1e-9:
        return 0.0

    # Newton with a decent seed from Corrado-Miller-like heuristic.
    sigma = 0.5 if price < 0.3 * s else 0.3
    for _ in range(max_iter):
        p = bs_call_price(s, k, t, sigma, r)
        v = bs_call_vega(s, k, t, sigma, r)
        diff = p - price
        if abs(diff) < tol:
            return sigma
        if v < 1e-10:
            break
        sigma -= diff / v
        if not (sigma_lo < sigma < sigma_hi):
            break

    # Bisection fallback.
    lo, hi = sigma_lo, sigma_hi
    p_lo = bs_call_price(s, k, t, lo, r)
    p_hi = bs_call_price(s, k, t, hi, r)
    if (p_lo - price) * (p_hi - price) > 0:
        return float("nan")
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        p = bs_call_price(s, k, t, mid, r)
        if abs(p - price) < tol:
            return mid
        if (p - price) * (p_lo - price) < 0:
            hi = mid
            p_hi = p
        else:
            lo = mid
            p_lo = p
    return 0.5 * (lo + hi)


if __name__ == "__main__":
    # Smoke test matching a textbook case: S=100 K=100 T=1 sigma=0.2 r=0 -> ~7.9656
    p = bs_call_price(100.0, 100.0, 1.0, 0.2, 0.0)
    iv = implied_vol_call(p, 100.0, 100.0, 1.0, 0.0)
    print(f"call={p:.6f} iv={iv:.6f}")
