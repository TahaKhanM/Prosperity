"""Black-Scholes call/put pricer and implied-vol solver (Round 4).

Post-competition numerical corrections are described in docs/NUMERICAL_REVIEW.md.
The standalone round modules retain their original import paths.

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
    return 0.5 * math.erfc(-x / SQRT2)


def _npdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / SQRT_2PI


def _validate(s: float, k: float, t: float, sigma: float, r: float) -> None:
    if not all(math.isfinite(x) for x in (s, k, t, sigma, r)):
        raise ValueError("pricing inputs must be finite")
    if s <= 0 or k <= 0 or t < 0 or sigma < 0:
        raise ValueError("spot/strike must be positive; time/volatility nonnegative")


def _d1d2(s: float, k: float, t: float, sigma: float, r: float):
    vsqrt_t = sigma * math.sqrt(t)
    d1 = (math.log(s / k) + (r + 0.5 * sigma * sigma) * t) / vsqrt_t
    d2 = d1 - vsqrt_t
    return d1, d2, vsqrt_t


def bs_call_price(s: float, k: float, t: float, sigma: float, r: float = 0.0) -> float:
    _validate(s, k, t, sigma, r)
    if t == 0.0 or sigma == 0.0:
        return max(s - k * math.exp(-r * t), 0.0)
    d1, d2, _ = _d1d2(s, k, t, sigma, r)
    return s * _ncdf(d1) - k * math.exp(-r * t) * _ncdf(d2)


def bs_put_price(s: float, k: float, t: float, sigma: float, r: float = 0.0) -> float:
    _validate(s, k, t, sigma, r)
    if t == 0.0 or sigma == 0.0:
        return max(k * math.exp(-r * t) - s, 0.0)
    d1, d2, _ = _d1d2(s, k, t, sigma, r)
    return k * math.exp(-r * t) * _ncdf(-d2) - s * _ncdf(-d1)


def bs_call_delta(s: float, k: float, t: float, sigma: float, r: float = 0.0) -> float:
    _validate(s, k, t, sigma, r)
    if t == 0.0 or sigma == 0.0:
        strike_pv = k * math.exp(-r * t)
        return 1.0 if s > strike_pv else (0.5 if s == strike_pv else 0.0)
    d1, _, _ = _d1d2(s, k, t, sigma, r)
    return _ncdf(d1)


def bs_put_delta(s: float, k: float, t: float, sigma: float, r: float = 0.0) -> float:
    return bs_call_delta(s, k, t, sigma, r) - 1.0


def bs_call_vega(s: float, k: float, t: float, sigma: float, r: float = 0.0) -> float:
    _validate(s, k, t, sigma, r)
    if t == 0.0 or sigma == 0.0:
        return 0.0
    d1, _, _ = _d1d2(s, k, t, sigma, r)
    return s * _npdf(d1) * math.sqrt(t)


def bs_call_gamma(s: float, k: float, t: float, sigma: float, r: float = 0.0) -> float:
    _validate(s, k, t, sigma, r)
    if t == 0.0 or sigma == 0.0:
        return 0.0
    d1, _, vsqrt_t = _d1d2(s, k, t, sigma, r)
    return _npdf(d1) / (s * vsqrt_t)


def bs_call_theta(s: float, k: float, t: float, sigma: float, r: float = 0.0) -> float:
    _validate(s, k, t, sigma, r)
    if t == 0.0 or sigma == 0.0:
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
    """Call IV on [sigma_lo, sigma_hi]; NaN if unidentifiable/out of range.

    Newton accelerates ordinary quotes; monotonic bisection guarantees the
    fallback keeps a valid price bracket. A price tolerance is not a guarantee
    of precise IV in low-vega tails. max_iter=0 forces the fallback.
    """
    _validate(s, k, t, 0.0, r)
    if not (math.isfinite(tol) and tol > 0 and max_iter >= 0):
        raise ValueError("tol must be positive and max_iter nonnegative")
    if not (0 <= sigma_lo < sigma_hi and math.isfinite(sigma_hi)):
        raise ValueError("require finite 0 <= sigma_lo < sigma_hi")
    lower = max(s - k * math.exp(-r * t), 0.0)
    if not math.isfinite(price) or price < lower or price >= s or t == 0:
        return float("nan")
    if price == lower:
        return 0.0
    lo, hi = sigma_lo, sigma_hi
    if not (bs_call_price(s, k, t, lo, r) <= price <= bs_call_price(s, k, t, hi, r)):
        return float("nan")

    sigma = min(max(0.5, lo), hi)
    for _ in range(max_iter):
        diff = bs_call_price(s, k, t, sigma, r) - price
        if abs(diff) < tol:
            return sigma
        if diff < 0:
            lo = sigma
        else:
            hi = sigma
        vega = bs_call_vega(s, k, t, sigma, r)
        if vega < 1e-10:
            break
        candidate = sigma - diff / vega
        if not (lo < candidate < hi):
            break
        sigma = candidate

    for _ in range(200):
        mid = 0.5 * (lo + hi)
        diff = bs_call_price(s, k, t, mid, r) - price
        if abs(diff) < tol:
            return mid
        if diff < 0:
            lo = mid
        else:
            hi = mid
    return float("nan")  # no convergence: never manufacture a usable IV


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
    _validate(s, k, t, 0.0, r)
    if not math.isfinite(price) or price < 0 or t == 0:
        return float("nan")
    call_equiv = price + s - k * math.exp(-r * t)
    return implied_vol_call(call_equiv, s, k, t, r, tol, max_iter)


if __name__ == "__main__":
    p_c = bs_call_price(100.0, 100.0, 1.0, 0.2, 0.0)
    p_p = bs_put_price(100.0, 100.0, 1.0, 0.2, 0.0)
    iv_c = implied_vol_call(p_c, 100.0, 100.0, 1.0, 0.0)
    iv_p = implied_vol_put(p_p, 100.0, 100.0, 1.0, 0.0)
    print(f"call={p_c:.6f} iv_c={iv_c:.6f}  put={p_p:.6f} iv_p={iv_p:.6f}")
