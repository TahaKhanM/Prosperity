"""Round 3 v9 (up to Phase 1) — v7 base + v8 smile-tightening only.

Phase tracker
-------------
Phase 0 (BS pricer + IV solver):              DONE
Phase 1 (smile-based MM near-ATM):            DONE — converged at v9
Phase 2 (delta-hedge voucher book vs VFE):    NOT IN THIS FILE
Phase 3 (residual scalp on sticky strikes):   NOT IN THIS FILE
Phase 4 (deep-ITM strategy):                  reverted to mostrecent's
                                              accumulation in this file.

Why v9 = v7 + smile tightening (and nothing else)
-------------------------------------------------
v8 hosted comparison (IMC site, day 2 historical, 1000 ticks):
    v7         total: +9,112
    v8 (T=8)   total: +8,785   (-327 vs v7)
    v8 (T=5)   total: +7,828   (-957 vs v8 T=8)

v8 had two changes; both hurt or were neutral:

1. Deep-ITM MM destroyed mostrecent's accumulation edge (-330).
   VEV_4000 PnL collapsed +166 -> +10, VEV_4500 +184 -> +10.
   Stepping inside the deep-ITM 21-shell market spread is wrong:
   that spread is information-risk compensation, not slack.
   mostrecent's `ask <= intrinsic + 4` accumulation rarely fired (10
   of 1000 ticks) but each fire was real edge. v9 restores it.

2. Tighter smile quotes (SMILE_QUOTE_VEGA_FRAC 0.012 -> 0.006,
   SMILE_QUOTE_MIN_EDGE 2 -> 1) were a wash on day-2 hosted: per-
   strike Δ summed to +4. **Kept** in v9 because tighter quotes
   should sit better inside live-R3 spreads (and didn't hurt here).

3. TTE = 5d caused the smile prior to over-extrapolate skew/
   convexity outside the research calibration range. Wing strikes
   (5400/5500) hit the +300 long cap and 5300 hit -300 short cap,
   bleeding -957. **v9 keeps TTE = 8.0** for IMC site backtester
   (which runs day 2 = TTE 6d). Flip to 5.0 ONLY for actual live R3
   submission, and accept that per-strike biases were measured at
   TTE 6-8d; live behaviour outside that range is unmeasured.

v9 changes vs v7
----------------
- SMILE_QUOTE_VEGA_FRAC: 0.012 -> 0.006   (carried over from v8)
- SMILE_QUOTE_MIN_EDGE:  2     -> 1       (carried over from v8)

Everything else identical to v7.

Submission contract: run(state) -> (orders, conversions, traderData).
"""
from __future__ import annotations

import json
import math
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState


# ---------- mostrecent.py constants (unchanged) ----------------------------

HYD = "HYDROGEL_PACK"
VFE = "VELVETFRUIT_EXTRACT"
CAP_H = 200
CAP_V = 200
CAP_VOU = 300

ANCHOR = 10000.0
A_W = 0.40
A_HYD = 0.10
H_TAKE = 4
H_QE = 3
H_SIZE = 20
H_IMB = 5.0

A_VFE = 0.20
V_TAKE = 1
V_QE = 1
V_SIZE = 40

ACC_STRIKES = [4000, 4500]
ACC_SLACK = 4
ACC_SIZE_PER_TICK = 50
EXIT_SLACK = 6


# ---------- Phase 1 smile MM constants -------------------------------------

SMILE_STRIKES = (5000, 5100, 5200, 5300, 5400, 5500)

START_TTE_DAYS = 8.0                # IMC site backtester (day 2 = TTE 6d).
                                    # Flip to 5.0 for actual live R3 only.
                                    # See docstring: T=5 hurt -957 in v8 hosted.
DAY_TICKS = 1_000_000.0
SMILE_TTE_FLOOR_DAYS = 0.25

SMILE_A0_BASE = 0.2420
SMILE_A0_DRIFT_PER_DAY = 0.00275
SMILE_A1_BASE = -0.011
SMILE_A1_DRIFT_PER_DAY = -0.075
SMILE_A2_BASE = 7.21
SMILE_A2_DRIFT_PER_DAY = 0.815

SMILE_A0_EMA_ALPHA = 0.05
SMILE_TAKE_EDGE_SHELLS = 0.7
SMILE_QUOTE_VEGA_FRAC = 0.006        # v9: carry-over from v8 (0.012 -> 0.006)
SMILE_QUOTE_MIN_EDGE = 1             # v9: carry-over from v8 (2 -> 1)
SMILE_QUOTE_SIZE = 5
SMILE_SOFT_CAP = 80
SMILE_VEGA_FLOOR = 0.5

# v7. Per-strike residual offset, IV units. Source: 30,000-tick mean
# residual measurement in smile_stability_report.md.
SMILE_PER_STRIKE_BIAS: Dict[int, float] = {
    5000: -0.0077,
    5100: +0.0004,
    5200: +0.0076,
    5300: +0.0087,
    5400: -0.0144,
    5500: -0.0067,
}

# v7. Warm-up gate. Update the a0 EMA from observed IVs but post no orders
# until the EMA has settled. ~3 half-lives of SMILE_A0_EMA_ALPHA=0.05.
SMILE_WARMUP_TICKS = 30


# ---------- Black-Scholes (inlined) ---------------------------------------

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


# ---------- mostrecent.py helpers (unchanged) ------------------------------


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
    b, a = _bb(d), _ba(d)
    if b is None or a is None:
        return 0.0
    bv = d.buy_orders[b]
    av = -d.sell_orders[a]
    t = bv + av
    return 0.0 if t <= 0 else (bv - av) / t


def _strike(s):
    if s.startswith("VEV_"):
        try:
            return int(s[4:])
        except Exception:
            return None
    return None


def _cb(p, c, ad, w):
    return max(0, min(w, c - (p + ad)))


def _cs(p, c, ad, w):
    return max(0, min(w, c + (p - ad)))


def _ew(p, s, a):
    return s if p is None else p * (1 - a) + s * a


# ---------- Phase 1 smile MM (v7: + per-strike bias + warm-up) -------------


def _tte_years(timestamp: int) -> float:
    days_left = max(START_TTE_DAYS - timestamp / DAY_TICKS, SMILE_TTE_FLOOR_DAYS)
    return days_left / 365.0


def _smile_prior(tte_days: float) -> Tuple[float, float, float]:
    drift = max(0.0, 8.0 - tte_days)
    a0 = SMILE_A0_BASE + SMILE_A0_DRIFT_PER_DAY * drift
    a1 = SMILE_A1_BASE + SMILE_A1_DRIFT_PER_DAY * drift
    a2 = SMILE_A2_BASE + SMILE_A2_DRIFT_PER_DAY * drift
    return a0, a1, a2


def _smile_voucher_orders(state: Dict, depths: Dict[str, OrderDepth],
                          positions: Dict[str, int], timestamp: int,
                          ve_micro: Optional[float]) -> Dict[str, List[Order]]:
    out: Dict[str, List[Order]] = {}
    if ve_micro is None or ve_micro <= 0:
        return out
    t = _tte_years(timestamp)
    if t <= 0:
        return out
    tte_days = t * 365.0
    a0_prior, a1, a2 = _smile_prior(tte_days)

    # 1) per-strike implied IV.
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

    # 2) refit a0 (vega-weighted, bias-adjusted).
    #    a0_implied_K = (IV_market_K - bias_K) - a1*m - a2*m^2
    num = 0.0; den = 0.0
    for (k, m, iv_m, v) in strike_data:
        bias_k = SMILE_PER_STRIKE_BIAS.get(k, 0.0)
        a0_implied = (iv_m - bias_k) - a1 * m - a2 * m * m
        num += v * a0_implied
        den += v
    a0_obs = num / den if den > 0 else a0_prior

    # 3) EMA a0 across ticks.
    prev = state.get("smile_a0")
    a0 = a0_obs if prev is None else prev * (1.0 - SMILE_A0_EMA_ALPHA) + a0_obs * SMILE_A0_EMA_ALPHA
    state["smile_a0"] = a0
    state["smile_a1"] = a1
    state["smile_a2"] = a2
    state["smile_s"] = ve_micro
    state["smile_tte_days"] = tte_days
    ticks = int(state.get("smile_ticks", 0)) + 1
    state["smile_ticks"] = ticks

    # 4) Warm-up gate.  Update the EMA but post no orders.
    if ticks < SMILE_WARMUP_TICKS:
        return out

    # 5) per-strike fair price + take-and-quote.
    for (k, m, _, v) in strike_data:
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

        if ask is not None and ask + SMILE_TAKE_EDGE_SHELLS <= fair:
            avail = -d_.sell_orders[ask]
            sz = _cb(pos, cap, bought, min(avail, SMILE_QUOTE_SIZE * 4))
            if sz > 0:
                legs.append(Order(sym, ask, sz)); bought += sz
        if bid is not None and bid - SMILE_TAKE_EDGE_SHELLS >= fair:
            avail = d_.buy_orders[bid]
            sz = _cs(pos, cap, sold, min(avail, SMILE_QUOTE_SIZE * 4))
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
            bsz_raw = max(0, int(round(SMILE_QUOTE_SIZE * (1.0 - inv))))
            ssz_raw = max(0, int(round(SMILE_QUOTE_SIZE * (1.0 + inv))))
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
        positions = state.position or {}
        depths = state.order_depths or {}

        # ---------- HYDROGEL fair (anchor + microprice EMA) ----------
        hd = depths.get(HYD)
        himb = 0.0
        if hd is not None:
            m = _micro(hd)
            if m is not None:
                fs[HYD] = _ew(fs.get(HYD), A_W * ANCHOR + (1 - A_W) * m, A_HYD)
            himb = _imb(hd)

        # ---------- VFE fair (microprice EMA) ----------
        vd = depths.get(VFE)
        if vd is not None:
            m = _micro(vd)
            if m is not None:
                fs[VFE] = _ew(fs.get(VFE), m, A_VFE)

        # ---------- HYDROGEL MM ----------
        if hd is not None and HYD in fs:
            bid = _bb(hd); ask = _ba(hd); pos = positions.get(HYD, 0)
            fair = fs[HYD] + H_IMB * himb
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
            bsz = _cb(pos, CAP_H, b, max(0, int(round(H_SIZE * max(0.0, 1 - 2.0 * inv)))))
            ssz = _cs(pos, CAP_H, s, max(0, int(round(H_SIZE * max(0.0, 1 + 2.0 * inv)))))
            if bsz > 0 and (ask is None or bp < ask):
                legs.append(Order(HYD, bp, bsz))
            if ssz > 0 and (bid is None or sp > bid):
                legs.append(Order(HYD, sp, -ssz))
            if legs:
                out[HYD] = legs

        # ---------- VFE MM ----------
        if vd is not None and VFE in fs:
            bid = _bb(vd); ask = _ba(vd); pos = positions.get(VFE, 0)
            fair = fs[VFE]
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

        # ---------- Voucher accumulation + identity arbs (mostrecent) ----------
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

        # ---------- Phase 1 smile MM (v7: bias + warm-up) ----------
        ve_micro = _micro(vd) if vd is not None else None
        smile_orders = _smile_voucher_orders(smile_state, depths, positions,
                                              state.timestamp, ve_micro)
        for sym, legs in smile_orders.items():
            out.setdefault(sym, []).extend(legs)

        td_out = {
            "fs": {k: round(v, 4) for k, v in fs.items()},
            "smile": {
                "smile_a0": smile_state.get("smile_a0"),
                "smile_a1": smile_state.get("smile_a1"),
                "smile_a2": smile_state.get("smile_a2"),
                "smile_s": smile_state.get("smile_s"),
                "smile_tte_days": smile_state.get("smile_tte_days"),
                "smile_ticks": smile_state.get("smile_ticks", 0),
            },
        }
        return out, 0, json.dumps(td_out)

    def bid(self):
        return 20