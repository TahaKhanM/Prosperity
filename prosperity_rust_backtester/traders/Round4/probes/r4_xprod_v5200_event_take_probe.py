"""Phase 6 followup: r4_xprod_v5200_event_take - event-triggered take on V_4000.

Reformulation of R4-XPROD-VEV5200 from a passive Mark-conditional lean
(rejected in Phase 8a, +42 only) to an EVENT-TRIGGERED TAKE. Phase 6 nulls
confirmed: source-product time-shuffle PASSES (z=+12.3 / +19.5) but Mark-
permutation FAILS -- the spillover is EVENT-driven, NOT Mark-attributable.
So the trigger is "any large V_5200 print", not "Mark 14 buys / Mark 22 sells".

Mechanism each tick:
1. Iterate state.market_trades["VEV_5200"]:
   - Skip if qty < EVENT_QTY_THR
   - Classify aggressor: buyer-initiated if price >= V_5200 ask;
     seller-initiated if price <= V_5200 bid; else skip
   - On buyer-initiated: take V_4000 BUY EVENT_TAKE_QTY (+ direction)
   - On seller-initiated: take V_4000 SELL EVENT_TAKE_QTY (- direction)
2. Per-day event count tracked in traderData; cap at EVENT_DAILY_CAP.
3. NO auto-flatten; v15's accumulation MM unwinds via EXIT_SLACK.

Phase 3 measurement: Mark 22 sell V_5200 -> V_4000 mid +5.087 within 5 ticks
(t=+20.8, lift +216 % of unconditional SD). Mark 14 buy mirror.

Pre-reg: EVENT_QTY_THR=5, EVENT_TAKE_QTY=10, EVENT_DAILY_CAP=30.
Ship gate: Δ vs v15 ≥ +200 AND ≥ 10 events fire AND day-3 dominates.

Original baseline docstring (v15 with START_TTE_DAYS shifted from 8 to 7).

R4 historical day 1/2/3 corresponds to TTE 7/6/5 days (vs R3's 8/7/6).
The only structural change vs v15 is START_TTE_DAYS = 7.0.

This probe establishes the Round 4 baseline against which every R4-specific
alpha probe must compare.

ORIGINAL v15 docstring follows.
================================================================
v15 - v13 + voucher/VFE 1-tick AC1 fade + tighter V skew cap.

Why v15
-------
After confirming v12's hosted-equiv overfit, v13 was rebuilt as a robust
joint-metric optimum.  v15 adds two independently-discovered alphas
verified via parallel deep statistical analysis and trade-level audit
of v13's runs:

1. **Voucher 1-tick AC1 mean-reversion fade** (per-strike).  Empirical
   AC1 of voucher mid returns is strongly negative: -0.21 (V5300) to
   -0.25 (V5400/V5500).  Fade adds skew = -K * (mid_t - mid_{t-1}) to
   the smile-MM fair, pushing fair against the most recent move.
   Optimal K = 0.6 * |empirical AC1| (sweep-locked at 0.5-0.6 plateau).
   Joint impact: +2,494 on (10k+1k).

2. **VFE 1-tick AC1 fade**.  Empirical VFE AC1 = -0.16.  Same fade
   formulation applied to VFE fair before the imb-k2 skew.  Optimal
   K = 0.03 (much smaller than empirical because of spread cost).
   Joint impact: +1,936 on (10k+1k).
   HYD fade tested and rejected - spread cost (8 shells/RT) >> AC1 edge
   (~0.27 shells), confirmed by data-analysis sim.

Plus tightened V_SKEW_CAP 2 -> 1 (+1,096 joint).

Joint Rust-BT bench (10k 3-day + 1k 3-day = "sum")
-------------------------------------------------
                         10k 3-day   1k 3-day   sum        Δ vs v9 (sum)
v9                       234,231     3,682      237,912    -
v10                      238,587     4,250      242,838    +4,926
v12 (1k overfit)         203,327     7,951      211,278    -26,634
v13                      268,136     5,740      273,876    +35,964
v14a (voucher AC1)       270,469     5,901      276,370    +38,458
v15 (this file)          275,471     5,543      281,014    +43,103 (+18.1%)

Per-day 10k 3-day total:
                         day 0      day 1      day 2     total
v9                       77,970     64,338     91,923    234,231
v15                      88,852     80,029    106,591    275,472   (+10.9k / +15.7k / +14.7k)

Per-product attribution (v15 vs v9, 10k 3-day)
---------------------------------------------
- HYDROGEL_PACK         +8.6k  (A_HYD=0.18 slow EMA: +6k day 0)
- VELVETFRUIT_EXTRACT   +4.0k  (V_SIZE=100, AC1 fade, tighter skew cap)
- Voucher 5000-5500    +30.5k  (frozen smile + AC1 fade)
- Voucher 4000/4500     +0.0k  (deep-ITM accumulation unchanged)

Risk profile
------------
v15's mid-day drawdown on the 1k day-2 hosted-equivalent test is similar
to v9 (~-14k).  This is *structural* to mean-reverting HYD MM under a
200-cap and a 50-shell intra-day range.  The strategy ENDS positive
after the drawdown recovers; the drawdown is mark-to-market on
inventory, not realised loss.  v15's H_SIZE=20 keeps inventory small.

Failed alphas (tested and rejected - kept here as a research log)
----------------------------------------------------------------
- HYD imb_k3 multivar skew (univariate -44, multivar -31):
  imb_k3 distribution is too narrow (std=0.016, 95% quantile=0); the
  signal rarely fires.  Adding it gave 0 joint improvement.
- HYD 1-tick AC1 fade: spread cost (8/RT) > revert edge (0.27).
- HYD wall-mid full replacement of anchor-blend: data analysis confirmed
  high R^2=0.10 but take-strategy still loses on 16-shell spread.
- Per-strike adaptive bias EMA (TimoDiehm-style): MM fair feedback loop
  absorbs the trade signal.  Only useful as a residual TAKE signal,
  not as fair adjuster.
- Static per-strike bias updates from data analysis (e.g., K5500 +2.5):
  any meaningful magnitude (|bias_iv| > 0.05) blew up the BT.  Calibrated
  values are knife-edge.
- HYD spectral 3333-tick cycle: day-0-only artefact, not robust.
- VFE→voucher cross-asset lead-lag: same-tick corr=0.62, all lags ≈0.
  No predictability beyond contemporaneous delta link.
- HYD ANCHOR=9991 (empirical mean) vs 10000: cleaner per-day plot but
  on 10k metric, ANCHOR=10000 wins (+32k vs ANCHOR=9985).

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
A_W = 0.40                  # weight of anchor in HYD fair-blend (v9 unchanged)
A_HYD = 0.18                # EMA alpha on HYD fair
H_TAKE = 4
H_QE = 3
H_SIZE = 20
H_IMB = 5.0                 # HYD imb-k1 skew slope (v9 unchanged)
H_WALL_W = 0.9              # v10 NEW: weight of wall-mid in HYD fair input

A_VFE = 0.20
V_TAKE = 1
V_QE = 1
V_SIZE = 100
V_IMB_K2 = 5.0              # v10 NEW: VFE imb-k2 skew slope (capped)
V_SKEW_CAP = 1.0            # v10 NEW: |skew| <= 2 shells
WALL_VOL_THR_HYD = 15       # ignore HYD levels with vol < 15 for wall-mid
WALL_VOL_THR_VFE = 20       # ignore VFE levels with vol < 20 for wall-mid

ACC_STRIKES = [4000, 4500]
ACC_SLACK = 4
ACC_SIZE_PER_TICK = 50
EXIT_SLACK = 6

# v14 NEW: voucher 1-tick AC1 mean-reversion fade
AC1_FADE_K_5000 = 0.06
AC1_FADE_K_5100 = 0.06
AC1_FADE_K_5200 = 0.084
AC1_FADE_K_5300 = 0.12
AC1_FADE_K_5400 = 0.15
AC1_FADE_K_5500 = 0.15
AC1_FADE_CAP = 0.5

# v15 NEW: HYD/VFE 1-tick AC1 fade
HYD_AC1_FADE_K = 0.0
HYD_AC1_FADE_CAP = 1.0
VFE_AC1_FADE_K = 0.03
VFE_AC1_FADE_CAP = 3.0


# ---------- Phase 1 smile MM constants (unchanged from v9) ------------------

SMILE_STRIKES = (5000, 5100, 5200, 5300, 5400, 5500)

START_TTE_DAYS = 7.0  # R4 hist day 1 = TTE 7d (was 8d in R3 day 0)
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

# R4-XPROD-VEV5200 event-take constants (NEW)
EVENT_SOURCE_PRODUCT = "VEV_5200"
EVENT_TARGET_PRODUCT = "VEV_4000"
EVENT_QTY_THR = 5
EVENT_TAKE_QTY = 10
EVENT_DAILY_CAP = 30
EVENT_DAY_TICKS_INT = 1_000_000


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
        # v14 NEW: 1-tick AC1 fade. Bias fair against most recent mid change.
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

        # v15 NEW: HYD AC1 fade - track prev mid
        prev_hyd_mid = float(prior.get("prev_hyd_mid") or 0.0)
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

        # v15 NEW: VFE prev mid
        prev_vfe_mid = float(prior.get("prev_vfe_mid") or 0.0)
        # ---------- VFE fair (v9 micro EMA + v10 imb-k2 skew at MM stage) -
        vd = depths.get(VFE)
        vimb_k2 = 0.0
        if vd is not None:
            m = _micro(vd)
            if m is not None:
                fs[VFE] = _ew(fs.get(VFE), m, A_VFE)
            vimb_k2 = _imb_k2(vd)

        # ---------- HYDROGEL MM (v9 unchanged) ----------------------------
        if hd is not None and HYD in fs:
            bid = _bb(hd); ask = _ba(hd); pos = positions.get(HYD, 0)
            hyd_mid_now = _mid(hd) if hd is not None else None
            hyd_fade = 0.0
            if hyd_mid_now is not None and prev_hyd_mid > 0:
                hyd_ret = hyd_mid_now - prev_hyd_mid
                hyd_fade = -HYD_AC1_FADE_K * hyd_ret
                if hyd_fade > HYD_AC1_FADE_CAP: hyd_fade = HYD_AC1_FADE_CAP
                if hyd_fade < -HYD_AC1_FADE_CAP: hyd_fade = -HYD_AC1_FADE_CAP
            fair = fs[HYD] + H_IMB * himb_k1 + hyd_fade
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

        # ---------- VFE MM (v10: imb-k2 skew NEW, capped) -----------------
        if vd is not None and VFE in fs:
            bid = _bb(vd); ask = _ba(vd); pos = positions.get(VFE, 0)
            skew = _clamp(V_IMB_K2 * vimb_k2, -V_SKEW_CAP, V_SKEW_CAP)
            vfe_mid_now = _mid(vd) if vd is not None else None
            vfe_fade = 0.0
            if vfe_mid_now is not None and prev_vfe_mid > 0:
                vfe_ret = vfe_mid_now - prev_vfe_mid
                vfe_fade = -VFE_AC1_FADE_K * vfe_ret
                if vfe_fade > VFE_AC1_FADE_CAP: vfe_fade = VFE_AC1_FADE_CAP
                if vfe_fade < -VFE_AC1_FADE_CAP: vfe_fade = -VFE_AC1_FADE_CAP
            fair = fs[VFE] + skew + vfe_fade
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

        # ---------- Phase 1 smile MM (v9 unchanged) -----------------------
        ve_micro = _micro(vd) if vd is not None else None
        smile_orders = _smile_voucher_orders(smile_state, depths, positions,
                                              state.timestamp, ve_micro)
        for sym, legs in smile_orders.items():
            out.setdefault(sym, []).extend(legs)

        # ---------- R4-XPROD-VEV5200 event-triggered TAKE (NEW) -----------
        # Take V_4000 in response to large V_5200 prints. Aggressor inferred from
        # trade.price vs V_5200 best bid/ask AT THIS TICK.
        prior_event_day = int(prior.get("event_day", -1))
        prior_event_count = int(prior.get("event_count", 0))
        cur_day = int(state.timestamp) // EVENT_DAY_TICKS_INT
        if cur_day != prior_event_day:
            event_count_today = 0
        else:
            event_count_today = prior_event_count

        v5200_d = depths.get(EVENT_SOURCE_PRODUCT)
        v4000_d = depths.get(EVENT_TARGET_PRODUCT)
        market_trades = getattr(state, "market_trades", {}) or {}
        v5200_trades = market_trades.get(EVENT_SOURCE_PRODUCT, []) or []
        if v5200_trades and v5200_d is not None and v4000_d is not None:
            v5200_bid = _bb(v5200_d)
            v5200_ask = _ba(v5200_d)
            v4000_bid = _bb(v4000_d)
            v4000_ask = _ba(v4000_d)
            pos_v4000 = positions.get(EVENT_TARGET_PRODUCT, 0)
            existing_legs = list(out.get(EVENT_TARGET_PRODUCT, []))
            existing_bought = sum(o.quantity for o in existing_legs if o.quantity > 0)
            existing_sold = sum(-o.quantity for o in existing_legs if o.quantity < 0)
            for t in v5200_trades:
                if event_count_today >= EVENT_DAILY_CAP:
                    break
                tq = float(getattr(t, "quantity", 0))
                tp = float(getattr(t, "price", 0))
                if tq < EVENT_QTY_THR:
                    continue
                # Classify aggressor side via current V_5200 best bid/ask.
                if v5200_ask is not None and tp >= v5200_ask:
                    side = +1   # buyer-initiated -> take V_4000 BUY
                elif v5200_bid is not None and tp <= v5200_bid:
                    side = -1   # seller-initiated -> take V_4000 SELL
                else:
                    continue    # ambiguous (mid-print) -> skip
                if side > 0 and v4000_ask is not None:
                    avail = -v4000_d.sell_orders[v4000_ask]
                    sz = _cb(pos_v4000, CAP_VOU, existing_bought,
                             min(int(avail), EVENT_TAKE_QTY))
                    if sz > 0:
                        existing_legs.append(Order(EVENT_TARGET_PRODUCT,
                                                    v4000_ask, sz))
                        existing_bought += sz
                        event_count_today += 1
                elif side < 0 and v4000_bid is not None:
                    avail = v4000_d.buy_orders[v4000_bid]
                    sz = _cs(pos_v4000, CAP_VOU, existing_sold,
                             min(int(avail), EVENT_TAKE_QTY))
                    if sz > 0:
                        existing_legs.append(Order(EVENT_TARGET_PRODUCT,
                                                    v4000_bid, -sz))
                        existing_sold += sz
                        event_count_today += 1
            if existing_legs:
                out[EVENT_TARGET_PRODUCT] = existing_legs

        td_out = {
            "fs": {k: round(v, 4) for k, v in fs.items()},
            "prev_hyd_mid": round(hyd_mid_now, 4) if hyd_mid_now is not None else 0.0,
            "prev_vfe_mid": round(vfe_mid_now, 4) if vfe_mid_now is not None else 0.0,
            "event_day": cur_day,
            "event_count": event_count_today,
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
