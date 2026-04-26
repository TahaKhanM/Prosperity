"""Probe 5 (followup): r4_mark_lean_v02_no_m67 - Mark lean WITHOUT Mark 67.

Identical to Probe 1 (r4_mark_lean_v01) except Mark 67 is removed from
MARK_RULES_VFE. Phase 6 nulls found Mark 67 fails both Mark-permutation
(p=0.47) and time-shuffle (z=+2.0); headline +1.19/u h500 PnL is likely
drift-correlated, not causal. This probe quantifies the contamination.

Decision rule:
  - Δ vs Probe 1 ≥ −100 over 3-day BT → ship the lighter form (Mark 67 was noise)
  - Δ vs Probe 1 < −100 → retain Mark 67 with documented "weak null on 7-Mark set"

Pre-registered: single-rule edit. No tuning.

ORIGINAL Probe 1 docstring:
r4_mark_lean_v01 - Mark-conditional lean stack on top of v15.

Adds a per-product `mark_lean` accumulator decoded/encoded via traderData JSON.
Decay 0.985 per tick (HL ~46 ticks).

Per-trade contribution (one per trade in state.market_trades[product]):

HYDROGEL_PACK:
  Mark 14 buyer:    lean[HYD] += 0.20 * qty * 0.05  (positive)
  Mark 14 seller:   lean[HYD] -= 0.20 * qty * 0.05
  Mark 38 buyer:    lean[HYD] -= 0.20 * qty * 0.05
  Mark 38 seller:   lean[HYD] += 0.20 * qty * 0.05
  Mark 22 buyer:    lean[HYD] -= 0.20 * qty * 0.05  (R4-HYD-M01 fade)

VELVETFRUIT_EXTRACT:
  Mark 14 buyer:    lean[VFE] += 0.10 * qty * 0.05
  Mark 14 seller:   lean[VFE] -= 0.10 * qty * 0.05
  Mark 38 buyer:    lean[VFE] -= 0.10 * qty * 0.05
  Mark 38 seller:   lean[VFE] += 0.10 * qty * 0.05
  Mark 67 buyer:    lean[VFE] += 0.10 * qty * 0.05  (R4-VFE-M01 buy follow)
  Mark 49 seller:   lean[VFE] += 0.10 * qty * 0.05  (R4-VFE-M02 informed seller -> long)
  Mark 22 seller:   lean[VFE] += 0.05 * qty * 0.05  (R4-VFE-M03)

Clamp lean to +/- 3.0 per product. Apply lean[HYD] to HYD MM fair after the
existing skew, and lean[VFE] to VFE MM fair after the existing skew+fade.

Submission contract: run(state) -> (orders, conversions, traderData).
"""
from __future__ import annotations

import json
import math
from typing import Any, Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState


# ---------- product constants ----------------------------------------------

HYD = "HYDROGEL_PACK"
VFE = "VELVETFRUIT_EXTRACT"
CAP_H = 200
CAP_V = 200
CAP_VOU = 300

ANCHOR = 10000.0
A_W = 0.40
A_HYD = 0.18
H_TAKE = 4
H_QE = 3
H_SIZE = 20
H_IMB = 5.0
H_WALL_W = 0.9

A_VFE = 0.20
V_TAKE = 1
V_QE = 1
V_SIZE = 100
V_IMB_K2 = 5.0
V_SKEW_CAP = 1.0
WALL_VOL_THR_HYD = 15
WALL_VOL_THR_VFE = 20

ACC_STRIKES = [4000, 4500]
ACC_SLACK = 4
ACC_SIZE_PER_TICK = 50
EXIT_SLACK = 6

AC1_FADE_K_5000 = 0.06
AC1_FADE_K_5100 = 0.06
AC1_FADE_K_5200 = 0.084
AC1_FADE_K_5300 = 0.12
AC1_FADE_K_5400 = 0.15
AC1_FADE_K_5500 = 0.15
AC1_FADE_CAP = 0.5

HYD_AC1_FADE_K = 0.0
HYD_AC1_FADE_CAP = 1.0
VFE_AC1_FADE_K = 0.03
VFE_AC1_FADE_CAP = 3.0


# ---------- mark lean constants (NEW) --------------------------------------

LEAN_DECAY = 0.985
LEAN_CLAMP_PROD = 3.0

# Per-product per-Mark weights. Tuple = (sign_on_buyer, sign_on_seller, weight).
# Convention: contribution = sign * qty * 0.05 * weight.
# weight = 0 means inactive.
# (qty * 0.05 is the per-unit base; weight scales it.)
MARK_RULES_HYD = {
    "Mark 14": (+0.20, -0.20),  # buyer +, seller -
    "Mark 38": (-0.20, +0.20),  # buyer -, seller +
    "Mark 22": (-0.20, 0.0),    # buyer -, seller no-op (R4-HYD-M01)
}
MARK_RULES_VFE = {
    "Mark 14": (+0.10, -0.10),
    "Mark 38": (-0.10, +0.10),
    # "Mark 67" REMOVED (Phase 6 nulls fail: perm p=0.47, shuffle z=+2.0)
    "Mark 49": (0.0, +0.10),    # seller -> +VE (R4-VFE-M02)
    "Mark 22": (0.0, +0.05),    # seller -> +VE (R4-VFE-M03)
}


# ---------- Phase 1 smile MM constants (unchanged) -------------------------

SMILE_STRIKES = (5000, 5100, 5200, 5300, 5400, 5500)

START_TTE_DAYS = 7.0
DAY_TICKS = 1_000_000.0
SMILE_TTE_FLOOR_DAYS = 0.25

SMILE_A0_BASE = 0.2420
SMILE_A0_DRIFT_PER_DAY = 0.00275
SMILE_A1_BASE = -0.011
SMILE_A1_DRIFT_PER_DAY = -0.075
SMILE_A2_BASE = 7.21
SMILE_A2_DRIFT_PER_DAY = 0.815

SMILE_A0_EMA_ALPHA = 0.0003
SMILE_TAKE_EDGE_SHELLS = 0.7
SMILE_QUOTE_VEGA_FRAC = 0.006
SMILE_QUOTE_MIN_EDGE = 1
SMILE_QUOTE_SIZE = 5
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

SMILE_WARMUP_TICKS = 20


# ---------- Black-Scholes ---------------------------------------------------

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


# ---------- helpers --------------------------------------------------------


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


def _imb_k2(d):
    if not d.buy_orders or not d.sell_orders:
        return 0.0
    bs = sorted(d.buy_orders.items(), key=lambda x: -x[0])[:2]
    asks = sorted(d.sell_orders.items(), key=lambda x: x[0])[:2]
    bv = sum(v for _, v in bs)
    av = sum(-v for _, v in asks)
    t = bv + av
    return 0.0 if t <= 0 else (bv - av) / t


def _wall_mid(d, vol_thr):
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


# ---------- mark lean update (NEW) -----------------------------------------


def _update_mark_lean(mark_lean: Dict[str, float], market_trades, current_ts: int,
                      last_ts: int) -> None:
    """Decay then accumulate per-product lean. Mutates `mark_lean` in place."""
    elapsed_ticks = max(0, (current_ts - last_ts) // 100)
    if elapsed_ticks > 0:
        decay = LEAN_DECAY ** elapsed_ticks
        for p in list(mark_lean):
            mark_lean[p] *= decay

    for product, trades in (market_trades or {}).items():
        if product == HYD:
            rules = MARK_RULES_HYD
        elif product == VFE:
            rules = MARK_RULES_VFE
        else:
            continue
        for t in trades:
            buyer = getattr(t, "buyer", None) or ""
            seller = getattr(t, "seller", None) or ""
            qty = float(getattr(t, "quantity", 0))
            if qty == 0:
                continue
            delta = 0.0
            if buyer in rules:
                w_buy, _ = rules[buyer]
                delta += w_buy * qty * 0.05
            if seller in rules:
                _, w_sell = rules[seller]
                delta += w_sell * qty * 0.05
            if delta != 0.0:
                new_v = mark_lean.get(product, 0.0) + delta
                if new_v > LEAN_CLAMP_PROD:
                    new_v = LEAN_CLAMP_PROD
                elif new_v < -LEAN_CLAMP_PROD:
                    new_v = -LEAN_CLAMP_PROD
                mark_lean[product] = new_v


# ---------- Phase 1 smile MM (unchanged) -----------------------------------


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

    prev_mids = state.setdefault("prev_mid", {})
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
        cur_mid = _mid(d_)
        if cur_mid is not None:
            kstr = str(k)
            prev = prev_mids.get(kstr)
            prev_mids[kstr] = cur_mid
            if prev is not None:
                ret_t = cur_mid - prev
                if k == 5000: k_ac = AC1_FADE_K_5000
                elif k == 5100: k_ac = AC1_FADE_K_5100
                elif k == 5200: k_ac = AC1_FADE_K_5200
                elif k == 5300: k_ac = AC1_FADE_K_5300
                elif k == 5400: k_ac = AC1_FADE_K_5400
                elif k == 5500: k_ac = AC1_FADE_K_5500
                else: k_ac = 0.0
                fade = -k_ac * ret_t
                if fade > AC1_FADE_CAP: fade = AC1_FADE_CAP
                if fade < -AC1_FADE_CAP: fade = -AC1_FADE_CAP
                fair = fair + fade

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


# ---------- Trader ---------------------------------------------------------


class Trader:
    def run(self, state: TradingState):
        out: Dict[str, List[Order]] = {}
        try:
            prior = json.loads(state.traderData) if state.traderData else {}
        except Exception:
            prior = {}
        fs = dict(prior.get("fs", {}) or {})
        smile_state: Dict = dict(prior.get("smile", {}) or {})
        mark_lean: Dict[str, float] = dict(prior.get("mark_lean", {}) or {})
        last_ts = int(prior.get("last_ts", state.timestamp))

        positions = state.position or {}
        depths = state.order_depths or {}

        # NEW: update mark lean from market trades
        market_trades = getattr(state, "market_trades", {}) or {}
        _update_mark_lean(mark_lean, market_trades, int(state.timestamp), last_ts)

        prev_hyd_mid = float(prior.get("prev_hyd_mid") or 0.0)
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

        prev_vfe_mid = float(prior.get("prev_vfe_mid") or 0.0)
        vd = depths.get(VFE)
        vimb_k2 = 0.0
        if vd is not None:
            m = _micro(vd)
            if m is not None:
                fs[VFE] = _ew(fs.get(VFE), m, A_VFE)
            vimb_k2 = _imb_k2(vd)

        # ---------- HYDROGEL MM (lean added to fair) ----------------------
        hyd_mid_now = _mid(hd) if hd is not None else None
        if hd is not None and HYD in fs:
            bid = _bb(hd); ask = _ba(hd); pos = positions.get(HYD, 0)
            hyd_fade = 0.0
            if hyd_mid_now is not None and prev_hyd_mid > 0:
                hyd_ret = hyd_mid_now - prev_hyd_mid
                hyd_fade = -HYD_AC1_FADE_K * hyd_ret
                if hyd_fade > HYD_AC1_FADE_CAP: hyd_fade = HYD_AC1_FADE_CAP
                if hyd_fade < -HYD_AC1_FADE_CAP: hyd_fade = -HYD_AC1_FADE_CAP
            lean_h = mark_lean.get(HYD, 0.0)
            fair = fs[HYD] + H_IMB * himb_k1 + hyd_fade + lean_h
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

        # ---------- VFE MM (lean added to fair) ---------------------------
        vfe_mid_now = _mid(vd) if vd is not None else None
        if vd is not None and VFE in fs:
            bid = _bb(vd); ask = _ba(vd); pos = positions.get(VFE, 0)
            skew = _clamp(V_IMB_K2 * vimb_k2, -V_SKEW_CAP, V_SKEW_CAP)
            vfe_fade = 0.0
            if vfe_mid_now is not None and prev_vfe_mid > 0:
                vfe_ret = vfe_mid_now - prev_vfe_mid
                vfe_fade = -VFE_AC1_FADE_K * vfe_ret
                if vfe_fade > VFE_AC1_FADE_CAP: vfe_fade = VFE_AC1_FADE_CAP
                if vfe_fade < -VFE_AC1_FADE_CAP: vfe_fade = -VFE_AC1_FADE_CAP
            lean_v = mark_lean.get(VFE, 0.0)
            fair = fs[VFE] + skew + vfe_fade + lean_v
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

        # ---------- voucher accumulation + identity arbs ------------------
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

        # ---------- Phase 1 smile MM (unchanged) -------------------------
        ve_micro = _micro(vd) if vd is not None else None
        smile_orders = _smile_voucher_orders(smile_state, depths, positions,
                                              state.timestamp, ve_micro)
        for sym, legs in smile_orders.items():
            out.setdefault(sym, []).extend(legs)

        td_out = {
            "fs": {k: round(v, 4) for k, v in fs.items()},
            "prev_hyd_mid": round(hyd_mid_now, 4) if hyd_mid_now is not None else 0.0,
            "prev_vfe_mid": round(vfe_mid_now, 4) if vfe_mid_now is not None else 0.0,
            "mark_lean": {k: round(v, 4) for k, v in mark_lean.items()},
            "last_ts": int(state.timestamp),
            "smile": {
                "smile_a0": smile_state.get("smile_a0"),
                "smile_a1": smile_state.get("smile_a1"),
                "smile_a2": smile_state.get("smile_a2"),
                "smile_s": smile_state.get("smile_s"),
                "smile_tte_days": smile_state.get("smile_tte_days"),
                "smile_ticks": smile_state.get("smile_ticks", 0),
                "prev_mid": smile_state.get("prev_mid", {}),
            },
        }
        return out, 0, json.dumps(td_out)

    def bid(self):
        return 20
