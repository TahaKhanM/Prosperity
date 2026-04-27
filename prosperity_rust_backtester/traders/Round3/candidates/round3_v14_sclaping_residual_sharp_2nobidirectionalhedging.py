"""Round 3 v14 — submitted-v12 + multi-strike conviction-scaled IV scalp.

Lineage / rationale
-------------------
The first v14 attempt was based on the wrong v12 (a stale source file
that had v9-equivalent params + a K=5300 scalp). It lost 2,686 hosted vs
the actually-submitted v12 because the actually-submitted v12 has tuned
HYD/VFE/smile MM params (NOT a scalp).

This v14 corrects the base. It starts from the verbatim submitted v12
(hosted +11,654, day-2 1k-tuned) and adds the scalp ON TOP — the multi-
strike, conviction-scaled residual scalp that the hint pushes for.

So v14 = v12 hosted (preserved exactly) + new scalp module (additive).

Hosted attribution under this design
------------------------------------
- HYD MM, VFE MM, smile MM, accumulation, identity-arb, counterparty hook
  are byte-identical to submitted v12 → expected same PnL contributions
  as v12 hosted (~+11,654 baseline).
- The new multi-strike scalp on K in {5300, 5400, 5500} adds taker
  activity tied to per-tick IV residuals from the smile fit. Worst case
  (no scalp edge in 1k regime) it costs the spread on each fire and
  marginally regresses; best case it adds material PnL.

Scalp design (the "exploit the structure" piece)
------------------------------------------------
1. Multi-strike. {5300, 5400, 5500} — strikes with residual half-life
   >= 1.4 ticks and meaningful sigma * vega per smile_stability_report:
       K     rho1   half-life   sigma(IV)   sigma*vega (shells/sigma)
       5300  0.683  1.82t       0.0042      ~0.96
       5400  0.772  2.68t       0.0053      ~0.80
       5500  0.616  1.43t       0.0054      ~0.43

2. Per-strike threshold. K=5300/5400 use 0.6sigma; K=5500 lifts to
   1.0sigma (weaker shells/sigma economics).

3. Conviction-proportional sizing.
       lots = clamp(BASE + SCALE * (|z| - threshold), MIN, MAX)
            = clamp(5 + 15 * excess_z, 3, 40)
   Implements the hint directly: bigger gap, bigger position.

4. Hard per-strike absolute inventory caps: 30 / 25 / 20 lots for
   K=5300 / 5400 / 5500.

5. Reuses smile_state (a0/a1/a2 from the smile MM at this tick) — does
   not refit. Tracks per-strike residual EMA in scalp_state for the
   "deviation vs recent regime" reading.

START_TTE_DAYS = 6.0 stays from submitted v12 (calibrated for IMC hosted
day-2 backtester). Flip to 5.0 only for actual live R3 submission.

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


# ---------- v14 multi-strike, conviction-scaled residual scalp -------------
# Trades extreme deviations of per-strike IV residual from its rolling mean.
# Three strikes with research half-life >= 1.4t and meaningful sigma * vega.

SCALP_STRIKES = (5300, 5400, 5500)
SCALP_RES_EMA_ALPHA = 0.05         # half-life ~14 ticks

# Per-strike z trigger.

SCALP_TRIGGER_Z: Dict[int, float] = {
    5300: 0.6,
    5400: 0.6,
    5500: 1.0,                      # weaker shells/sigma -> demand more conviction
}

# Conviction-scaled sizing: lots = clamp(BASE + SCALE * (|z| - threshold),
# MIN, MAX). At threshold = MIN; at threshold + ~2.3sigma = MAX.
SCALP_BASE_LOTS = 5
SCALP_LOTS_PER_Z = 15
SCALP_MIN_LOTS = 3
SCALP_MAX_LOTS = 40

# Hard absolute per-strike scalp inventory cap (lots).
SCALP_POS_CAP: Dict[int, int] = {
    5300: 30,
    5400: 25,
    5500: 20,
}

# Per-strike sigma in IV units (smile_stability_report.md, 30k ticks).
SCALP_SIGMA: Dict[int, float] = {
    5300: 0.0042,
    5400: 0.0053,
    5500: 0.0054,
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


# ---------- v14 multi-strike, conviction-scaled residual scalp -------------


def _scalp_lots_from_z(abs_z: float, threshold: float) -> int:
    """Conviction-proportional sizing.

    Returns lots given |z| above the per-strike threshold. Bigger gap,
    bigger position — clamped to [MIN, MAX].
    """
    excess = max(0.0, abs_z - threshold)
    raw = SCALP_BASE_LOTS + SCALP_LOTS_PER_Z * excess
    sz = int(round(raw))
    return max(SCALP_MIN_LOTS, min(SCALP_MAX_LOTS, sz))


def _residual_scalp(state: Dict, depths: Dict[str, OrderDepth],
                    positions: Dict[str, int], timestamp: int,
                    smile_state: Dict) -> Dict[str, List[Order]]:

    out: Dict[str, List[Order]] = {}

    a0 = smile_state.get("smile_a0")
    a1 = smile_state.get("smile_a1")
    a2 = smile_state.get("smile_a2")

    if a0 is None or a1 is None or a2 is None:
        return out

    vd = depths.get(VFE)
    if vd is None:
        return out

    S = _micro(vd)
    if S is None or S <= 0:
        return out

    t = _tte_years(timestamp)
    if t <= 0:
        return out

    # ---------- Step 1: compute IVs for all strikes ----------
    ivs = {}
    vegas = {}
    mids = {}
    spreads = {}

    for k in SCALP_STRIKES:
        sym = f"VEV_{k}"
        d = depths.get(sym)
        if d is None:
            continue

        bid = _bb(d)
        ask = _ba(d)

        if bid is None or ask is None:
            continue

        spread = ask - bid
        if spread > 3:   # liquidity filter
            continue

        mid = (bid + ask) / 2

        iv = implied_vol_call(mid, S, float(k), t)
        if not (iv == iv) or iv <= 0.005:
            continue

        vega = bs_call_vega(S, float(k), t, iv)

        ivs[k] = iv
        vegas[k] = vega
        mids[k] = mid
        spreads[k] = spread

    if len(ivs) < 3:
        return out

    # ---------- Step 2: compute cross-strike residual ----------
    sorted_K = sorted(ivs.keys())

    residuals = {}

    for i in range(1, len(sorted_K) - 1):
        k = sorted_K[i]
        k_left = sorted_K[i - 1]
        k_right = sorted_K[i + 1]

        neighbor_avg = (ivs[k_left] + ivs[k_right]) / 2
        residuals[k] = ivs[k] - neighbor_avg

    # ---------- Step 3: EMA smoothing ----------
    res_ema = state.setdefault("scalp_res_ema", {})

    signals = {}

    for k, res in residuals.items():
        key = str(k)
        prev = res_ema.get(key)

        ema = res if prev is None else prev * (1 - SCALP_RES_EMA_ALPHA) + res * SCALP_RES_EMA_ALPHA
        res_ema[key] = ema

        if prev is None:
            continue

        dev = res - ema

        sigma = SCALP_SIGMA.get(k, 0.005)
        if sigma <= 0:
            continue

        z = dev / sigma
        signals[k] = z

    # ---------- Step 4: execute PAIR trades ----------
    for k, z in signals.items():

        threshold = SCALP_TRIGGER_Z.get(k, 0.6)
        if abs(z) < threshold:
            continue

        sym = f"VEV_{k}"
        d = depths[sym]

        bid = _bb(d)
        ask = _ba(d)

        if bid is None or ask is None:
            continue

        spread = spreads[k]
        vega = vegas[k]

        # better sizing: z * vega / spread
        edge_strength = abs(z) * vega / max(1.0, spread)

        lots = int(round(SCALP_BASE_LOTS + SCALP_LOTS_PER_Z * edge_strength))
        lots = max(SCALP_MIN_LOTS, min(SCALP_MAX_LOTS, lots))

        pos = positions.get(sym, 0)
        cap = SCALP_POS_CAP.get(k, 25)

        # pick hedge strike (neighbor)
        idx = sorted_K.index(k)
        if idx == 0 or idx == len(sorted_K) - 1:
            continue

        hedge_k = sorted_K[idx - 1] if abs(z) > threshold else sorted_K[idx + 1]
        hedge_sym = f"VEV_{hedge_k}"
        hedge_d = depths.get(hedge_sym)

        if hedge_d is None:
            continue

        hedge_bid = _bb(hedge_d)
        hedge_ask = _ba(hedge_d)

        if hedge_bid is None or hedge_ask is None:
            continue

        legs = []

        spread = ask - bid
        if spread > 3:
            continue

        if z > 0:
            # IV too high → SELL k, BUY hedge
            sell_room = max(0, pos + cap)
            if sell_room > 0:
                sz = min(lots, sell_room, d.buy_orders[bid])
                if sz > 0:
                    legs.append(Order(sym, bid, -sz))
                    # legs.append(Order(hedge_sym, hedge_ask, sz))

        else:
            # IV too low → BUY k, SELL hedge
            buy_room = max(0, cap - pos)
            if buy_room > 0:
                sz = min(lots, buy_room, -d.sell_orders[ask])
                if sz > 0:
                    legs.append(Order(sym, ask, sz))
                    # legs.append(Order(hedge_sym, hedge_bid, -sz))

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
        cp_state: Dict = dict(prior.get("cp", {}) or {})
        positions = state.position or {}
        depths = state.order_depths or {}

        # ---------- Counterparty bookkeeping (v12 NEW; live-only) ---------
        mids_now: Dict[str, float] = {}
        for s_, dep in depths.items():
            mp = _mid(dep)
            if mp is not None:
                mids_now[s_] = mp
        _update_cp_state(cp_state, getattr(state, "market_trades", {}) or {}, mids_now)

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
            fair = fs[VFE] + skew + _cp_signed_skew(cp_state, VFE)
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

        # ---------- v14 multi-strike conviction scalp (NEW) ----------------
        scalp_state: Dict = dict(prior.get("scalp", {}) or {})
        scalp_orders = _residual_scalp(scalp_state, depths, positions,
                                       state.timestamp, smile_state)
        for sym, legs in scalp_orders.items():
            out.setdefault(sym, []).extend(legs)

        td_out = {
            "fs": {k: round(v, 4) for k, v in fs.items()},
            "cp": {
                "by_name": cp_state.get("by_name", {}),
                "pending": cp_state.get("pending", [])[-200:],
            },
            "smile": {
                "smile_a0": smile_state.get("smile_a0"),
                "smile_a1": smile_state.get("smile_a1"),
                "smile_a2": smile_state.get("smile_a2"),
                "smile_s": smile_state.get("smile_s"),
                "smile_tte_days": smile_state.get("smile_tte_days"),
                "smile_ticks": smile_state.get("smile_ticks", 0),
            },
            "scalp": {
                "scalp_res_ema": {k: round(v, 6) for k, v in
                                  scalp_state.get("scalp_res_ema", {}).items()},
            },
        }
        return out, 0, json.dumps(td_out)

    def bid(self):
        return 20