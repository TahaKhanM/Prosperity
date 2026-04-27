"""Implementation of trader id alpha on top of round 3 results to see if there's any improvement

NOTE: TEST SUBMISSION ONLY. Local simulation against day-2 data in
v12's framework shows the cross-strike taker pair trade has negative
expected edge at every (threshold, hold) combination tested:
   z>=1.5 hold=10t  -> -1.92 shells/fire on K=5300/5400
   z>=2.0 hold=10t  -> -1.81 shells/fire on K=5300/5400
   z>=3.0 hold=100t -> -1.23 shells/fire on K=5300/5400
The signal exists structurally (autocorr decays from 0.85 -> 0.37 over
10 ticks) but only ~23% of predicted reversion is captured in 100t,
which doesn't cover the 2.5-shell crossing cost. Submitting anyway to
see whether hosted matches local sim.

Lineage / motivation
--------------------
v14 attempted a single-strike IV residual scalp (K=5300/5400/5500 each
trading independently against its own residual EMA). It showed only
+917 lift on rust BT and faces a structural problem: submitted v12's
smile MM uses SMILE_A0_EMA_ALPHA = 0.40 (half-life 1.4 ticks) which
ALREADY absorbs the per-strike level-residual signal as a maker.
v14's scalp tries to capture the same edge as a TAKER (paying spread),
which is uneconomic at most strikes.

v15 hunts the alpha smile MM does NOT exploit: cross-strike SHAPE
mispricings. The smile MM refits a0 only (level), never a1 (skew) or
a2 (convexity). When two adjacent strikes' IVs diverge in a way that
implies a smile-shape error, the residual SPREAD between them persists
much longer than each single residual.

Empirical evidence (vol_surface_residuals.csv, 30 000 ticks)
------------------------------------------------------------
                           half-life   sigma     rho1
single-strike residual K=5300    1.82t   0.0042   0.683
single-strike residual K=5400    2.68t   0.0053   0.772
single-strike residual K=5500    1.43t   0.0054   0.616

PAIR (K=5300 - K=5400)           8.02t   0.00736  0.917
PAIR (K=5400 - K=5500)           6.05t   0.00600  0.892

Pair half-life is 3-4x longer than single-strike. This is the smile-
shape signature that smile MM (level-only) cannot absorb. A taker can
fire on the spread, fill in 1-2 ticks, and capture reversion before
half-life elapses (6-8 ticks of room).

Per-fire economics (at S=5237, T=6d, IV=0.244, vega-neutral hedge):
                               shells/sigma_pair   break-even z
  K=5300/5400 pair (lots 2:3)         ~1.84              0.5
  K=5400/5500 pair (lots 1:2)         ~1.01              1.0

v15 sets thresholds at z=1.0 (5300/5400) and z=1.5 (5400/5500), well
above break-even.

What v15 changes vs submitted v12
---------------------------------
Only adds the pair-trade module. HYD MM, VFE MM, smile MM, accumulation,
identity-arb, counterparty hook are byte-identical to submitted v12 so
the hosted +11,654 baseline is preserved. The pair trade is purely
additive.

Pair-trade design
-----------------
Per tick, after smile MM has refit a0:

  for each pair (K1, K2):
      res(K) = IV_market(K) - (a0 + a1*m_K + a2*m_K^2 + bias_K)
      pair_res = res(K1) - res(K2) - mean_pair_static
      pair_ema = ewma(pair_res, alpha=0.05)
      dev = pair_res - pair_ema
      z = dev / sigma_pair
      if |z| > threshold(K1,K2):
          lots1 = clamp(BASE + SCALE * (|z| - threshold), MIN, MAX)
          lots2 = lots1 * ratio2 / ratio1   (vega-neutral hedge)
          if z > 0:  sell lots1 K=K1, buy lots2 K=K2
          if z < 0:  buy  lots1 K=K1, sell lots2 K=K2
          (cap each leg by per-strike inventory cap)

Both legs cross the spread. Per-strike inventory caps keep exposure
bounded if the pair signal persists.

Risks
-----
1. Smile shape can genuinely change (a1/a2 drift). The slow EMA
   (alpha=0.05) adapts but not instantly — sustained shape change
   could leave us holding losing positions for ~30 ticks before the
   EMA catches up.
2. Partial fills on either leg leave residual single-strike exposure
   until next tick. Mitigated by: pair signal persists 6-8 ticks, so
   subsequent fires re-balance.
3. Both pairs share K=5400. Combined K=5400 inventory is bounded by
   per-strike cap (80 lots in either direction).

START_TTE_DAYS = 6.0 stays from submitted v12 (calibrated for IMC
hosted day-2 backtester). Flip to 5.0 only for live R3.

Submission contract: run(state) -> (orders, conversions, traderData).
"""
from __future__ import annotations

import json
import math
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState


# ---------- product constants ----------------------------------------------

HYD = "HYDROGEL_PACK"
VFE = "VELVETFRUIT_EXTRACT"
CAP_H = 200
CAP_V = 200
CAP_VOU = 300

ANCHOR = 10000.0
A_W = 0.35
A_HYD = 0.08                # EMA alpha on HYD fair
H_TAKE = 5
H_QE = 6
H_SIZE = 100
H_IMB = 0.0                 # HYD imb-k1 skew slope (v9 unchanged)
H_WALL_W = 0.9              # v10 NEW: weight of wall-mid in HYD fair input

A_VFE = 0.20
V_TAKE = 1
V_QE = 1
V_SIZE = 40
V_IMB_K2 = 8.0              # v10 NEW: VFE imb-k2 skew slope (capped)
V_SKEW_CAP = 2.0            # v10 NEW: |skew| <= 2 shells
WALL_VOL_THR_HYD = 15       # ignore HYD levels with vol < 15 for wall-mid
WALL_VOL_THR_VFE = 20       # ignore VFE levels with vol < 20 for wall-mid

ACC_STRIKES = [4000, 4500]
ACC_SLACK = 4
ACC_SIZE_PER_TICK = 50
EXIT_SLACK = 2

# Counterparty copy hook (v12) — live-only. Historical buyer/seller fields
# are 100% empty in R3 days 0/1/2.  If IMC plants a named smart bot in live
# market_trades (P3 precedent: 'Olivia'), accumulate horizon-PnL per name
# and skew our quotes by ±1 shell in their inferred direction once the name
# has enough trade history with statistically-significant directional bias.
CP_TRACK_MIN_TRADES = 20
CP_SHARPE_THR = 2.0
CP_MAX_NAMES = 8
CP_SKEW_SHELLS = 1.0           # cap on counterparty-driven fair skew


# ---------- Round 4 named counterparty alpha -------------------------------
# Explicit buyer -> seller VFE signals found from Round 4 historical data.
# These are directional signals on the underlying VELVETFRUIT_EXTRACT.
#
# Format:
#   (buyer, seller): (direction, horizon_ticks, vfe_fair_bias, option_S_bias)
#
# vfe_fair_bias affects direct VFE market making.
# option_S_bias shifts the S input used by voucher Black-Scholes pricing.
USE_NAMED_VFE_CP_ALPHA = True

NAMED_VFE_CP_SIGNALS = {
    ("Mark 67", "Mark 49"): ("SHORT", 1000, 4.0, 4.0), 
    ("Mark 67", "Mark 22"): ("SHORT", 1000, 3.0, 3.0),
    ("Mark 55", "Mark 14"): ("SHORT", 10000, 2.0, 2.0),
    ("Mark 14", "Mark 55"): ("LONG", 10000, 2.0, 2.0),
}

NAMED_VFE_CP_MAX_FAIR_BIAS = 6.0
NAMED_VFE_CP_MAX_OPTION_S_BIAS = 6.0

# Optional safety: do not let stale active signals accumulate forever.
NAMED_VFE_CP_MAX_ACTIVE = 20

# Cross-strike pair trade was experimentally negative in the file header.
# Keep off unless a fresh backtest proves it helps.
USE_PAIR_TRADE = False

# ---------- Phase 1 smile MM constants (unchanged from v9) ------------------

SMILE_STRIKES = (5000, 5100, 5200, 5300, 5400, 5500)

START_TTE_DAYS = 6.0
DAY_TICKS = 1_000_000.0
SMILE_TTE_FLOOR_DAYS = 0.25

SMILE_A0_BASE = 0.2420
SMILE_A0_DRIFT_PER_DAY = 0.00275
SMILE_A1_BASE = -0.011
SMILE_A1_DRIFT_PER_DAY = -0.075
SMILE_A2_BASE = 7.21
SMILE_A2_DRIFT_PER_DAY = 0.815

SMILE_A0_EMA_ALPHA = 0.40
SMILE_TAKE_EDGE_SHELLS = 0.7
SMILE_QUOTE_VEGA_FRAC = 0.006
SMILE_QUOTE_MIN_EDGE = 1
SMILE_QUOTE_SIZE = 8
SMILE_SOFT_CAP = 80
SMILE_VEGA_FLOOR = 0.5

SMILE_PER_STRIKE_BIAS: Dict[int, float] = {
    5000: -0.0077,
    5100: +0.0004,
    5200: +0.0076,
    5300: +0.0087,
    5400: -0.0144,
    5500: -0.0067,
}

SMILE_WARMUP_TICKS = 15

# ---- IV smile and black scholes constants ---------


USE_OPTION_IMPLIED_VFE_BIAS = True
# W_OPTION_S_TO_VFE = 0.075
# W_OPTION_S_TO_VFE = 0.1
W_OPTION_S_TO_VFE = 0.125
# W_OPTION_S_TO_VFE = 0.15
# W_OPTION_S_TO_VFE = 0.175
OPTION_S_CONF_TH = 1.5
OPTION_S_BIAS_CAP = 3.0

# ---------- delta-lag signal constants --------------------------------------

USE_DELTA_LAG = True

# Trade only near-ish strikes. Deep ITM 4000/4500 are already handled by intrinsic arb.
DELTA_LAG_STRIKES = (5000, 5100, 5300, 5400, 5500)

# 
# edge = model_expected_option_move - actual_option_move
DELTA_LAG_EDGE_TH = 1.5

# Avoid wide-spread taker trades.
DELTA_LAG_MAX_SPREAD = 2

# Small size first. This is a taker module.
DELTA_LAG_MAX_TAKE = 2

# Do not trade if underlying barely moved.
DELTA_LAG_MIN_ABS_DS = 1.0


# ---------- v15 cross-strike pair-trade constants --------------------------
# Trades shape mispricings between adjacent strikes — the part of the IV
# residual structure that smile MM (level-only via a0 EMA) does NOT absorb.
# Pair half-life from research = 6-8 ticks (vs 1-3 ticks single-strike).
#
# IMPORTANT: pair_res in v12's framework (which subtracts per-strike bias_k
# in fair_iv) is ALREADY zero-mean. Verified empirical mean over 30k ticks:
#   K=5300/5400 v12-frame: mean = 0.00005  (essentially zero)
#   K=5400/5500 v12-frame: mean = -0.00007 (essentially zero)
# So mean_pair = 0 here. The +0.0231 / -0.0078 means in research data are
# the raw means before bias subtraction, which v12 already handles.
#
# No EMA either: alpha=0.05 EMA absorbs the actual signal we want to trade,
# crushing fire frequency from 32% (raw) to 0.34% (after EMA dev). Trade
# directly against zero.

# (K1, K2, sigma_pair, ratio_K1, ratio_K2)  — vega-neutral hedge ratios
PAIR_TRADES: List[Tuple[int, int, float, int, int]] = [
    (5300, 5400, 0.00736, 2, 3),   # half-life 8.02t, vega ratio 1.49
    (5400, 5500, 0.00600, 1, 2),   # half-life 6.05t, vega ratio 2.09
]

# Per-pair z trigger.  Set above break-even after 2-leg crossing cost.
# 5300/5400: 1.84 shells/z gross, ~2.5 shells crossing cost (2-shell books)
#            -> z >= 1.36 break-even, use 1.5 for margin (fires 11.65%)
# 5400/5500: 1.01 shells/z gross, ~2.0 shells crossing cost (mixed spreads)
#            -> z >= 1.98 break-even, use 2.0 (fires 5.32%)
PAIR_TRIGGER_Z: Dict[Tuple[int, int], float] = {
    (5300, 5400): 1.5,
    (5400, 5500): 2.0,
}

# Conviction-scaled K1 leg lots: clamp(BASE + SCALE*(|z| - threshold), MIN, MAX)
PAIR_BASE_LOTS = 2
PAIR_LOTS_PER_Z = 4
PAIR_MIN_LOTS = 1
PAIR_MAX_LOTS = 12

# Hard absolute per-strike cap for pair-derived inventory (lots).  K=5400
# is shared by both pairs — its cap accounts for combined exposure.
PAIR_POS_CAP: Dict[int, int] = {
    5300: 60,
    5400: 80,
    5500: 60,
}


# ---------- Black-Scholes (inlined, unchanged) -----------------------------

_SQRT2 = math.sqrt(2.0)
_SQRT_2PI = math.sqrt(2.0 * math.pi)


def _ncdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / _SQRT2))


def _npdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / _SQRT_2PI


def bs_call_price(s: float, k: float, t: float, sigma: float, r: float = 0.0) -> float:
    if t <= 0.0 or sigma <= 0.0:
        return max(s - k, 0.0)
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
    if t <= 0.0 or sigma <= 0.0:
        return 0.0
    vsqrt_t = sigma * math.sqrt(t)
    d1 = (math.log(s / k) + (r + 0.5 * sigma * sigma) * t) / vsqrt_t
    return s * _npdf(d1) * math.sqrt(t)


def implied_vol_call(price: float, s: float, k: float, t: float,
                     r: float = 0.0, tol: float = 1e-6, max_iter: int = 40,
                     sigma_lo: float = 1e-6, sigma_hi: float = 5.0) -> float:
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
    for _ in range(120):
        mid = 0.5 * (lo + hi)
        p = bs_call_price(s, k, t, mid, r)
        if abs(p - price) < tol:
            return mid
        if (p - price) * (p_lo - price) < 0:
            hi = mid; p_hi = p
        else:
            lo = mid; p_lo = p
    return 0.5 * (lo + hi)

# ---------- implied underlying price from options analysis (found by solving for implied volatility using volatility smile, then plugging into black scholes to get price)

# finds the implied/fair price of option underlying based on volatility smile and black scholes

def implied_underlying_from_options(depths, smile_state, timestamp):
    """
    Returns:
        (S_consensus, edge, confidence)
    """

    a0 = smile_state.get("smile_a0")
    a1 = smile_state.get("smile_a1")
    a2 = smile_state.get("smile_a2")

    if a0 is None or a1 is None or a2 is None:
        return None, 0.0, 0.0

    ve_depth = depths.get(VFE)
    if ve_depth is None:
        return None, 0.0, 0.0

    S_market = _micro(ve_depth)
    if S_market is None or S_market <= 0:
        return None, 0.0, 0.0

    t = _tte_years(timestamp)
    if t <= 0:
        return None, 0.0, 0.0

    implied_S = []
    weights = []

    for k in SMILE_STRIKES:
        sym = f"VEV_{k}"
        d = depths.get(sym)
        if d is None:
            continue

        mid_px = _mid(d)
        if mid_px is None or mid_px <= 0:
            continue

        # --- use SMILE vol, not market IV ---
        bias_k = SMILE_PER_STRIKE_BIAS.get(k, 0.0)

        # --- invert BS to solve for S, but recompute smile sigma at each S_mid ---
        S_low, S_high = 1.0, 20000.0

        valid = True

        for _ in range(40):
            S_mid = 0.5 * (S_low + S_high)

            m_mid = math.log(S_mid / float(k))
            sigma_mid = a0 + a1 * m_mid + a2 * m_mid * m_mid + bias_k

            if sigma_mid <= 0.01 or not (sigma_mid == sigma_mid):
                valid = False
                break

            price_mid = bs_call_price(S_mid, float(k), t, sigma_mid)

            if price_mid > mid_px:
                S_high = S_mid
            else:
                S_low = S_mid

        if not valid:
            continue

        S_imp = 0.5 * (S_low + S_high)

        # recompute final sigma at solved S_imp
        m_imp = math.log(S_imp / float(k))
        sigma_imp = a0 + a1 * m_imp + a2 * m_imp * m_imp + bias_k

        if sigma_imp <= 0.01 or not (sigma_imp == sigma_imp):
            continue

        # --- weight by vega (reliability) ---
        vega = bs_call_vega(S_imp, float(k), t, sigma_imp)
        if vega < 0.1:
            continue

        implied_S.append(S_imp)
        weights.append(vega)

    if not implied_S:
        return None, 0.0, 0.0

    # --- weighted average ---
    total_w = sum(weights)
    S_consensus = sum(s * w for s, w in zip(implied_S, weights)) / total_w

    edge = S_consensus - S_market

    # confidence = dispersion inverse
    mean = S_consensus
    var = sum(w * (s - mean) ** 2 for s, w in zip(implied_S, weights)) / total_w
    std = math.sqrt(var)

    confidence = 0.0 if std == 0 else abs(edge) / std

    return S_consensus, edge, confidence



# ---------- scalper for fair price (calculated from options) - actual price mismatch
# module to actually run the implied-volatility scalping (detect mismatch from fair price and true price using IV found from volatility smile, then black scholes)



def _sgn(x: float) -> int:
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def _has_existing_side(out: Dict[str, List[Order]], sym: str, side: int) -> bool:
    """
    side = +1 means already buying
    side = -1 means already selling
    """
    for o in out.get(sym, []):
        if side > 0 and o.quantity > 0:
            return True
        if side < 0 and o.quantity < 0:
            return True
    return False


def single_strike_scalp(
    depths,
    positions,
    smile_state,
    timestamp,
    underlying_edge: float = 0.0,
    pair_active_strikes=None,
    existing_orders=None,
):
    out = {}
    pair_active_strikes = pair_active_strikes or set()
    existing_orders = existing_orders or {}

    a0 = smile_state.get("smile_a0")
    a1 = smile_state.get("smile_a1")
    a2 = smile_state.get("smile_a2")

    if a0 is None or a1 is None or a2 is None:
        return out

    ve_depth = depths.get(VFE)
    if ve_depth is None:
        return out

    S = _micro(ve_depth)
    if S is None or S <= 0:
        return out

    t = _tte_years(timestamp)
    if t <= 0:
        return out

    # Empirical residual sigmas.
    # Tune these from your backtest logs.
    SIGMA_BY_STRIKE = {
        5300: 0.0042,
        5400: 0.0053,
        5500: 0.0054,
    }

    SCALP_TRIGGER_Z = 2.25

    for k in [5300, 5400, 5500]:
        sym = f"VEV_{k}"
        d = depths.get(sym)
        if d is None:
            continue

        mid = _mid(d)
        if mid is None or mid <= 0:
            continue

        iv_m = implied_vol_call(mid, S, float(k), t)
        if not (iv_m == iv_m) or iv_m <= 0.005:
            continue

        m = math.log(S / float(k))
        bias_k = SMILE_PER_STRIKE_BIAS.get(k, 0.0)
        fair_iv = a0 + a1 * m + a2 * m * m + bias_k

        residual = iv_m - fair_iv
        sigma = SIGMA_BY_STRIKE.get(k, 0.005)

        if sigma <= 0:
            continue

        z = residual / sigma

        if abs(z) < SCALP_TRIGGER_Z:
            continue

        bid = _bb(d)
        ask = _ba(d)
        pos = positions.get(sym, 0)

        size = min(3 + int(abs(z)), 10)

        # z > 0: option IV rich -> sell
        # z < 0: option IV cheap -> buy
        desired_side = -_sgn(z)  # +1 buy, -1 sell

        # 1. Don't fight pair trades: reduce size if pair touched this strike.
        if k in pair_active_strikes:
            size = max(1, size // 2)

        # 2. Don't fight underlying bias.
        # underlying_edge > 0 means options imply VFE should be higher,
        # so buying calls is more aligned than selling calls.
        underlying_side = _sgn(underlying_edge)

        if underlying_side != 0 and desired_side != underlying_side:
            size = max(1, size // 2)

        # 3. Don't overlap with existing MM/pair orders.
        if _has_existing_side(existing_orders, sym, desired_side):
            continue

        if desired_side > 0:
            # BUY cheap option
            if ask is not None:
                avail = -d.sell_orders[ask]
                room = _cb(pos, CAP_VOU, 0, size)
                sz = min(size, avail, room)
                if sz > 0:
                    out.setdefault(sym, []).append(Order(sym, ask, sz))

        else:
            # SELL rich option
            if bid is not None:
                avail = d.buy_orders[bid]
                room = _cs(pos, CAP_VOU, 0, size)
                sz = min(size, avail, room)
                if sz > 0:
                    out.setdefault(sym, []).append(Order(sym, bid, -sz))

    return out


# ---------- delta lag module ---------------------------------------------

def _delta_lag_signal(
    lag_state: Dict,
    depths: Dict[str, OrderDepth],
    positions: Dict[str, int],
    timestamp: int,
    smile_state: Dict,
    existing_orders: Optional[Dict[str, List[Order]]] = None,
) -> Dict[str, List[Order]]:
    """
    Detects when a voucher has not moved enough relative to the underlying move.

    edge = delta * dS - dC

    edge > 0:
        option underreacted / lagged upward move -> BUY option

    edge < 0:
        option overreacted or lagged downward move -> SELL option

    This is a taker module, so thresholds/spread filters are important.
    """
    out: Dict[str, List[Order]] = {}
    existing_orders = existing_orders or {}

    vd = depths.get(VFE)
    if vd is None:
        return out

    S = _micro(vd)
    if S is None or S <= 0:
        return out

    t = _tte_years(timestamp)
    if t <= 0:
        return out

    prev_S = lag_state.get("prev_S")

    # Update prev_S even if we cannot trade yet.
    lag_state["prev_S"] = S

    if prev_S is None:
        # Still need to store option mids below for next tick.
        for k in DELTA_LAG_STRIKES:
            sym = f"VEV_{k}"
            d = depths.get(sym)
            if d is None:
                continue
            mid = _mid(d)
            if mid is not None:
                lag_state[f"prev_mid_{k}"] = mid
        return out

    dS = S - float(prev_S)

    if abs(dS) < DELTA_LAG_MIN_ABS_DS:
        # Update option mids and skip trading.
        for k in DELTA_LAG_STRIKES:
            sym = f"VEV_{k}"
            d = depths.get(sym)
            if d is None:
                continue
            mid = _mid(d)
            if mid is not None:
                lag_state[f"prev_mid_{k}"] = mid
        return out

    a0 = smile_state.get("smile_a0")
    a1 = smile_state.get("smile_a1")
    a2 = smile_state.get("smile_a2")

    for k in DELTA_LAG_STRIKES:
        sym = f"VEV_{k}"
        d = depths.get(sym)
        if d is None:
            continue

        bid = _bb(d)
        ask = _ba(d)
        mid = _mid(d)

        if bid is None or ask is None or mid is None or mid <= 0:
            continue

        spread = ask - bid
        if spread > DELTA_LAG_MAX_SPREAD:
            lag_state[f"prev_mid_{k}"] = mid
            continue

        prev_mid = lag_state.get(f"prev_mid_{k}")

        # Update after reading previous value.
        lag_state[f"prev_mid_{k}"] = mid

        if prev_mid is None:
            continue

        dC = mid - float(prev_mid)

        # Prefer smile-model delta if available, because market IV can be noisy.
        sigma = None
        if a0 is not None and a1 is not None and a2 is not None:
            m = math.log(S / float(k))
            sigma_model = a0 + a1 * m + a2 * m * m + SMILE_PER_STRIKE_BIAS.get(k, 0.0)
            if sigma_model > 0.005 and sigma_model == sigma_model:
                sigma = sigma_model

        # Fallback to market implied vol.
        if sigma is None:
            iv_m = implied_vol_call(mid, S, float(k), t)
            if not (iv_m == iv_m) or iv_m <= 0.005:
                continue
            sigma = iv_m

        delta = bs_call_delta(S, float(k), t, sigma)

        expected_dC = delta * dS
        edge = expected_dC - dC

        # Must beat threshold plus some spread cost.
        # Since we cross, require more edge when spread is wider.
        effective_threshold = DELTA_LAG_EDGE_TH + 0.25 * spread

        if abs(edge) < effective_threshold:
            continue

        pos = positions.get(sym, 0)

        if edge > 0:
            # Option underreacted upward / too cheap -> BUY at ask.
            desired_side = +1
            if _has_existing_side(existing_orders, sym, desired_side):
                continue

            avail = -d.sell_orders[ask]
            room = _cb(pos, CAP_VOU, 0, DELTA_LAG_MAX_TAKE)
            sz = min(DELTA_LAG_MAX_TAKE, avail, room)

            if sz > 0:
                out.setdefault(sym, []).append(Order(sym, ask, sz))

        else:
            # Option overreacted / too rich -> SELL at bid.
            desired_side = -1
            if _has_existing_side(existing_orders, sym, desired_side):
                continue

            avail = d.buy_orders[bid]
            room = _cs(pos, CAP_VOU, 0, DELTA_LAG_MAX_TAKE)
            sz = min(DELTA_LAG_MAX_TAKE, avail, room)

            if sz > 0:
                out.setdefault(sym, []).append(Order(sym, bid, -sz))

    return out

# ---------- helpers -------------------------------------------------------


def _bb(d):
    return max(d.buy_orders) if d.buy_orders else None


def _ba(d):
    return min(d.sell_orders) if d.sell_orders else None


def _mid(d):
    b, a = _bb(d), _ba(d)
    return None if b is None or a is None else (b + a) / 2.0


def _micro(d):
    b, a = _bb(d), _ba(d)
    if b is None or a is None:
        return None
    bv = d.buy_orders[b]
    av = -d.sell_orders[a]
    t = bv + av
    return (b + a) / 2.0 if t <= 0 else (a * bv + b * av) / t


def _imb(d):
    """Level-1 signed imbalance (v9 back-compat)."""
    b, a = _bb(d), _ba(d)
    if b is None or a is None:
        return 0.0
    bv = d.buy_orders[b]
    av = -d.sell_orders[a]
    t = bv + av
    return 0.0 if t <= 0 else (bv - av) / t


def _imb_k2(d):
    """Top-2-levels signed imbalance.  Empirical regression slope:
    HYD next-tick mid change = 12 × imb_k2 (t≈35).
    VFE next-tick mid change =  3 × imb_k2 (t≈20).
    """
    if not d.buy_orders or not d.sell_orders:
        return 0.0
    bs = sorted(d.buy_orders.items(), key=lambda x: -x[0])[:2]
    asks = sorted(d.sell_orders.items(), key=lambda x: x[0])[:2]
    bv = sum(v for _, v in bs)
    av = sum(-v for _, v in asks)
    t = bv + av
    return 0.0 if t <= 0 else (bv - av) / t


def _wall_mid(d, vol_thr):
    """Mid of highest-volume bid level and highest-volume ask level
    among quotes whose individual volume is >= vol_thr.  None if no
    qualifying levels.

    Past-winner reference (TimoDiehm P3 2nd, jmerle 25th): the "popular"
    level is far more stable under noise than the 1-shell-deep top-of-book.
    """
    if not d.buy_orders or not d.sell_orders:
        return None
    bids = [(p, v) for p, v in d.buy_orders.items() if v >= vol_thr]
    asks = [(p, -v) for p, v in d.sell_orders.items() if -v >= vol_thr]
    if not bids or not asks:
        return None
    wb = max(bids, key=lambda x: x[1])[0]
    wa = max(asks, key=lambda x: x[1])[0]
    return (wb + wa) / 2.0


def _strike(s):
    if s.startswith("VEV_"):
        try:
            return int(s[4:])
        except Exception:
            return None
    return None


def _cb(p, c, ad, w): return max(0, min(w, c - (p + ad)))
def _cs(p, c, ad, w): return max(0, min(w, c + (p - ad)))
def _ew(p, s, a):     return s if p is None else p * (1 - a) + s * a
def _clamp(x, lo, hi): return max(lo, min(hi, x))


def _update_cp_state(cp_state: Dict, market_trades, mids_now: Dict[str, float]) -> None:
    """Advance counterparty-PnL accounting using last-tick pending fills + current mids."""
    pending = cp_state.get("pending", [])
    new_pending = []
    by_name = cp_state.setdefault("by_name", {})
    for entry in pending:
        sym = entry["s"]; px = entry["p"]; q = entry["q"]; name = entry["n"]
        m = mids_now.get(sym)
        if m is None:
            new_pending.append(entry)
            continue
        pnl = q * (m - px)
        rec = by_name.setdefault(name, {"n": 0, "pnl": 0.0, "p2": 0.0, "sym_pnl": {}})
        rec["n"] += 1
        rec["pnl"] += pnl
        rec["p2"] += pnl * pnl
        sp = rec.setdefault("sym_pnl", {})
        sp[sym] = sp.get(sym, 0.0) + pnl
    cp_state["pending"] = new_pending
    if len(by_name) > CP_MAX_NAMES:
        names = sorted(by_name.items(), key=lambda kv: kv[1]["n"])
        for k_, _ in names[: max(0, len(names) - CP_MAX_NAMES)]:
            by_name.pop(k_, None)
    for sym, trades in (market_trades or {}).items():
        for tr in trades or []:
            buyer = (getattr(tr, "buyer", "") or "").strip()
            seller = (getattr(tr, "seller", "") or "").strip()
            qty = int(getattr(tr, "quantity", 0) or 0)
            price = float(getattr(tr, "price", 0.0) or 0.0)
            if qty <= 0 or price <= 0:
                continue
            if buyer:
                cp_state.setdefault("pending", []).append({"s": sym, "p": price, "q": +qty, "n": buyer})
            if seller:
                cp_state.setdefault("pending", []).append({"s": sym, "p": price, "q": -qty, "n": seller})


def _cp_signed_skew(cp_state: Dict, sym: str) -> float:
    """Return skew in shells based on smart-counterparty signal for `sym`.
    Returns 0 unless a name has accumulated >= CP_TRACK_MIN_TRADES with
    Sharpe > CP_SHARPE_THR.  Empty in historical data.
    """
    skew = 0.0
    for name, rec in cp_state.get("by_name", {}).items():
        n = rec.get("n", 0)
        if n < CP_TRACK_MIN_TRADES:
            continue
        mean = rec.get("pnl", 0.0) / n
        var = max(0.0, rec.get("p2", 0.0) / n - mean * mean)
        if var <= 0:
            continue
        se = (var / n) ** 0.5
        if se <= 0:
            continue
        z = mean / se
        if abs(z) <= CP_SHARPE_THR:
            continue
        sym_pnl = rec.get("sym_pnl", {}).get(sym, 0.0)
        if sym_pnl > 0:
            skew += +CP_SKEW_SHELLS
        elif sym_pnl < 0:
            skew += -CP_SKEW_SHELLS
    return _clamp(skew, -2 * CP_SKEW_SHELLS, 2 * CP_SKEW_SHELLS)


def _update_named_vfe_cp_alpha(named_cp_state: Dict, market_trades, timestamp: int) -> None:
    """
    Stores active explicit VFE counterparty signals.

    A signal activates when one of the discovered buyer->seller relationships
    appears in market_trades[VFE]. It expires after its fitted horizon.
    """
    if not USE_NAMED_VFE_CP_ALPHA:
        named_cp_state["active"] = []
        return

    active = named_cp_state.setdefault("active", [])

    # Drop expired signals first.
    active = [x for x in active if int(x.get("expiry", -1)) >= timestamp]

    for tr in (market_trades or {}).get(VFE, []) or []:
        buyer = (getattr(tr, "buyer", "") or "").strip()
        seller = (getattr(tr, "seller", "") or "").strip()
        key = (buyer, seller)

        if key not in NAMED_VFE_CP_SIGNALS:
            continue

        direction, horizon, vfe_bias, option_s_bias = NAMED_VFE_CP_SIGNALS[key]
        sign = +1.0 if direction == "LONG" else -1.0

        active.append({
            "buyer": buyer,
            "seller": seller,
            "direction": direction,
            "expiry": int(timestamp + horizon),
            "vfe_bias": float(sign * vfe_bias),
            "option_s_bias": float(sign * option_s_bias),
        })

    # Keep recent active signals only.
    if len(active) > NAMED_VFE_CP_MAX_ACTIVE:
        active = active[-NAMED_VFE_CP_MAX_ACTIVE:]

    named_cp_state["active"] = active


def _named_vfe_cp_bias(named_cp_state: Dict, timestamp: int) -> Tuple[float, float]:
    """
    Returns:
        (vfe_fair_bias, option_S_bias)

    vfe_fair_bias:
        added to VFE fair value.

    option_S_bias:
        added to the underlying S input used for voucher Black-Scholes.
    """
    if not USE_NAMED_VFE_CP_ALPHA:
        return 0.0, 0.0

    active = [
        x for x in named_cp_state.get("active", [])
        if int(x.get("expiry", -1)) >= timestamp
    ]
    named_cp_state["active"] = active

    vfe_bias = sum(float(x.get("vfe_bias", 0.0)) for x in active)
    option_s_bias = sum(float(x.get("option_s_bias", 0.0)) for x in active)

    vfe_bias = _clamp(vfe_bias, -NAMED_VFE_CP_MAX_FAIR_BIAS, NAMED_VFE_CP_MAX_FAIR_BIAS)
    option_s_bias = _clamp(option_s_bias, -NAMED_VFE_CP_MAX_OPTION_S_BIAS, NAMED_VFE_CP_MAX_OPTION_S_BIAS)

    return vfe_bias, option_s_bias

# ---------- Phase 1 smile MM (unchanged from v9) ---------------------------


def _tte_years(timestamp):
    days_left = max(START_TTE_DAYS - timestamp / DAY_TICKS, SMILE_TTE_FLOOR_DAYS)
    return days_left / 365.0


def _smile_prior(tte_days):
    drift = max(0.0, 8.0 - tte_days)
    a0 = SMILE_A0_BASE + SMILE_A0_DRIFT_PER_DAY * drift
    a1 = SMILE_A1_BASE + SMILE_A1_DRIFT_PER_DAY * drift
    a2 = SMILE_A2_BASE + SMILE_A2_DRIFT_PER_DAY * drift
    return a0, a1, a2


def _smile_voucher_orders(state, depths, positions, timestamp, ve_micro):
    out: Dict[str, List[Order]] = {}
    if ve_micro is None or ve_micro <= 0:
        return out
    t = _tte_years(timestamp)
    if t <= 0:
        return out
    tte_days = t * 365.0
    a0_prior, a1, a2 = _smile_prior(tte_days)

    strike_data: List[Tuple[int, float, float, float]] = []
    for k in SMILE_STRIKES:
        sym = f"VEV_{k}"
        d_ = depths.get(sym)
        if d_ is None:
            continue
        mid_px = _mid(d_)
        if mid_px is None or mid_px <= 0:
            continue
        iv_m = implied_vol_call(mid_px, ve_micro, float(k), t)
        if not (iv_m == iv_m) or iv_m <= 0.005:
            continue
        v = bs_call_vega(ve_micro, float(k), t, iv_m)
        if v < SMILE_VEGA_FLOOR:
            continue
        m = math.log(ve_micro / float(k))
        strike_data.append((k, m, iv_m, v))

    if not strike_data:
        return out

    num = 0.0; den = 0.0
    for (k, m, iv_m, v) in strike_data:
        bias_k = SMILE_PER_STRIKE_BIAS.get(k, 0.0)
        a0_implied = (iv_m - bias_k) - a1 * m - a2 * m * m
        num += v * a0_implied
        den += v
    a0_obs = num / den if den > 0 else a0_prior

    prev = state.get("smile_a0")
    a0 = a0_obs if prev is None else prev * (1.0 - SMILE_A0_EMA_ALPHA) + a0_obs * SMILE_A0_EMA_ALPHA
    state["smile_a0"] = a0
    state["smile_a1"] = a1
    state["smile_a2"] = a2
    state["smile_s"] = ve_micro
    state["smile_tte_days"] = tte_days
    ticks = int(state.get("smile_ticks", 0)) + 1
    state["smile_ticks"] = ticks

    if ticks < SMILE_WARMUP_TICKS:
        return out

    for (k, m, _, v) in strike_data:
        strike_quote_size = SMILE_QUOTE_SIZE
        if k == 5200: # STOP TRADING VEV5200 for SMILE MM since it's a bad trade all the time (too much randomness, price too close to underlying)
            continue
            strike_quote_size = 1
        sym = f"VEV_{k}"
        d_ = depths.get(sym)
        if d_ is None:
            continue
        bias_k = SMILE_PER_STRIKE_BIAS.get(k, 0.0)
        fair_iv = a0 + a1 * m + a2 * m * m + bias_k
        if fair_iv <= 0.005:
            continue
        fair = bs_call_price(ve_micro, float(k), t, fair_iv)
        if fair <= 0:
            continue

        pos = positions.get(sym, 0)
        bid = _bb(d_); ask = _ba(d_)
        bought = sold = 0
        legs: List[Order] = []
        cap = CAP_VOU

        strike_quote_size = SMILE_QUOTE_SIZE
        if k == 5200:
            strike_quote_size = max(1, SMILE_QUOTE_SIZE // 4)

        if ask is not None and ask + SMILE_TAKE_EDGE_SHELLS <= fair:
            avail = -d_.sell_orders[ask]
            sz = _cb(pos, cap, bought, min(avail, strike_quote_size * 4))
            if sz > 0:
                legs.append(Order(sym, ask, sz)); bought += sz
        if bid is not None and bid - SMILE_TAKE_EDGE_SHELLS >= fair:
            avail = d_.buy_orders[bid]
            sz = _cs(pos, cap, sold, min(avail, strike_quote_size * 4))
            if sz > 0:
                legs.append(Order(sym, bid, -sz)); sold += sz

        edge_shells = max(SMILE_QUOTE_MIN_EDGE, v * SMILE_QUOTE_VEGA_FRAC)
        bp = int(math.floor(fair - edge_shells))
        sp = int(math.ceil(fair + edge_shells))
        if bid is not None:
            bp = min(bp, bid + 1)
            sp = max(sp, bid + 1)
        if ask is not None:
            sp = max(sp, ask - 1)
            bp = min(bp, ask - 1)
        bp = max(bp, 1)

        if bp < sp:
            inv = 0.0 if cap == 0 else max(-1.0, min(1.0, (pos + bought - sold) / float(cap)))
            bsz_raw = max(0, int(round(strike_quote_size * (1.0 - inv))))
            ssz_raw = max(0, int(round(strike_quote_size * (1.0 + inv))))
            if pos > SMILE_SOFT_CAP: bsz_raw = 0
            if pos < -SMILE_SOFT_CAP: ssz_raw = 0
            bsz = _cb(pos, cap, bought, bsz_raw)
            ssz = _cs(pos, cap, sold, ssz_raw)
            if bsz > 0 and (ask is None or bp < ask):
                legs.append(Order(sym, bp, bsz))
            if ssz > 0 and (bid is None or sp > bid):
                legs.append(Order(sym, sp, -ssz))

        if legs:
            out.setdefault(sym, []).extend(legs)

    return out


# ---------- v15 cross-strike pair-trade module -----------------------------


def _pair_lots_k1(abs_z: float, threshold: float) -> int:
    """Conviction-proportional sizing on the K1 leg."""
    excess = max(0.0, abs_z - threshold)
    raw = PAIR_BASE_LOTS + PAIR_LOTS_PER_Z * excess
    sz = int(round(raw))
    return max(PAIR_MIN_LOTS, min(PAIR_MAX_LOTS, sz))


def _hedge_lots(sz1: int, ratio1: int, ratio2: int) -> int:
    """Round to nearest hedge size keeping vega-neutral ratio."""
    if sz1 <= 0 or ratio1 <= 0:
        return 0
    return max(1, (sz1 * ratio2 + ratio1 // 2) // ratio1)


def _pair_trade(state: Dict, depths: Dict[str, OrderDepth],
                positions: Dict[str, int], timestamp: int,
                smile_state: Dict) -> Dict[str, List[Order]]:
    """Cross-strike vega-neutral pair trade on smile-shape mispricings.

    Reuses smile_state's a0/a1/a2 (does not refit). Per pair, computes
    the bias-subtracted residual spread (already zero-mean in v12's
    framework) and fires when |z| exceeds the threshold. Trades both
    legs as takers.
    """
    out: Dict[str, List[Order]] = {}
    a0 = smile_state.get("smile_a0")
    a1 = smile_state.get("smile_a1")
    a2 = smile_state.get("smile_a2")
    if a0 is None or a1 is None or a2 is None:
        return out
    ve_depth = depths.get(VFE)
    if ve_depth is None:
        return out
    s = _micro(ve_depth)
    if s is None or s <= 0:
        return out
    t = _tte_years(timestamp)
    if t <= 0:
        return out

    # Compute per-strike residual once (used by all pairs).
    res: Dict[int, float] = {}
    for k in (5300, 5400, 5500):
        sym = f"VEV_{k}"
        d_ = depths.get(sym)
        if d_ is None:
            continue
        mid_px = _mid(d_)
        if mid_px is None or mid_px <= 0:
            continue
        iv_m = implied_vol_call(mid_px, s, float(k), t)
        if not (iv_m == iv_m) or iv_m <= 0.005:
            continue
        m = math.log(s / float(k))
        bias_k = SMILE_PER_STRIKE_BIAS.get(k, 0.0)
        fair_iv = a0 + a1 * m + a2 * m * m + bias_k
        res[k] = iv_m - fair_iv

    for (k1, k2, sigma_pair, ratio1, ratio2) in PAIR_TRADES:
        if k1 not in res or k2 not in res:
            continue
        sym1, sym2 = f"VEV_{k1}", f"VEV_{k2}"
        d1, d2 = depths.get(sym1), depths.get(sym2)
        if d1 is None or d2 is None:
            continue

        # In v12's frame, pair_res is already zero-mean (bias_k already
        # subtracted in fair_iv). Trade directly against zero.
        pair_res = res[k1] - res[k2]
        z = pair_res / sigma_pair
        threshold = PAIR_TRIGGER_Z.get((k1, k2), 1.5)
        if abs(z) < threshold:
            continue

        sz1_intended = _pair_lots_k1(abs(z), threshold)
        sz2_intended = _hedge_lots(sz1_intended, ratio1, ratio2)
        cap1 = PAIR_POS_CAP.get(k1, 50)
        cap2 = PAIR_POS_CAP.get(k2, 50)
        pos1 = positions.get(sym1, 0)
        pos2 = positions.get(sym2, 0)
        bid1 = _bb(d1); ask1 = _ba(d1)
        bid2 = _bb(d2); ask2 = _ba(d2)

        if z > 0:
            # K1 IV rich relative to K2: SELL K1, BUY K2.
            if bid1 is None or ask2 is None:
                continue
            sell1_room = max(0, min(pos1 + cap1, CAP_VOU + pos1))
            buy2_room = max(0, min(cap2 - pos2, CAP_VOU - pos2))
            avail1 = d1.buy_orders[bid1]
            avail2 = -d2.sell_orders[ask2]
            sz1 = min(sz1_intended, avail1, sell1_room)
            sz2_target = _hedge_lots(sz1, ratio1, ratio2)
            sz2 = min(sz2_target, avail2, buy2_room)
            if sz2 < sz2_target:
                # Hedge constrained — shrink K1 to maintain ratio.
                sz1 = max(0, (sz2 * ratio1 + ratio2 // 2) // ratio2) if ratio2 > 0 else 0
            if sz1 > 0 and sz2 > 0:
                out.setdefault(sym1, []).append(Order(sym1, bid1, -sz1))
                out.setdefault(sym2, []).append(Order(sym2, ask2, sz2))
        else:
            # K1 IV cheap relative to K2: BUY K1, SELL K2.
            if ask1 is None or bid2 is None:
                continue
            buy1_room = max(0, min(cap1 - pos1, CAP_VOU - pos1))
            sell2_room = max(0, min(pos2 + cap2, CAP_VOU + pos2))
            avail1 = -d1.sell_orders[ask1]
            avail2 = d2.buy_orders[bid2]
            sz1 = min(sz1_intended, avail1, buy1_room)
            sz2_target = _hedge_lots(sz1, ratio1, ratio2)
            sz2 = min(sz2_target, avail2, sell2_room)
            if sz2 < sz2_target:
                sz1 = max(0, (sz2 * ratio1 + ratio2 // 2) // ratio2) if ratio2 > 0 else 0
            if sz1 > 0 and sz2 > 0:
                out.setdefault(sym1, []).append(Order(sym1, ask1, sz1))
                out.setdefault(sym2, []).append(Order(sym2, bid2, -sz2))

    return out


# ---------- Trader --------------------------------------------------------


class Trader:
    def run(self, state: TradingState):
        out: Dict[str, List[Order]] = {}
        try:
            prior = json.loads(state.traderData) if state.traderData else {}
        except Exception:
            prior = {}
        fs = dict(prior.get("fs", {}) or {})
        smile_state: Dict = dict(prior.get("smile", {}) or {})
        cp_state: Dict = dict(prior.get("cp", {}) or {})
        named_cp_state: Dict = dict(prior.get("named_cp", {}) or {})
        lag_state: Dict = dict(prior.get("lag", {}) or {})
        positions = state.position or {}
        depths = state.order_depths or {}

        # ---------- Counterparty bookkeeping (v12 NEW; live-only) ---------
        mids_now: Dict[str, float] = {}
        for s_, dep in depths.items():
            mp = _mid(dep)
            if mp is not None:
                mids_now[s_] = mp
        _update_cp_state(cp_state, getattr(state, "market_trades", {}) or {}, mids_now)

        # Explicit Round 4 VFE Mark-pair alpha.
        _update_named_vfe_cp_alpha(
            named_cp_state,
            getattr(state, "market_trades", {}) or {},
            state.timestamp,
        )

        named_vfe_bias, named_option_s_bias = _named_vfe_cp_bias(
            named_cp_state,
            state.timestamp,
        )

        # ---------- HYDROGEL fair (v10: micro+wall blend into anchor) -----
        hd = depths.get(HYD)
        himb_k1 = 0.0
        if hd is not None:
            m = _micro(hd)
            wm = _wall_mid(hd, WALL_VOL_THR_HYD)
            if wm is not None and m is not None:
                base = H_WALL_W * wm + (1.0 - H_WALL_W) * m
            else:
                base = m if m is not None else wm
            if base is not None:
                fs[HYD] = _ew(fs.get(HYD), A_W * ANCHOR + (1 - A_W) * base, A_HYD)
            himb_k1 = _imb(hd)

        # ---------- VFE fair (v9 micro EMA + v10 imb-k2 skew at MM stage) -
        vd = depths.get(VFE)
        vimb_k2 = 0.0
        if vd is not None:
            m = _micro(vd)
            if m is not None:
                fs[VFE] = _ew(fs.get(VFE), m, A_VFE)
            vimb_k2 = _imb_k2(vd)

        # ---------- Option-implied underlying signal -----------------------
        underlying_edge = 0.0
        underlying_conf = 0.0
        S_consensus = None
        underlying_bias = 0.0
        vfe_option_bias = 0.0

        if vd is not None:
            S_consensus, underlying_edge, underlying_conf = implied_underlying_from_options(
                depths,
                smile_state,
                state.timestamp,
            )

        if S_consensus is not None and underlying_conf >= OPTION_S_CONF_TH:
            strength = min(underlying_conf / 3.0, 1.0)

            # Bias used for option smile pricing.
            underlying_bias = strength * underlying_edge * 0.5

            # Separate, smaller bias used for VFE itself.
            if USE_OPTION_IMPLIED_VFE_BIAS:
                vfe_option_bias = _clamp(
                    W_OPTION_S_TO_VFE * strength * underlying_edge,
                    -OPTION_S_BIAS_CAP,
                    OPTION_S_BIAS_CAP,
                )

        # ---------- HYDROGEL MM (v9 unchanged) ----------------------------
        if hd is not None and HYD in fs:
            bid = _bb(hd); ask = _ba(hd); pos = positions.get(HYD, 0)
            fair = fs[HYD] + H_IMB * himb_k1 + _cp_signed_skew(cp_state, HYD)
            legs = []; b = s = 0
            if ask is not None and ask + H_TAKE <= fair:
                av = -hd.sell_orders[ask]
                sz = _cb(pos, CAP_H, b, min(av, CAP_H))
                if sz > 0:
                    legs.append(Order(HYD, ask, sz)); b += sz
            if bid is not None and bid - H_TAKE >= fair:
                av = hd.buy_orders[bid]
                sz = _cs(pos, CAP_H, s, min(av, CAP_H))
                if sz > 0:
                    legs.append(Order(HYD, bid, -sz)); s += sz
            inv = max(-1.0, min(1.0, (pos + b - s) / CAP_H))
            bp = int(math.floor(fair - H_QE))
            sp = int(math.ceil(fair + H_QE))
            if bid is not None: bp = min(bp, bid + 1)
            if ask is not None:
                bp = min(bp, ask - 1); sp = max(sp, ask - 1)
            if bid is not None: sp = max(sp, bid + 1)
            bsz = _cb(pos, CAP_H, b, max(0, int(round(H_SIZE * max(0.0, 1 - 1.0 * inv)))))
            ssz = _cs(pos, CAP_H, s, max(0, int(round(H_SIZE * max(0.0, 1 + 1.0 * inv)))))
            if bsz > 0 and (ask is None or bp < ask):
                legs.append(Order(HYD, bp, bsz))
            if ssz > 0 and (bid is None or sp > bid):
                legs.append(Order(HYD, sp, -ssz))
            if legs:
                out[HYD] = legs

        # ---------- VFE MM (v10: imb-k2 skew NEW, capped) -----------------
        if vd is not None and VFE in fs:
            bid = _bb(vd); ask = _ba(vd); pos = positions.get(VFE, 0)
            skew = _clamp(V_IMB_K2 * vimb_k2, -V_SKEW_CAP, V_SKEW_CAP)
            fair = (
                fs[VFE]
                + skew
                + _cp_signed_skew(cp_state, VFE)
                + vfe_option_bias
                + named_vfe_bias
            )
            legs = []; b = s = 0
            if ask is not None and ask + V_TAKE <= fair:
                av = -vd.sell_orders[ask]
                sz = _cb(pos, CAP_V, b, min(av, CAP_V))
                if sz > 0:
                    legs.append(Order(VFE, ask, sz)); b += sz
            if bid is not None and bid - V_TAKE >= fair:
                av = vd.buy_orders[bid]
                sz = _cs(pos, CAP_V, s, min(av, CAP_V))
                if sz > 0:
                    legs.append(Order(VFE, bid, -sz)); s += sz
            inv = max(-1.0, min(1.0, (pos + b - s) / CAP_V))
            bp = int(math.floor(fair - V_QE))
            sp = int(math.ceil(fair + V_QE))
            if bid is not None: bp = min(bp, bid + 1)
            if ask is not None:
                bp = min(bp, ask - 1); sp = max(sp, ask - 1)
            if bid is not None: sp = max(sp, bid + 1)
            bsz = _cb(pos, CAP_V, b, max(0, int(round(V_SIZE * max(0.0, 1 - 1.5 * inv)))))
            ssz = _cs(pos, CAP_V, s, max(0, int(round(V_SIZE * max(0.0, 1 + 1.5 * inv)))))
            if bsz > 0 and (ask is None or bp < ask):
                legs.append(Order(VFE, bp, bsz))
            if ssz > 0 and (bid is None or sp > bid):
                legs.append(Order(VFE, sp, -ssz))
            if legs:
                out[VFE] = legs

        # ---------- Voucher accumulation + identity arbs (v9 unchanged) ---
        ref = fs.get(VFE)
        if ref is None and vd is not None:
            ref = _mid(vd)
        for sym in depths:
            if sym in (HYD, VFE):
                continue
            k = _strike(sym)
            if k is None or not (4000 <= k <= 6500):
                continue
            
            d_ = depths.get(sym)
            if d_ is None or ref is None:
                continue
            bid = _bb(d_); ask = _ba(d_)
            pos = positions.get(sym, 0)
            intr = max(ref - k, 0.0)
            legs = []
            if k in ACC_STRIKES:
                if ask is not None and ask <= intr + ACC_SLACK:
                    av = -d_.sell_orders[ask]
                    sz = _cb(pos, CAP_VOU, 0, min(av, ACC_SIZE_PER_TICK))
                    if sz > 0:
                        legs.append(Order(sym, ask, sz))
                if bid is not None and bid >= intr + EXIT_SLACK and pos > 0:
                    av = d_.buy_orders[bid]
                    sz = _cs(pos, CAP_VOU, 0, min(av, min(pos, 50)))
                    if sz > 0:
                        legs.append(Order(sym, bid, -sz))
            else:
                if ask is not None and ask + 1 < intr:
                    av = -d_.sell_orders[ask]
                    sz = _cb(pos, CAP_VOU, 0, min(av, CAP_VOU))
                    if sz > 0:
                        legs.append(Order(sym, ask, sz))
                if bid is not None and bid - 1 > ref:
                    av = d_.buy_orders[bid]
                    sz = _cs(pos, CAP_VOU, 0, min(av, CAP_VOU))
                    if sz > 0:
                        legs.append(Order(sym, bid, -sz))
            if legs:
                out.setdefault(sym, []).extend(legs)


        pre_smile_orders = {sym: list(legs) for sym, legs in out.items()}
        # ---------- Phase 1 smile MM --------------------------------------
        # Important: use biased ve_micro so option pricing reacts THIS tick.
        raw_ve_micro = _micro(vd) if vd is not None else None

        if raw_ve_micro is not None:
            # underlying_bias comes from option-implied VFE.
            # named_option_s_bias comes from explicit Mark-pair VFE alpha. (buyer seller signal alpha should affect vouchers since they affect underlying)
            ve_micro_for_smile = raw_ve_micro + underlying_bias + named_option_s_bias
        else:
            ve_micro_for_smile = None

        smile_orders = _smile_voucher_orders(
            smile_state,
            depths,
            positions,
            state.timestamp,
            ve_micro_for_smile,
        )

        for sym, legs in smile_orders.items():
            out.setdefault(sym, []).extend(legs)

        # ---------- v15 cross-strike pair trade ---------------------------
        pair_orders: Dict[str, List[Order]] = {}

        if USE_PAIR_TRADE:
            pair_state: Dict = {}
            pair_orders = _pair_trade(
                pair_state,
                depths,
                positions,
                state.timestamp,
                smile_state,
            )

            for sym, legs in pair_orders.items():
                out.setdefault(sym, []).extend(legs)

        # Track which strikes the pair trade touched.
        pair_active_strikes = set()
        for sym, legs in pair_orders.items():
            if legs:
                k = _strike(sym)
                if k is not None:
                    pair_active_strikes.add(k)

        # ---------- delta-lag option reaction signal ----------------------
        if USE_DELTA_LAG:
            # Block overlap with accumulation / VFE / pair orders.
            # Do not block against passive smile quotes, because those are maker quotes.
            lag_blockers = {sym: list(legs) for sym, legs in pre_smile_orders.items()}

            for sym, legs in pair_orders.items():
                lag_blockers.setdefault(sym, []).extend(legs)

            lag_orders = _delta_lag_signal(
                lag_state=lag_state,
                depths=depths,
                positions=positions,
                timestamp=state.timestamp,
                smile_state=smile_state,
                existing_orders=lag_blockers,
            )

            for sym, legs in lag_orders.items():
                out.setdefault(sym, []).extend(legs)

        # ---------- single-strike scalp -----------------------------------
        # Called last so it can see existing MM / smile / pair orders and
        # avoid overlapping with them.
        scalp_blockers = {sym: list(legs) for sym, legs in pre_smile_orders.items()}

        for sym, legs in pair_orders.items():
            scalp_blockers.setdefault(sym, []).extend(legs)

        # scalp_orders = single_strike_scalp(
        #     depths=depths,
        #     positions=positions,
        #     smile_state=smile_state,
        #     timestamp=state.timestamp,
        #     underlying_edge=underlying_edge if underlying_conf >= 1.5 else 0.0,
        #     pair_active_strikes=pair_active_strikes,
        #     existing_orders=scalp_blockers,
        # )

        # for sym, legs in scalp_orders.items():
        #     out.setdefault(sym, []).extend(legs)

        td_out = {
            "fs": {k: round(v, 4) for k, v in fs.items()},
            "cp": {
                "by_name": cp_state.get("by_name", {}),
                "pending": cp_state.get("pending", [])[-200:],
            },
            "named_cp": {
                "active": named_cp_state.get("active", [])[-NAMED_VFE_CP_MAX_ACTIVE:],
            },
            "smile": {
                "smile_a0": smile_state.get("smile_a0"),
                "smile_a1": smile_state.get("smile_a1"),
                "smile_a2": smile_state.get("smile_a2"),
                "smile_s": smile_state.get("smile_s"),
                "smile_tte_days": smile_state.get("smile_tte_days"),
                "smile_ticks": smile_state.get("smile_ticks", 0),
            },
            "lag": lag_state,
        }

        return out, 0, json.dumps(td_out)

    def bid(self):
        return 20