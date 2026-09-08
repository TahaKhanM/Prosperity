"""Closed-form fair-value pricers for the Round 4 manual exotics.

Three exotics are listed in `New Context/round_4_trading_round.md`:

1. **Chooser** — K=50, expiry T=21 days, decision date T_c=14 days.
   Auto-converts to whichever of call/put is in the money at the decision
   point. Behaves vanilla afterward. Under the simple-chooser identity:
       Chooser(S, K, T, T_c) = C(S, K, T) + P(S, K * exp(-r*(T - T_c)), T_c)
   With r=0 (Prosperity convention), the put strike collapses to K and:
       Chooser = Call(S, K, T) + Put(S, K, T_c)

2. **Binary (digital) put** — K=40, expiry T=21 days, payoff `Q` if
   `S_T < K` else 0. Closed-form under BS:
       DigitalPut(S, K, T, sigma, Q) = Q * N(-d2)
   The Round 4 brief says `Q = 10`.

3. **Knockout (down-and-out) put** — K=45, barrier B=35, expiry T=21 days.
   Pays `max(K - S_T, 0)` if `S_t > B` for all t in [0, T]; 0 otherwise.
   Reiner-Rubinstein closed-form (rebate=0, no dividends):
       DOPut = Put(S, K, T) - DIPut(S, K, B, T)
   where DIPut is the standard down-and-in put under BS.

Run as a script with `--spot --sigma --year-basis` to print fair values for
the three exotics; or import the functions individually. Pure stdlib.

Usage
-----
    python3 exotic_pricers.py --spot 50 --sigma 0.30
    # → prints chooser / digital-put / knockout-put fair values

Key references
--------------
- Hull, "Options, Futures, and Other Derivatives" 9th ed., Ch. 26.
- Reiner & Rubinstein 1991, "Breaking Down the Barriers", Risk Magazine.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

import bs


@dataclass
class ExoticContract:
    name: str
    fair_value: float
    delta: float
    notes: str = ""


# ---------- Chooser ----------

def chooser_value(
    s: float,
    k: float,
    t_total: float,        # years to expiry (e.g. 21/365)
    t_choice: float,       # years to decision date (e.g. 14/365)
    sigma: float,
    r: float = 0.0,
) -> float:
    """Simple-chooser fair value (Hull 26.2).

    Chooser = Call(S, K, T) + Put(S, K * exp(-r * (T - T_c)), T_c).
    Under r=0 the put strike collapses to K.
    """
    bs._validate(s, k, t_total, sigma, r)
    if not 0 <= t_choice <= t_total:
        raise ValueError("decision date must be between now and expiry")
    if t_total == 0.0:
        # at expiry the chooser collapses to max(intrinsic_call, intrinsic_put)
        return max(s - k, k - s, 0.0)
    if t_choice <= 0.0:
        # A decision made now selects the more valuable vanilla option.
        return max(bs.bs_call_price(s, k, t_total, sigma, r),
                   bs.bs_put_price(s, k, t_total, sigma, r))
    k_put = k * math.exp(-r * (t_total - t_choice))
    return (
        bs.bs_call_price(s, k, t_total, sigma, r)
        + bs.bs_put_price(s, k_put, t_choice, sigma, r)
    )


def chooser_delta(
    s: float, k: float, t_total: float, t_choice: float, sigma: float, r: float = 0.0
) -> float:
    bs._validate(s, k, t_total, sigma, r)
    if not 0 <= t_choice <= t_total:
        raise ValueError("decision date must be between now and expiry")
    if t_total == 0:
        return 1.0 if s > k else (-1.0 if s < k else 0.0)
    if t_choice == 0:
        call = bs.bs_call_price(s, k, t_total, sigma, r)
        put = bs.bs_put_price(s, k, t_total, sigma, r)
        if call == put:
            return bs.bs_call_delta(s, k, t_total, sigma, r) - 0.5
        if call > put:
            return bs.bs_call_delta(s, k, t_total, sigma, r)
        return bs.bs_put_delta(s, k, t_total, sigma, r)
    k_put = k * math.exp(-r * (t_total - t_choice))
    return (
        bs.bs_call_delta(s, k, t_total, sigma, r)
        + bs.bs_put_delta(s, k_put, t_choice, sigma, r)
    )


# ---------- Binary (digital) put ----------

def digital_put_value(
    s: float,
    k: float,
    t: float,
    sigma: float,
    payoff: float = 10.0,
    r: float = 0.0,
) -> float:
    """Digital (cash-or-nothing) put paying `payoff` if S_T < K, else 0.

    Closed form: Q * exp(-r*t) * N(-d2).
    """
    bs._validate(s, k, t, sigma, r)
    if not math.isfinite(payoff) or payoff < 0:
        raise ValueError("payoff must be finite and nonnegative")
    if t == 0.0:
        return payoff if s < k else 0.0
    if sigma == 0.0:
        return payoff * math.exp(-r * t) if s * math.exp(r * t) < k else 0.0
    d1, d2, _ = bs._d1d2(s, k, t, sigma, r)  # noqa: SLF001
    return payoff * math.exp(-r * t) * bs._ncdf(-d2)  # noqa: SLF001


def digital_put_delta(
    s: float, k: float, t: float, sigma: float, payoff: float = 10.0, r: float = 0.0
) -> float:
    bs._validate(s, k, t, sigma, r)
    if not math.isfinite(payoff) or payoff < 0:
        raise ValueError("payoff must be finite and nonnegative")
    if payoff == 0:
        return 0.0
    if t == 0.0 or sigma == 0.0:
        return float('nan') if s == k * math.exp(-r * t) else 0.0
    d1, d2, vsqrt_t = bs._d1d2(s, k, t, sigma, r)  # noqa: SLF001
    return -payoff * math.exp(-r * t) * bs._npdf(d2) / (s * vsqrt_t)  # noqa: SLF001


# ---------- Down-and-out put (knockout) ----------
# Closed form via Reiner-Rubinstein. With r=q=0, the put DI/DO formulas
# simplify; below we keep r as a parameter for generality.

def _normal_interval(lo: float, hi: float) -> float:
    """Normal mass in [lo, hi], using the smaller tail to avoid cancellation."""
    if lo >= 0:
        return bs._ncdf(-lo) - bs._ncdf(-hi)
    return bs._ncdf(hi) - bs._ncdf(lo)


def _absorbed_payoff_fraction(x: float, cap: float, drift: float, variance: float) -> float:
    """Stable quadrature when an analytic image multiplier exhausts float range.

    Image/free density = exp(-2*x*y/variance). Integrating their positive
    difference in normal-standard-deviation units avoids both a huge multiplier
    and narrow peaks in log-price space. The integrand is bounded by the normal
    density; truncating at 12 standard deviations omits <4e-33 of strike PV.
    """
    sd = math.sqrt(variance)
    mean = x + drift
    lo, hi = max(-12.0, -mean / sd), min(12.0, (cap - mean) / sd)
    if lo >= hi:
        return 0.0

    def value(z):
        y = max(0.0, min(cap, mean + sd * z))
        return bs._npdf(z) * (-math.expm1(y - cap)) * (-math.expm1(-2*x*y/variance))

    def refine(a, b, fa, fm, fb, estimate, tolerance, depth):
        midpoint = (a + b) / 2
        left_mid, right_mid = value((a + midpoint)/2), value((midpoint + b)/2)
        left = (midpoint-a) * (fa + 4*left_mid + fm) / 6
        right = (b-midpoint) * (fm + 4*right_mid + fb) / 6
        error = left + right - estimate
        if abs(error) <= 15*tolerance:
            return left + right + error/15
        if depth == 0:
            raise ArithmeticError('barrier quadrature did not converge')
        return (refine(a, midpoint, fa, left_mid, fm, left, tolerance/2, depth-1)
                + refine(midpoint, b, fm, right_mid, fb, right, tolerance/2, depth-1))

    # Unit-width panels ensure a distant normal peak cannot be missed by an
    # initial wide-panel error estimate. No extra runtime dependency is needed.
    panels = max(1, math.ceil(hi-lo))
    pieces = []
    for index in range(panels):
        a, b = lo+(hi-lo)*index/panels, lo+(hi-lo)*(index+1)/panels
        fa, fm, fb = value(a), value((a+b)/2), value(b)
        estimate = (b-a)*(fa+4*fm+fb)/6
        pieces.append(refine(a,b,fa,fm,fb,estimate,1e-12/panels,24))
    return math.fsum(pieces)


def down_and_out_put(
    s: float, k: float, b: float, t: float, sigma: float, r: float = 0.0
) -> float:
    """Continuously monitored, zero-rebate put under GBM, no past breach.

    Integrate the payoff against the absorbing log-price transition density:
    the free normal density minus its reflected image at log(barrier).
    See docs/NUMERICAL_REVIEW.md for the derivation and validation. This is
    equivalent to the full Reiner–Rubinstein K > B branch, not just its
    reflection term. Discrete monitoring requires a different model.
    """
    bs._validate(s, k, t, sigma, r)
    if not math.isfinite(b) or b <= 0:
        raise ValueError("barrier must be finite and positive")
    if s <= b or k <= b:
        return 0.0
    if t == 0:
        return max(k - s, 0.0)
    if sigma == 0 or sigma * sigma * t == 0:
        terminal = s * math.exp(r * t)
        if min(s, terminal) <= b:
            return 0.0
        return math.exp(-r * t) * max(k - terminal, 0.0)

    variance = sigma * sigma * t
    if not math.isfinite(variance):
        raise ValueError('combined variance exceeds floating-point range')
    sd = math.sqrt(variance)
    drift = (r - 0.5 * sigma * sigma) * t
    x = math.log(s / b)
    cap = math.log(k / b)
    image_exponent = -2 * drift * x / variance
    if image_exponent > 500:
        return k * math.exp(-r*t) * _absorbed_payoff_fraction(x, cap, drift, variance)

    def truncated_payoff(mean):
        mass = _normal_interval(-mean / sd, (cap - mean) / sd)
        first_moment = math.exp(mean + variance / 2) * _normal_interval(
            (-mean - variance) / sd, (cap - mean - variance) / sd
        )
        return max(k * mass - b * first_moment, 0.0)

    direct = truncated_payoff(x + drift)
    reflected = truncated_payoff(-x + drift)
    # Large positive exponents use the stable density integral above; here an
    # underflowed reflected tail has negligible contribution even after scaling.
    image = 0.0 if reflected == 0 else math.exp(image_exponent) * reflected
    return max(0.0, min(bs.bs_put_price(s, k, t, sigma, r),
                        math.exp(-r * t) * (direct - image)))


def _di_put(
    s: float, k: float, b: float, t: float, sigma: float, r: float = 0.0
) -> float:
    """Knock-in value from in/out parity (same continuous-monitoring model)."""
    return bs.bs_put_price(s, k, t, sigma, r) - down_and_out_put(s, k, b, t, sigma, r)


def down_and_out_put_delta(
    s: float, k: float, b: float, t: float, sigma: float, r: float = 0.0,
    h: float = 1e-3,
) -> float:
    """Numerical delta with a stencil that stays above an unbreached barrier."""
    down_and_out_put(s, k, b, t, sigma, r)  # validate all pricing inputs first
    if not math.isfinite(h) or h <= 0:
        raise ValueError('finite-difference step must be finite and positive')
    if s <= b:
        return 0.0  # already knocked out; moving spot does not revive the contract
    h = min(h, (s-b)/2)
    if s+h == s or s-h == s:
        return float('nan')
    return (
        down_and_out_put(s + h, k, b, t, sigma, r)
        - down_and_out_put(s - h, k, b, t, sigma, r)
    ) / (2 * h)


# ---------- Round 4 standard set ----------

ROUND4_DEFAULTS = {
    "year_basis": 365.0,
    "expiry_days": 21,
    "chooser_strike": 50.0,
    "chooser_decision_days": 14,
    "binary_put_strike": 40.0,
    "binary_put_payoff": 10.0,
    "knockout_put_strike": 45.0,
    "knockout_put_barrier": 35.0,
}


def price_round4_set(spot: float, sigma: float, year_basis: float = 365.0):
    if not math.isfinite(year_basis) or year_basis <= 0:
        raise ValueError("year_basis must be finite and positive")
    t = ROUND4_DEFAULTS["expiry_days"] / year_basis
    t_c = ROUND4_DEFAULTS["chooser_decision_days"] / year_basis
    chooser = chooser_value(
        spot, ROUND4_DEFAULTS["chooser_strike"], t, t_c, sigma
    )
    binary = digital_put_value(
        spot,
        ROUND4_DEFAULTS["binary_put_strike"],
        t,
        sigma,
        ROUND4_DEFAULTS["binary_put_payoff"],
    )
    knockout = down_and_out_put(
        spot,
        ROUND4_DEFAULTS["knockout_put_strike"],
        ROUND4_DEFAULTS["knockout_put_barrier"],
        t,
        sigma,
    )
    chooser_d = chooser_delta(
        spot, ROUND4_DEFAULTS["chooser_strike"], t, t_c, sigma
    )
    binary_d = digital_put_delta(
        spot,
        ROUND4_DEFAULTS["binary_put_strike"],
        t,
        sigma,
        ROUND4_DEFAULTS["binary_put_payoff"],
    )
    knockout_d = down_and_out_put_delta(
        spot,
        ROUND4_DEFAULTS["knockout_put_strike"],
        ROUND4_DEFAULTS["knockout_put_barrier"],
        t,
        sigma,
    )
    return [
        ExoticContract(
            "chooser_K=50",
            chooser,
            chooser_d,
            f"= Call(S,50,21d) + Put(S,50,14d). T_c = decision date.",
        ),
        ExoticContract(
            "binary_put_K=40_pays=10",
            binary,
            binary_d,
            "= 10 * N(-d2). Tail probability depends on spot and volatility.",
        ),
        ExoticContract(
            "down_and_out_put_K=45_B=35",
            knockout,
            knockout_d,
            f"Vanilla put minus down-and-in put (Reiner-Rubinstein).",
        ),
    ]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--spot", type=float, required=True, help="Aether Crystal spot (S).")
    p.add_argument("--sigma", type=float, required=True, help="Annualized vol (e.g. 0.30).")
    p.add_argument("--year-basis", type=float, default=365.0)
    args = p.parse_args()
    contracts = price_round4_set(args.spot, args.sigma, args.year_basis)
    width = max(len(c.name) for c in contracts)
    print(f"{'contract':<{width}}  fair_value     delta      notes")
    for c in contracts:
        print(f"{c.name:<{width}}  {c.fair_value:>10.4f}  {c.delta:>+8.4f}   {c.notes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
