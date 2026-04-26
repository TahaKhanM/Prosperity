"""Black-Scholes call/put pricer and implied-vol solver (Round 4).

Identical to `scripts/round3_options/bs.py` (the math has not changed) plus
the put pricer needed by the Round 4 manual exotics.

Conventions
-----------
- `t` is *time to expiry in years*. Convert from Prosperity-day TTE via
  `t = days / 365` (or 252 if you prefer trading-day basis — be consistent).
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


def _d1d2(s: float, k: float, t: float, sigma: float, r: float):
    vsqrt_t = sigma * math.sqrt(t)
    d1 = (math.log(s / k) + (r + 0.5 * sigma * sigma) * t) / vsqrt_t
    d2 = d1 - vsqrt_t
    return d1, d2, vsqrt_t


def bs_call_price(s: float, k: float, t: float, sigma: float, r: float = 0.0) -> float:
    if t <= 0.0 or sigma <= 0.0:
        return max(s - k, 0.0)
    d1, d2, _ = _d1d2(s, k, t, sigma, r)
    return s * _ncdf(d1) - k * math.exp(-r * t) * _ncdf(d2)


def bs_put_price(s: float, k: float, t: float, sigma: float, r: float = 0.0) -> float:
    if t <= 0.0 or sigma <= 0.0:
        return max(k - s, 0.0)
    d1, d2, _ = _d1d2(s, k, t, sigma, r)
    return k * math.exp(-r * t) * _ncdf(-d2) - s * _ncdf(-d1)


def bs_call_delta(s: float, k: float, t: float, sigma: float, r: float = 0.0) -> float:
    if t <= 0.0 or sigma <= 0.0:
        return 1.0 if s > k else (0.5 if s == k else 0.0)
    d1, _, _ = _d1d2(s, k, t, sigma, r)
    return _ncdf(d1)


def bs_put_delta(s: float, k: float, t: float, sigma: float, r: float = 0.0) -> float:
    return bs_call_delta(s, k, t, sigma, r) - 1.0


def bs_call_vega(s: float, k: float, t: float, sigma: float, r: float = 0.0) -> float:
    if t <= 0.0 or sigma <= 0.0:
        return 0.0
    d1, _, _ = _d1d2(s, k, t, sigma, r)
    return s * _npdf(d1) * math.sqrt(t)


def bs_call_gamma(s: float, k: float, t: float, sigma: float, r: float = 0.0) -> float:
    if t <= 0.0 or sigma <= 0.0:
        return 0.0
    d1, _, vsqrt_t = _d1d2(s, k, t, sigma, r)
    return _npdf(d1) / (s * vsqrt_t)


def bs_call_theta(s: float, k: float, t: float, sigma: float, r: float = 0.0) -> float:
    if t <= 0.0 or sigma <= 0.0:
        return 0.0
    d1, d2, _ = _d1d2(s, k, t, sigma, r)
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
    """Implied vol for a European call. Returns nan when out of arb bounds."""
    intrinsic = max(s - k, 0.0)
    if price < intrinsic - 1e-9 or price > s + 1e-9 or t <= 0.0:
        return float("nan")
    if price <= intrinsic + 1e-9:
        return 0.0

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
            p_lo = p
        else:
            lo = mid
            p_lo = p
    return 0.5 * (lo + hi)


def implied_vol_put(
    price: float,
    s: float,
    k: float,
    t: float,
    r: float = 0.0,
    tol: float = 1e-7,
    max_iter: int = 60,
) -> float:
    """Implied vol for a European put — solved via put-call parity then call IV.

    Under put-call parity: C - P = S - K * exp(-r*t).
    """
    if t <= 0.0:
        return float("nan")
    call_equiv = price + s - k * math.exp(-r * t)
    return implied_vol_call(call_equiv, s, k, t, r, tol, max_iter)


if __name__ == "__main__":
    p_c = bs_call_price(100.0, 100.0, 1.0, 0.2, 0.0)
    p_p = bs_put_price(100.0, 100.0, 1.0, 0.2, 0.0)
    iv_c = implied_vol_call(p_c, 100.0, 100.0, 1.0, 0.0)
    iv_p = implied_vol_put(p_p, 100.0, 100.0, 1.0, 0.0)
    print(f"call={p_c:.6f} iv_c={iv_c:.6f}  put={p_p:.6f} iv_p={iv_p:.6f}")
